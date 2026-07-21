"""Schema contract tests, validate the ORM metadata without a live database."""

from __future__ import annotations

from sqlalchemy import DateTime

from copilot.db.models import Base

EXPECTED_TABLES = {
    "tickets",
    "resolutions",
    "jobs",
    "document_registry",
    "processed_messages",
    "audit_log",
    "api_keys",
}


def test_all_system_of_record_tables_exist() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_resolutions_cascade_on_ticket_delete() -> None:
    """GDPR RTBF relies on resolutions dying with their ticket."""
    fk = next(iter(Base.metadata.tables["resolutions"].foreign_keys))
    assert fk.ondelete == "CASCADE"


def test_jobs_survive_ticket_delete() -> None:
    """Job history is operational data, not personal data, kept on RTBF."""
    fk = next(iter(Base.metadata.tables["jobs"].foreign_keys))
    assert fk.ondelete == "SET NULL"


def test_hot_query_paths_are_indexed() -> None:
    indexes = {
        idx.name for table in Base.metadata.tables.values() for idx in table.indexes
    }
    assert {
        "ix_tickets_status",
        "ix_jobs_status_created_at",
        "ix_resolutions_ticket_id",
        "ix_document_registry_content_hash",
    } <= indexes


def test_timestamps_are_timezone_aware() -> None:
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, DateTime):
                assert column.type.timezone, f"{table.name}.{column.name} is naive"
