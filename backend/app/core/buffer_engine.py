"""Buffer engine — character stability tracking and word boundary detection.

Implements the same stability logic as the original app.py but encapsulated
in a reusable, testable class with per-session state.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.utils.logging import get_logger

logger = get_logger("buffer_engine")


class BufferEvent(str, Enum):
    """Events emitted by the buffer engine."""

    CHAR_ACCEPTED = "char_accepted"
    WORD_READY = "word_ready"
    BUFFER_UPDATED = "buffer_updated"
    CHAR_IGNORED = "char_ignored"


@dataclass
class BufferResult:
    """Result of processing a character through the buffer engine."""

    event: BufferEvent
    buffer: str = ""
    word: Optional[str] = None
    stability_progress: int = 0
    stability_required: int = 5


class BufferEngine:
    """Manages character stability tracking and word accumulation.

    A character must be consistently detected for `stability_frames`
    consecutive frames before being accepted into the buffer. When no
    new character is detected for `timeout_seconds`, the buffer contents
    are emitted as a word candidate.

    Args:
        stability_frames: Number of consecutive frames required to accept a char.
        timeout_seconds: Seconds of inactivity before emitting buffer as a word.
        min_buffer_size: Minimum characters required to form a word.
        skip_char: Character to ignore at start/end of buffer (e.g., 'Q').
    """

    def __init__(
        self,
        stability_frames: int = 5,
        timeout_seconds: float = 5.0,
        min_buffer_size: int = 3,
        skip_char: str = "Q",
    ) -> None:
        self._stability_frames = stability_frames
        self._timeout_seconds = timeout_seconds
        self._min_buffer_size = min_buffer_size
        self._skip_char = skip_char

        # Mutable state
        self._buffer: str = ""
        self._current_stable_char: str = ""
        self._stability_counter: int = 0
        self._last_char_time: float = time.time()

    @property
    def buffer(self) -> str:
        """Current character buffer contents."""
        return self._buffer

    @property
    def stability_progress(self) -> int:
        """Current stability frame count."""
        return self._stability_counter

    @property
    def stability_required(self) -> int:
        """Required stability frames for acceptance."""
        return self._stability_frames

    def process_char(self, char: str, confidence: float) -> BufferResult:
        """Process a detected character through the stability filter.

        Args:
            char: The detected character.
            confidence: Detection confidence (0-100).

        Returns:
            BufferResult describing what happened.
        """
        # Track stability — same char must be held for N frames
        if char == self._current_stable_char:
            self._stability_counter += 1
        else:
            self._current_stable_char = char
            self._stability_counter = 1

        # Check if stability threshold reached
        if self._stability_counter >= self._stability_frames:
            is_new = not self._buffer or self._current_stable_char != self._buffer[-1]

            if is_new:
                # Skip char at buffer start
                if not self._buffer and self._current_stable_char == self._skip_char:
                    logger.debug("Ignored skip char '%s' at buffer start", self._skip_char)
                    self._current_stable_char = ""
                    self._stability_counter = 0
                    return BufferResult(
                        event=BufferEvent.CHAR_IGNORED,
                        buffer=self._buffer,
                        stability_progress=0,
                        stability_required=self._stability_frames,
                    )

                # Accept character into buffer
                self._buffer += self._current_stable_char
                self._last_char_time = time.time()
                self._stability_counter = 0
                self._current_stable_char = ""

                logger.info("Char accepted — buffer: '%s'", self._buffer)
                return BufferResult(
                    event=BufferEvent.CHAR_ACCEPTED,
                    buffer=self._buffer,
                    stability_progress=0,
                    stability_required=self._stability_frames,
                )

        return BufferResult(
            event=BufferEvent.BUFFER_UPDATED,
            buffer=self._buffer,
            stability_progress=self._stability_counter,
            stability_required=self._stability_frames,
        )

    def reset_stability(self) -> None:
        """Reset stability tracking (e.g., when confidence drops)."""
        self._stability_counter = 0
        self._current_stable_char = ""

    def check_timeout(self) -> Optional[str]:
        """Check if the buffer has timed out and should emit a word.

        Returns:
            The buffer contents if timeout triggered and buffer is long enough,
            or None if no timeout.
        """
        if not self._buffer:
            return None

        elapsed = time.time() - self._last_char_time
        if elapsed <= self._timeout_seconds:
            return None

        if len(self._buffer) < self._min_buffer_size:
            logger.debug(
                "Buffer too short (%d < %d) on timeout — keeping",
                len(self._buffer),
                self._min_buffer_size,
            )
            return None

        # Strip skip char from end
        result = self._buffer
        if result.endswith(self._skip_char):
            result = result[:-1]
            if len(result) < self._min_buffer_size:
                self._buffer = result
                self._last_char_time = time.time()
                return None

        logger.info("Buffer timeout — emitting word candidate: '%s'", result)
        return result

    def force_emit(self) -> Optional[str]:
        """Force-emit the current buffer as a word (e.g., "Next Word" button).

        Returns:
            Buffer contents if non-empty and meets minimum size, else None.
        """
        if len(self._buffer) < self._min_buffer_size:
            return None

        result = self._buffer
        if result.endswith(self._skip_char):
            result = result[:-1]

        logger.info("Forced emit — word candidate: '%s'", result)
        return result if len(result) >= self._min_buffer_size else None

    def clear_buffer(self) -> None:
        """Clear the buffer after a word has been emitted."""
        self._buffer = ""
        self._current_stable_char = ""
        self._stability_counter = 0
        self._last_char_time = time.time()
        logger.debug("Buffer cleared")

    def reset(self) -> None:
        """Full reset — clear all state."""
        self._buffer = ""
        self._current_stable_char = ""
        self._stability_counter = 0
        self._last_char_time = time.time()
        logger.debug("Buffer engine fully reset")
