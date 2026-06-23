"""LLM service — Groq API integration for word correction and sentence building.

Uses the OpenAI-compatible SDK to call Groq's API. This design makes it
trivial to swap providers (Together AI, OpenAI, etc.) by changing the
base_url and API key.
"""

from __future__ import annotations

import re
from typing import List

from openai import AsyncOpenAI

from app.utils.logging import get_logger

logger = get_logger("llm_service")


class LLMService:
    """Async LLM client for word correction and sentence refinement.

    Uses Groq's OpenAI-compatible API with Llama 3.3 70B by default.
    Swapping to another provider is a one-line config change.
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        """Initialise the LLM client.

        Args:
            api_key: Groq API key (from env var, never hardcoded).
            model: Model identifier (e.g., "llama-3.3-70b-versatile").
        """
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self._model = model
        logger.info("LLM service initialised (model=%s)", model)

    async def correct_word(self, chars: str) -> str:
        """Correct a sequence of signed characters into a real English word.

        Args:
            chars: Raw character sequence from the buffer (e.g., "HELO").

        Returns:
            Corrected word (e.g., "HELLO"), or the original chars on failure.
        """
        word_length = len(chars)

        prompt = (
            f"The user signed a sequence of {word_length} characters: '{chars}'. "
            "Assume that one or two of these characters might be misread due to "
            "signing errors or model uncertainty. "
            f"What is the single, most likely English word of exactly {word_length} letters "
            "that the user was trying to spell? "
            "Only return the predicted word, nothing else."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a spelling correction assistant for sign language. "
                            "You ONLY return a single word. No explanations, no punctuation."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=word_length + 10,
                stop=["\n"],
            )

            raw_result = response.choices[0].message.content.strip()
            logger.info("LLM word correction: '%s' → '%s'", chars, raw_result)

            # Clean: extract only alphabetic characters, uppercase
            cleaned = re.sub(r"[^A-Za-z]", "", raw_result).upper()
            return cleaned if cleaned else chars

        except Exception:
            logger.exception("LLM word correction failed for '%s'", chars)
            return chars

    async def refine_sentence(self, words: List[str]) -> str:
        """Refine a list of words into a grammatically correct sentence.

        Called when the user clicks "Finish" to polish the accumulated words.

        Args:
            words: List of corrected words (e.g., ["HELLO", "WORLD"]).

        Returns:
            A natural English sentence (e.g., "Hello, world!").
        """
        if not words:
            return ""

        words_str = ", ".join(words)

        prompt = (
            f"The following words were spelled using sign language: [{words_str}]. "
            "Form the most natural, grammatically correct English sentence using "
            "these words. You may adjust tense, add articles/prepositions, and add "
            "punctuation to make the sentence natural. "
            "Return ONLY the sentence, nothing else."
        )

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a sentence construction assistant. "
                            "You receive words from sign language and form natural sentences. "
                            "Return ONLY the final sentence."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=200,
            )

            result = response.choices[0].message.content.strip()
            logger.info("LLM sentence refinement: %s → '%s'", words, result)
            return result

        except Exception:
            logger.exception("LLM sentence refinement failed for %s", words)
            # Graceful fallback: join words as-is
            return " ".join(word.capitalize() for word in words) + "."

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.close()
        logger.info("LLM service closed")
