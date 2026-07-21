"""
Central logging setup. (structlog JSON logging arrives with the observability step; interface
stays stable.)
"""

from __future__ import annotations

import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "copilot.log"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        LOG_DIR.mkdir(exist_ok=True)
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
