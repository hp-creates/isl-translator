"""WebSocket endpoint for real-time sign language translation.

Handles the full lifecycle of a translation session:
1. Client connects → session state initialised
2. Client sends frames → processed through ML pipeline → response sent back
3. Client sends controls → session state updated
4. Client disconnects → resources cleaned up
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.core.buffer_engine import BufferEngine, BufferEvent
from app.core.frame_processor import FrameProcessor
from app.core.llm_service import LLMService
from app.core.sentence_builder import SentenceBuilder
from app.core.sign_classifier import SignClassifier
from app.models.schemas import ControlAction, PredictionResponse
from app.utils.logging import get_logger

logger = get_logger("websocket")

router = APIRouter()

# Shared resources (loaded once at app startup via lifespan)
_frame_processor: FrameProcessor | None = None
_sign_classifier: SignClassifier | None = None
_llm_service: LLMService | None = None


def init_shared_resources(
    frame_processor: FrameProcessor,
    sign_classifier: SignClassifier,
    llm_service: LLMService,
) -> None:
    """Inject shared resources from app lifespan.

    Called once at application startup. These resources are shared
    across all WebSocket connections (they are stateless/thread-safe).
    """
    global _frame_processor, _sign_classifier, _llm_service
    _frame_processor = frame_processor
    _sign_classifier = sign_classifier
    _llm_service = llm_service
    logger.info("Shared resources initialised for WebSocket handler")


@router.websocket("/ws/translate")
async def websocket_translate(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for real-time ISL translation.

    Each connection gets its own BufferEngine and SentenceBuilder,
    providing isolated session state per client.
    """
    await websocket.accept()
    client_id = id(websocket)
    logger.info("Client connected: %s", client_id)

    settings = get_settings()

    # Per-session state
    buffer_engine = BufferEngine(
        stability_frames=settings.stability_frames,
        timeout_seconds=settings.buffer_timeout_seconds,
        min_buffer_size=settings.min_buffer_size,
    )
    sentence_builder = SentenceBuilder(_llm_service)
    is_active = False
    timeout_task: asyncio.Task | None = None

    async def check_timeout_loop() -> None:
        """Background task that checks for buffer timeout and emits words."""
        nonlocal is_active
        while is_active:
            await asyncio.sleep(0.5)
            word_candidate = buffer_engine.check_timeout()
            if word_candidate:
                await _handle_word_ready(word_candidate)

    async def _handle_word_ready(raw_chars: str) -> None:
        """Process a completed word — correct via LLM and update sentence."""
        buffer_engine.clear_buffer()

        corrected_word, sentence = await sentence_builder.add_word(raw_chars)

        # Send word event + updated state to client
        await _send_state(
            extra={
                "event": "word_ready",
                "original_chars": raw_chars,
                "corrected_word": corrected_word,
            }
        )
        logger.info(
            "Word processed: '%s' → '%s' | Sentence: '%s'",
            raw_chars,
            corrected_word,
            sentence,
        )

    async def _send_state(extra: dict[str, Any] | None = None) -> None:
        """Send current session state to the client."""
        response = PredictionResponse(
            buffer=buffer_engine.buffer,
            words=sentence_builder.words,
            sentence=sentence_builder.sentence,
            is_active=is_active,
            stability_progress=buffer_engine.stability_progress,
            stability_required=buffer_engine.stability_required,
        )
        data = response.model_dump()
        if extra:
            data.update(extra)

        try:
            await websocket.send_json(data)
        except Exception:
            logger.warning("Failed to send state to client %s", client_id)

    try:
        while True:
            # Receive message
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            msg_type = message.get("type")

            # --- Handle Control Messages ---
            if msg_type == "control":
                action = message.get("action")

                if action == ControlAction.START:
                    is_active = True
                    buffer_engine.reset()
                    # Start timeout checker
                    if timeout_task is None or timeout_task.done():
                        timeout_task = asyncio.create_task(check_timeout_loop())
                    logger.info("Session started for client %s", client_id)
                    await _send_state()

                elif action == ControlAction.STOP:
                    is_active = False
                    if timeout_task and not timeout_task.done():
                        timeout_task.cancel()
                    logger.info("Session stopped for client %s", client_id)
                    await _send_state()

                elif action == ControlAction.NEXT_WORD:
                    word_candidate = buffer_engine.force_emit()
                    if word_candidate:
                        await _handle_word_ready(word_candidate)
                    else:
                        await _send_state()

                elif action == ControlAction.FINISH:
                    # Finalise sentence via LLM
                    refined = await sentence_builder.finish()
                    await _send_state(
                        extra={
                            "event": "sentence_finished",
                            "refined_sentence": refined,
                        }
                    )
                    logger.info("Sentence finished for client %s: '%s'", client_id, refined)

                elif action == ControlAction.CLEAR:
                    buffer_engine.reset()
                    sentence_builder.reset()
                    await _send_state(extra={"event": "cleared"})
                    logger.info("Session cleared for client %s", client_id)

                continue

            # --- Handle Frame Messages ---
            if msg_type == "frame" and is_active:
                frame_data = message.get("data")
                if not frame_data:
                    continue

                # Process frame through ML pipeline
                result = _frame_processor.process_frame(frame_data)

                if result is None:
                    await _send_state()
                    continue

                features, num_hands = result
                char, confidence = _sign_classifier.predict(features)

                response_data: dict[str, Any] = {
                    "hands_detected": num_hands,
                }

                if confidence >= settings.confidence_threshold:
                    buf_result = buffer_engine.process_char(char, confidence)
                    response_data.update(
                        {
                            "current_char": char,
                            "confidence": round(confidence, 2),
                            "stability_progress": buf_result.stability_progress,
                            "stability_required": buf_result.stability_required,
                            "buffer": buf_result.buffer,
                        }
                    )
                else:
                    buffer_engine.reset_stability()
                    response_data.update(
                        {
                            "current_char": None,
                            "confidence": round(confidence, 2),
                            "stability_progress": 0,
                        }
                    )

                # Merge with full state
                state = PredictionResponse(
                    current_char=response_data.get("current_char"),
                    confidence=response_data.get("confidence", 0),
                    stability_progress=response_data.get("stability_progress", 0),
                    stability_required=buffer_engine.stability_required,
                    buffer=buffer_engine.buffer,
                    words=sentence_builder.words,
                    sentence=sentence_builder.sentence,
                    is_active=is_active,
                    hands_detected=response_data.get("hands_detected", 0),
                )
                await websocket.send_json(state.model_dump())

    except WebSocketDisconnect:
        logger.info("Client disconnected: %s", client_id)
    except Exception:
        logger.exception("Unexpected error for client %s", client_id)
    finally:
        # Cleanup
        if timeout_task and not timeout_task.done():
            timeout_task.cancel()
        logger.info("Session cleaned up for client %s", client_id)
