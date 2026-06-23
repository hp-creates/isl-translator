"""Pydantic schemas for WebSocket message validation.

Defines the contract between frontend and backend for all WebSocket
communication. All messages are validated before processing.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ControlAction(str, Enum):
    """Actions the client can send to control the session."""

    START = "start"
    STOP = "stop"
    NEXT_WORD = "next_word"
    FINISH = "finish"
    CLEAR = "clear"


class MessageType(str, Enum):
    """Discriminator for incoming WebSocket messages."""

    FRAME = "frame"
    CONTROL = "control"


# ---------------------------------------------------------------------------
# Client → Server Messages
# ---------------------------------------------------------------------------


class FrameMessage(BaseModel):
    """A single video frame sent from the client."""

    type: MessageType = MessageType.FRAME
    data: str = Field(..., description="Base64-encoded JPEG frame data")


class ControlMessage(BaseModel):
    """A control command sent from the client."""

    type: MessageType = MessageType.CONTROL
    action: ControlAction


class IncomingMessage(BaseModel):
    """Union of all possible incoming WebSocket messages."""

    type: MessageType
    data: Optional[str] = None
    action: Optional[ControlAction] = None


# ---------------------------------------------------------------------------
# Server → Client Messages
# ---------------------------------------------------------------------------


class PredictionResponse(BaseModel):
    """Real-time prediction update sent to the client after each frame."""

    current_char: Optional[str] = Field(None, description="Currently detected character")
    confidence: float = Field(0.0, description="Prediction confidence (0-100)")
    stability_progress: int = Field(0, description="Frames held for current char")
    stability_required: int = Field(5, description="Frames required for acceptance")
    buffer: str = Field("", description="Current character buffer")
    words: List[str] = Field(default_factory=list, description="List of recognised words")
    sentence: str = Field("", description="Current accumulated sentence")
    is_active: bool = Field(False, description="Whether recognition is active")
    hands_detected: int = Field(0, description="Number of hands detected in frame")


class WordEvent(BaseModel):
    """Sent when a new word is recognised and corrected."""

    original_chars: str = Field(..., description="Raw characters from buffer")
    corrected_word: str = Field(..., description="LLM-corrected word")


class SentenceEvent(BaseModel):
    """Sent when the sentence is finalised/refined."""

    raw_words: List[str] = Field(..., description="List of words before refinement")
    refined_sentence: str = Field(..., description="LLM-refined sentence")


class ErrorResponse(BaseModel):
    """Error message sent to the client."""

    error: str
    detail: Optional[str] = None
