"""Logging setup.

In production (or when LOG_JSON=1) logs are emitted as one JSON object per
line, so the Log Analytics workspace the Container Apps ship stdout to can
query them by field. Every record carries the request correlation id when one
is set, so a single id ties the whole request together across api and worker.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "copilot.log"


def _correlation_id() -> str:
    # lazy import: the worker and CLIs have no API middleware loaded
    try:
        from copilot.api.middleware import get_correlation_id

        return get_correlation_id()
    except Exception:
        return ""


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _correlation_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        cid = getattr(record, "correlation_id", "")
        if cid:
            payload["correlation_id"] = cid
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def _use_json() -> bool:
    return os.environ.get("LOG_JSON") == "1" or os.environ.get("ENVIRONMENT") == "production"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        LOG_DIR.mkdir(exist_ok=True)
        if _use_json():
            formatter: logging.Formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(correlation_id)s | %(message)s"
            )

        correlation_filter = CorrelationFilter()
        for handler in (logging.FileHandler(LOG_FILE), logging.StreamHandler()):
            handler.setFormatter(formatter)
            handler.addFilter(correlation_filter)
            logger.addHandler(handler)

    return logger
