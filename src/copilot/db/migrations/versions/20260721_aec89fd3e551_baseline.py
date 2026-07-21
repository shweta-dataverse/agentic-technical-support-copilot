"""baseline

Revision ID: aec89fd3e551
Revises: 
Create Date: 2026-07-21 03:01:26.362208
"""
from collections.abc import Sequence

import sqlalchemy as sa  # noqa: F401
from alembic import op  # noqa: F401


revision: str = 'aec89fd3e551'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
