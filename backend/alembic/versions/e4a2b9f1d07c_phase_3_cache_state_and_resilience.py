"""phase_3_cache_state_and_resilience

Revision ID: e4a2b9f1d07c
Revises: c3f8719a9a03
Create Date: 2026-11-19 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'e4a2b9f1d07c'
down_revision: Union[str, Sequence[str], None] = 'c3f8719a9a03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema:
      - Add 'state' to mandi_cache_metadata for unambiguous state-scoped cache identity.
      - Add 'last_successful_fetch_at', 'last_attempted_at', 'last_successful_record_count', and 'cooldown_until'.
      - Update ix_mandi_query index to include 'state'.
    """
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. Update mandi_cache_metadata
    if "mandi_cache_metadata" in existing_tables:
        existing_cols = [c["name"] for c in inspector.get_columns("mandi_cache_metadata")]
        with op.batch_alter_table("mandi_cache_metadata") as batch_op:
            if "state" not in existing_cols:
                batch_op.add_column(
                    sa.Column("state", sa.String(), server_default="All", nullable=False)
                )
            if "last_successful_fetch_at" not in existing_cols:
                batch_op.add_column(
                    sa.Column("last_successful_fetch_at", sa.DateTime(timezone=True), nullable=True)
                )
            if "last_attempted_at" not in existing_cols:
                batch_op.add_column(
                    sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True)
                )
            if "last_successful_record_count" not in existing_cols:
                batch_op.add_column(
                    sa.Column("last_successful_record_count", sa.Integer(), server_default="0", nullable=False)
                )
            if "cooldown_until" not in existing_cols:
                batch_op.add_column(
                    sa.Column("cooldown_until", sa.DateTime(timezone=True), nullable=True)
                )

        # Update cache scope index / constraint if not present
        existing_indices = [i["name"] for i in inspector.get_indexes("mandi_cache_metadata")]
        if "ix_mandi_cache_scope" not in existing_indices:
            try:
                op.create_index(
                    "ix_mandi_cache_scope",
                    "mandi_cache_metadata",
                    ["state", "district", "market", "commodity"],
                    unique=False
                )
            except Exception:
                pass

    # 2. Update mandi_price_records index to cover state
    if "mandi_price_records" in existing_tables:
        existing_indices = [i["name"] for i in inspector.get_indexes("mandi_price_records")]
        if "ix_mandi_query_v2" not in existing_indices:
            try:
                op.create_index(
                    "ix_mandi_query_v2",
                    "mandi_price_records",
                    ["state", "district", "market", "commodity", "arrival_date"],
                    unique=False
                )
            except Exception:
                pass


def downgrade() -> None:
    """Downgrade schema from cache resilience additions."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if "mandi_cache_metadata" in existing_tables:
        existing_indices = [i["name"] for i in inspector.get_indexes("mandi_cache_metadata")]
        if "ix_mandi_cache_scope" in existing_indices:
            try:
                op.drop_index("ix_mandi_cache_scope", table_name="mandi_cache_metadata")
            except Exception:
                pass

        if conn.dialect.name != "sqlite":
            existing_cols = [c["name"] for c in inspector.get_columns("mandi_cache_metadata")]
            with op.batch_alter_table("mandi_cache_metadata") as batch_op:
                for col in ("cooldown_until", "last_successful_record_count", "last_attempted_at", "last_successful_fetch_at", "state"):
                    if col in existing_cols:
                        batch_op.drop_column(col)

    if "mandi_price_records" in existing_tables:
        existing_indices = [i["name"] for i in inspector.get_indexes("mandi_price_records")]
        if "ix_mandi_query_v2" in existing_indices:
            try:
                op.drop_index("ix_mandi_query_v2", table_name="mandi_price_records")
            except Exception:
                pass
