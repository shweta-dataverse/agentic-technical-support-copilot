"""Structured-logging tests: JSON format and correlation-id injection."""

from __future__ import annotations

import json
import logging

from copilot.utils.logger import CorrelationFilter, JsonFormatter


def test_json_formatter_emits_valid_json_with_fields() -> None:
    record = logging.LogRecord(
        name="copilot.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="resolved ticket %s",
        args=("SUP-1",),
        exc_info=None,
    )
    record.correlation_id = "corr-123"
    payload = json.loads(JsonFormatter().format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "copilot.test"
    assert payload["message"] == "resolved ticket SUP-1"
    assert payload["correlation_id"] == "corr-123"


def test_correlation_filter_sets_attribute() -> None:
    record = logging.LogRecord(
        name="x", level=logging.INFO, pathname=__file__, lineno=1, msg="m",
        args=(), exc_info=None,
    )
    assert CorrelationFilter().filter(record) is True
    assert hasattr(record, "correlation_id")
