"""Sentence builder — accumulates corrected words into sentences.

Maintains the word history and current sentence for a session.
Delegates to LLMService for word correction and sentence refinement.
"""

from __future__ import annotations

from typing import List, Optional

from app.core.llm_service import LLMService
from app.utils.logging import get_logger

logger = get_logger("sentence_builder")


class SentenceBuilder:
    """Accumulates recognised words and builds sentences.

    Maintains a list of corrected words and provides methods to:
    - Add new words (with LLM correction)
    - Get the current sentence
    - Finish and refine the sentence via LLM
    - Reset for a new session
    """

    def __init__(self, llm_service: LLMService) -> None:
        self._llm = llm_service
        self._words: List[str] = []
        self._sentence: str = ""

    @property
    def words(self) -> List[str]:
        """List of all recognised words in order."""
        return list(self._words)

    @property
    def sentence(self) -> str:
        """Current accumulated sentence."""
        return self._sentence

    async def add_word(self, raw_chars: str) -> tuple[str, str]:
        """Correct a character sequence and add it as a word.

        Args:
            raw_chars: Raw character buffer contents (e.g., "HELO").

        Returns:
            Tuple of (corrected_word, updated_sentence).
        """
        corrected = await self._llm.correct_word(raw_chars)
        self._words.append(corrected)
        self._sentence = " ".join(w.capitalize() for w in self._words)

        logger.info(
            "Word added: '%s' → '%s' | Sentence: '%s'",
            raw_chars,
            corrected,
            self._sentence,
        )
        return corrected, self._sentence

    async def finish(self) -> str:
        """Finalise and refine the sentence using the LLM.

        Returns:
            The LLM-refined sentence, or the raw sentence if LLM fails.
        """
        if not self._words:
            return ""

        refined = await self._llm.refine_sentence(self._words)
        self._sentence = refined

        logger.info("Sentence finalised: '%s'", refined)
        return refined

    def reset(self) -> None:
        """Clear all words and sentence state."""
        self._words.clear()
        self._sentence = ""
        logger.debug("Sentence builder reset")
