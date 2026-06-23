"""Structured logging configuration.

Provides consistent, JSON-structured logging across the application.
Log level is controlled via the LOG_LEVEL environment variable.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configure and return the application logger.

    Args:
        level: Log level string (e.g., "info", "debug"). Defaults to "info".

    Returns:
        Configured root logger for the application.
    """
    log_level = getattr(logging, (level or "info").upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure stream handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure application logger
    logger = logging.getLogger("isl_translator")
    logger.setLevel(log_level)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a specific module.

    Args:
        name: Module name (e.g., "frame_processor", "llm_service").

    Returns:
        Child logger under the "isl_translator" namespace.
    """
    return logging.getLogger(f"isl_translator.{name}")
