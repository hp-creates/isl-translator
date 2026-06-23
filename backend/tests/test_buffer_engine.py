"""Tests for the BufferEngine — stability tracking and word emission."""

from __future__ import annotations

import time
from unittest.mock import patch

from app.core.buffer_engine import BufferEngine, BufferEvent


class TestBufferEngine:
    """Test suite for BufferEngine."""

    def setup_method(self):
        """Create a fresh BufferEngine for each test."""
        self.engine = BufferEngine(
            stability_frames=3,
            timeout_seconds=2.0,
            min_buffer_size=2,
            skip_char="Q",
        )

    def test_char_not_accepted_below_stability(self):
        """Character should not be accepted before reaching stability threshold."""
        result = self.engine.process_char("A", 95.0)
        assert result.event == BufferEvent.BUFFER_UPDATED
        assert self.engine.buffer == ""

        result = self.engine.process_char("A", 95.0)
        assert result.event == BufferEvent.BUFFER_UPDATED
        assert self.engine.buffer == ""

    def test_char_accepted_at_stability(self):
        """Character should be accepted after stability threshold is met."""
        for _ in range(2):
            self.engine.process_char("H", 95.0)

        result = self.engine.process_char("H", 95.0)
        assert result.event == BufferEvent.CHAR_ACCEPTED
        assert self.engine.buffer == "H"

    def test_multiple_chars_build_buffer(self):
        """Multiple different chars should accumulate in the buffer."""
        # Accept 'H'
        for _ in range(3):
            self.engine.process_char("H", 95.0)

        # Accept 'I'
        for _ in range(3):
            self.engine.process_char("I", 95.0)

        assert self.engine.buffer == "HI"

    def test_duplicate_char_not_re_added(self):
        """Same char should not be added twice consecutively."""
        # Accept 'H'
        for _ in range(3):
            self.engine.process_char("H", 95.0)

        # Try to add 'H' again — should not re-add
        for _ in range(3):
            result = self.engine.process_char("H", 95.0)

        assert self.engine.buffer == "H"

    def test_skip_char_at_start(self):
        """Skip character should be ignored at buffer start."""
        for _ in range(2):
            self.engine.process_char("Q", 95.0)

        result = self.engine.process_char("Q", 95.0)
        assert result.event == BufferEvent.CHAR_IGNORED
        assert self.engine.buffer == ""

    def test_skip_char_stripped_from_end_on_emit(self):
        """Skip character should be stripped from end on force emit."""
        # Build buffer "HIQ"
        for char in ["H", "I", "Q"]:
            for _ in range(3):
                self.engine.process_char(char, 95.0)

        word = self.engine.force_emit()
        assert word == "HI"

    def test_timeout_emits_word(self):
        """Buffer should emit word after timeout."""
        # Build buffer "HI"
        for char in ["H", "I"]:
            for _ in range(3):
                self.engine.process_char(char, 95.0)

        # Simulate time passing
        with patch("app.core.buffer_engine.time") as mock_time:
            mock_time.time.return_value = time.time() + 10.0
            word = self.engine.check_timeout()

        assert word == "HI"

    def test_no_timeout_when_buffer_too_short(self):
        """Timeout should not emit when buffer is below min size."""
        # Only one char
        for _ in range(3):
            self.engine.process_char("H", 95.0)

        with patch("app.core.buffer_engine.time") as mock_time:
            mock_time.time.return_value = time.time() + 10.0
            word = self.engine.check_timeout()

        assert word is None

    def test_force_emit(self):
        """Force emit should return buffer if it meets min size."""
        for char in ["H", "I"]:
            for _ in range(3):
                self.engine.process_char(char, 95.0)

        word = self.engine.force_emit()
        assert word == "HI"

    def test_force_emit_returns_none_when_too_short(self):
        """Force emit should return None when buffer is too short."""
        for _ in range(3):
            self.engine.process_char("H", 95.0)

        word = self.engine.force_emit()
        assert word is None

    def test_reset_clears_all_state(self):
        """Reset should clear buffer and stability tracking."""
        for _ in range(3):
            self.engine.process_char("H", 95.0)

        self.engine.reset()
        assert self.engine.buffer == ""
        assert self.engine.stability_progress == 0

    def test_reset_stability(self):
        """Reset stability should clear only stability tracking."""
        self.engine.process_char("A", 95.0)
        self.engine.process_char("A", 95.0)
        assert self.engine.stability_progress == 2

        self.engine.reset_stability()
        assert self.engine.stability_progress == 0
        assert self.engine.buffer == ""  # Buffer was empty anyway

    def test_clear_buffer_after_emit(self):
        """Clear buffer should reset for next word."""
        for char in ["H", "I"]:
            for _ in range(3):
                self.engine.process_char(char, 95.0)

        self.engine.clear_buffer()
        assert self.engine.buffer == ""
