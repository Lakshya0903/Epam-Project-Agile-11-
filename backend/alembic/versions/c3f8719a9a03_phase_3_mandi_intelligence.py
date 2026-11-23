"""phase_3_mandi_intelligence

Revision ID: c3f8719a9a03
Revises: 22f82a866cc9
Create Date: 2026-11-19 00:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'c3f8719a9a03'
down_revision: Union[str, Sequence[str], None] = '22f82a866cc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to Phase 3: Mandi Price Intelligence, Caching & Provenance Tracking."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update mandi_price_records table
    if "mandi_price_records" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("mandi_price_records")]

        if "source" not in existing_cols:
            op.add_column(
                "mandi_price_records",
                sa.Column("source", sa.String(), server_default="seed", nullable=False)
            )

        if "fetched_at" not in existing_cols:
            op.add_column(
                "mandi_price_records",
                sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True)
            )

        existing_indices = [i["name"] for i in inspector.get_indexes("mandi_price_records")]
        if "ix_mandi_query" not in existing_indices:
            try:
                op.create_index(
                    "ix_mandi_query",
                    "mandi_price_records",
                    ["district", "market", "commodity", "arrival_date"],
                    unique=False
                )
            except Exception:
                pass

    # 2. mandi_cache_metadata table
    if "mandi_cache_metadata" not in existing_tables:
        op.create_table(
            "mandi_cache_metadata",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("district", sa.String(), nullable=False, index=True),
            sa.Column("market", sa.String(), nullable=True, index=True),
            sa.Column("commodity", sa.String(), nullable=False, index=True),
            sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(), server_default="success", nullable=False),
            sa.Column("record_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("error_message", sa.String(), nullable=True),
            sa.Column("source", sa.String(), server_default="ogd_api", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("district", "market", "commodity", name="uq_mandi_cache_scope"),
        )


def downgrade() -> None:
    """Downgrade schema from Phase 3."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if "mandi_cache_metadata" in existing_tables:
        op.drop_table("mandi_cache_metadata")

    if "mandi_price_records" in existing_tables:
        existing_indices = [i["name"] for i in inspector.get_indexes("mandi_price_records")]
        if "ix_mandi_query" in existing_indices:
            try:
                op.drop_index("ix_mandi_query", table_name="mandi_price_records")
            except Exception:
                pass
        # Note: SQLite does not support dropping columns without table copy,
        # so column drops are guarded for PostgreSQL compatibility.
        if conn.dialect.name != "sqlite":
            existing_cols = [c["name"] for c in inspector.get_columns("mandi_price_records")]
            if "fetched_at" in existing_cols:
                op.drop_column("mandi_price_records", "fetched_at")
            if "source" in existing_cols:
                op.drop_column("mandi_price_records", "source")

