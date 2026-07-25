"""Logging configuration for the AI Translation & Quality Scoring Pipeline.

Provides structured, readable console logging for operational transparency.
"""

import logging
import sys
from config import config


def setup_logger(name: str = "ai_pipeline") -> logging.Logger:
    """Configures and returns a logger instance with standardized formatting.

    Args:
        name: Name of the logger domain.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Primary application logger
logger = setup_logger()
