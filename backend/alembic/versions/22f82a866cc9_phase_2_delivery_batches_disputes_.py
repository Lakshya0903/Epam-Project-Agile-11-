"""phase_2_delivery_batches_disputes_payments

Revision ID: 22f82a866cc9
Revises: 
Create Date: 2026-11-10 20:44:01.776417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '22f82a866cc9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to Phase 2: Delivery Batches, Nationwide Logistics, Disputes & Payments."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. delivery_zones table
    if "delivery_zones" not in existing_tables:
        op.create_table(
            "delivery_zones",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("code", sa.String(), unique=True, index=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("state", sa.String(), nullable=False),
            sa.Column("covered_pincodes", sa.JSON(), nullable=True),
            sa.Column("min_weight_threshold_kg", sa.Float(), server_default="25.0", nullable=False),
            sa.Column("max_weight_capacity_kg", sa.Float(), server_default="500.0", nullable=False),
            sa.Column("max_orders_per_batch", sa.Integer(), server_default="50", nullable=False),
            sa.Column("dispatch_buffer_minutes", sa.Integer(), server_default="60", nullable=False),
            sa.Column("home_delivery_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("drop_point_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 2. shared_drop_points table
    if "shared_drop_points" not in existing_tables:
        op.create_table(
            "shared_drop_points",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("zone_id", sa.String(), sa.ForeignKey("delivery_zones.id", name="fk_drop_points_zone_id", ondelete="SET NULL"), nullable=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("code", sa.String(), unique=True, index=True, nullable=False),
            sa.Column("pincode", sa.String(), index=True, nullable=False),
            sa.Column("physical_address", sa.String(), nullable=False),
            sa.Column("operating_hours", sa.String(), server_default="08:00 - 20:00", nullable=True),
            sa.Column("capacity_orders", sa.Integer(), server_default="30", nullable=False),
            sa.Column("contact_person", sa.String(), nullable=True),
            sa.Column("contact_phone", sa.String(), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 3. Alter orders table
    if "orders" in existing_tables:
        cols = [c["name"] for c in inspector.get_columns("orders")]
        with op.batch_alter_table("orders") as batch_op:
            if "delivery_pincode" not in cols:
                batch_op.add_column(sa.Column("delivery_pincode", sa.String(), nullable=True))
            if "delivery_mode" not in cols:
                batch_op.add_column(sa.Column("delivery_mode", sa.String(), server_default="home_delivery", nullable=True))
            if "shared_drop_point_id" not in cols:
                batch_op.add_column(sa.Column("shared_drop_point_id", sa.String(), sa.ForeignKey("shared_drop_points.id", name="fk_orders_drop_point_id", ondelete="SET NULL"), nullable=True))
            if "dispatched_at" not in cols:
                batch_op.add_column(sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True))
            if "delivered_at" not in cols:
                batch_op.add_column(sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))
            if "cancelled_at" not in cols:
                batch_op.add_column(sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))

    # 4. Alter delivery_batches table
    if "delivery_batches" in existing_tables:
        cols = [c["name"] for c in inspector.get_columns("delivery_batches")]
        with op.batch_alter_table("delivery_batches") as batch_op:
            if "batch_code" not in cols:
                batch_op.add_column(sa.Column("batch_code", sa.String(), nullable=True))
            if "zone_id" not in cols:
                batch_op.add_column(sa.Column("zone_id", sa.String(), sa.ForeignKey("delivery_zones.id", name="fk_batches_zone_id", ondelete="SET NULL"), nullable=True))
            if "delivery_mode" not in cols:
                batch_op.add_column(sa.Column("delivery_mode", sa.String(), server_default="home_delivery", nullable=True))
            if "shared_drop_point_id" not in cols:
                batch_op.add_column(sa.Column("shared_drop_point_id", sa.String(), sa.ForeignKey("shared_drop_points.id", name="fk_batches_drop_point_id", ondelete="SET NULL"), nullable=True))
            if "max_weight_kg" not in cols:
                batch_op.add_column(sa.Column("max_weight_kg", sa.Float(), server_default="500.0", nullable=True))
            if "max_orders" not in cols:
                batch_op.add_column(sa.Column("max_orders", sa.Integer(), server_default="50", nullable=True))
            if "cutoff_time" not in cols:
                batch_op.add_column(sa.Column("cutoff_time", sa.DateTime(timezone=True), nullable=True))
            if "is_below_threshold" not in cols:
                batch_op.add_column(sa.Column("is_below_threshold", sa.Boolean(), server_default=sa.false(), nullable=True))
            if "needs_review" not in cols:
                batch_op.add_column(sa.Column("needs_review", sa.Boolean(), server_default=sa.false(), nullable=True))

    # 5. Alter deliveries table
    if "deliveries" in existing_tables:
        cols = [c["name"] for c in inspector.get_columns("deliveries")]
        with op.batch_alter_table("deliveries") as batch_op:
            if "delivery_mode" not in cols:
                batch_op.add_column(sa.Column("delivery_mode", sa.String(), server_default="home_delivery", nullable=True))
            if "shared_drop_point_id" not in cols:
                batch_op.add_column(sa.Column("shared_drop_point_id", sa.String(), sa.ForeignKey("shared_drop_points.id", name="fk_deliveries_drop_point_id", ondelete="SET NULL"), nullable=True))
            if "receiver_confirmed_at" not in cols:
                batch_op.add_column(sa.Column("receiver_confirmed_at", sa.DateTime(timezone=True), nullable=True))
            if "receiver_confirmation_notes" not in cols:
                batch_op.add_column(sa.Column("receiver_confirmation_notes", sa.String(), nullable=True))

    # 6. Alter payments table
    if "payments" in existing_tables:
        cols = [c["name"] for c in inspector.get_columns("payments")]
        with op.batch_alter_table("payments") as batch_op:
            if "escrow_held" not in cols:
                batch_op.add_column(sa.Column("escrow_held", sa.Boolean(), server_default=sa.true(), nullable=True))
            if "held_amount" not in cols:
                batch_op.add_column(sa.Column("held_amount", sa.Float(), server_default="0.0", nullable=True))
            if "gateway_order_id" not in cols:
                batch_op.add_column(sa.Column("gateway_order_id", sa.String(), nullable=True))
            if "gateway_payment_id" not in cols:
                batch_op.add_column(sa.Column("gateway_payment_id", sa.String(), nullable=True))
            if "gateway_signature" not in cols:
                batch_op.add_column(sa.Column("gateway_signature", sa.String(), nullable=True))
            if "refund_status" not in cols:
                batch_op.add_column(sa.Column("refund_status", sa.String(), nullable=True))
            if "refund_amount" not in cols:
                batch_op.add_column(sa.Column("refund_amount", sa.Float(), server_default="0.0", nullable=True))
            if "buyer_confirmed_at" not in cols:
                batch_op.add_column(sa.Column("buyer_confirmed_at", sa.DateTime(timezone=True), nullable=True))
            if "payout_released_at" not in cols:
                batch_op.add_column(sa.Column("payout_released_at", sa.DateTime(timezone=True), nullable=True))

    # 7. order_status_history table
    if "order_status_history" not in existing_tables:
        op.create_table(
            "order_status_history",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("order_id", sa.String(), sa.ForeignKey("orders.id", name="fk_history_order_id", ondelete="CASCADE"), nullable=False),
            sa.Column("from_status", sa.String(), nullable=True),
            sa.Column("to_status", sa.String(), nullable=False),
            sa.Column("changed_by_user_id", sa.String(), sa.ForeignKey("users.id", name="fk_history_user_id", ondelete="SET NULL"), nullable=True),
            sa.Column("role", sa.String(), nullable=True),
            sa.Column("notes", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 8. disputes table
    if "disputes" not in existing_tables:
        op.create_table(
            "disputes",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("order_id", sa.String(), sa.ForeignKey("orders.id", name="fk_disputes_order_id", ondelete="CASCADE"), unique=True, nullable=False),
            sa.Column("buyer_id", sa.String(), sa.ForeignKey("users.id", name="fk_disputes_buyer_id", ondelete="CASCADE"), nullable=False),
            sa.Column("reason", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=False),
            sa.Column("status", sa.String(), server_default="PENDING_REVIEW", nullable=False),
            sa.Column("resolution", sa.String(), nullable=True),
            sa.Column("reviewer_notes", sa.String(), nullable=True),
            sa.Column("assigned_reviewer_id", sa.String(), sa.ForeignKey("users.id", name="fk_disputes_reviewer_id", ondelete="SET NULL"), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 9. dispute_evidence table
    if "dispute_evidence" not in existing_tables:
        op.create_table(
            "dispute_evidence",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("dispute_id", sa.String(), sa.ForeignKey("disputes.id", name="fk_evidence_dispute_id", ondelete="CASCADE"), nullable=False),
            sa.Column("file_name", sa.String(), nullable=False),
            sa.Column("file_url", sa.String(), nullable=False),
            sa.Column("file_size_bytes", sa.Integer(), nullable=False),
            sa.Column("mime_type", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 10. payment_ledger_entries table
    if "payment_ledger_entries" not in existing_tables:
        op.create_table(
            "payment_ledger_entries",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("payment_id", sa.String(), sa.ForeignKey("payments.id", name="fk_ledger_payment_id", ondelete="CASCADE"), nullable=False),
            sa.Column("order_id", sa.String(), sa.ForeignKey("orders.id", name="fk_ledger_order_id", ondelete="CASCADE"), nullable=False),
            sa.Column("entry_type", sa.String(), nullable=False),
            sa.Column("amount", sa.Float(), nullable=False),
            sa.Column("currency", sa.String(), server_default="INR", nullable=False),
            sa.Column("description", sa.String(), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("payment_ledger_entries")
    op.drop_table("dispute_evidence")
    op.drop_table("disputes")
    op.drop_table("order_status_history")
    op.drop_table("shared_drop_points")
    op.drop_table("delivery_zones")
