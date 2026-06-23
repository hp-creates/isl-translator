"""Tests for the SentenceBuilder."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.sentence_builder import SentenceBuilder


@pytest.fixture
def mock_llm():
    """Create a mock LLM service."""
    llm = MagicMock()
    llm.correct_word = AsyncMock(side_effect=lambda chars: chars.upper())
    llm.refine_sentence = AsyncMock(
        side_effect=lambda words: " ".join(w.capitalize() for w in words) + "."
    )
    return llm


@pytest.fixture
def builder(mock_llm):
    """Create a SentenceBuilder with mock LLM."""
    return SentenceBuilder(mock_llm)


class TestSentenceBuilder:
    """Test suite for SentenceBuilder."""

    @pytest.mark.asyncio
    async def test_add_single_word(self, builder, mock_llm):
        """Adding a word should call LLM and update sentence."""
        mock_llm.correct_word = AsyncMock(return_value="HELLO")

        corrected, sentence = await builder.add_word("HELO")

        assert corrected == "HELLO"
        assert "Hello" in sentence
        assert builder.words == ["HELLO"]
        mock_llm.correct_word.assert_called_once_with("HELO")

    @pytest.mark.asyncio
    async def test_add_multiple_words(self, builder, mock_llm):
        """Multiple words should accumulate and build a sentence."""
        mock_llm.correct_word = AsyncMock(side_effect=["HELLO", "WORLD"])

        await builder.add_word("HELO")
        _, sentence = await builder.add_word("WRLD")

        assert builder.words == ["HELLO", "WORLD"]
        assert "Hello" in sentence
        assert "World" in sentence

    @pytest.mark.asyncio
    async def test_finish_calls_refine(self, builder, mock_llm):
        """Finish should call LLM refine_sentence."""
        mock_llm.correct_word = AsyncMock(side_effect=["I", "AM", "HAPPY"])
        mock_llm.refine_sentence = AsyncMock(return_value="I am happy.")

        await builder.add_word("I")
        await builder.add_word("AM")
        await builder.add_word("HAPY")

        result = await builder.finish()

        assert result == "I am happy."
        mock_llm.refine_sentence.assert_called_once_with(["I", "AM", "HAPPY"])

    @pytest.mark.asyncio
    async def test_finish_empty(self, builder):
        """Finish with no words should return empty string."""
        result = await builder.finish()
        assert result == ""

    def test_reset(self, builder):
        """Reset should clear all state."""
        builder._words = ["HELLO", "WORLD"]
        builder._sentence = "Hello World"

        builder.reset()

        assert builder.words == []
        assert builder.sentence == ""

    def test_words_returns_copy(self, builder):
        """Words property should return a copy, not a reference."""
        builder._words = ["HELLO"]
        words = builder.words
        words.append("EXTRA")

        assert builder.words == ["HELLO"]  # Original unchanged
