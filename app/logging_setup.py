"""Logging configuration for ARIS."""

import sys
from pathlib import Path

from loguru import logger


def configure_logging() -> None:
    """Configure loguru outputs for console and file."""
    logger.remove()

    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        ),
        level="INFO",
    )

    log_dir = Path(__file__).resolve().parent.parent / "data/logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "aris_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
