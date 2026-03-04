"""phase1 core schema

Revision ID: 0001_phase1_core
Revises: 
Create Date: 2026-03-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_phase1_core"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("telegram_id"),
    )

    op.create_table(
        "exchange_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exchange", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("api_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "exchange", "label", name="uq_exchange_account_user_exchange_label"),
    )

    op.create_table(
        "wallets_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exchange_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("asset_symbol", sa.String(length=32), nullable=False),
        sa.Column("wallet_balance", sa.Numeric(38, 18), nullable=False),
        sa.Column("available_balance", sa.Numeric(38, 18), nullable=True),
        sa.Column("locked_balance", sa.Numeric(38, 18), nullable=True),
        sa.Column("usd_value", sa.Numeric(38, 18), nullable=True),
        sa.Column("source_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exchange_account_id"], ["exchange_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wallet_snapshots_account_ts", "wallets_snapshots", ["exchange_account_id", "snapshot_ts"], unique=False)
    op.create_index("ix_wallet_snapshots_asset_ts", "wallets_snapshots", ["asset_symbol", "snapshot_ts"], unique=False)

    op.create_table(
        "transactions_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exchange_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_event_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("asset_symbol", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Numeric(38, 18), nullable=False),
        sa.Column("amount_usd", sa.Numeric(38, 18), nullable=True),
        sa.Column("fee_amount", sa.Numeric(38, 18), nullable=True),
        sa.Column("fee_asset_symbol", sa.String(length=32), nullable=True),
        sa.Column("event_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["exchange_account_id"], ["exchange_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exchange_account_id", "source", "external_event_id", name="uq_ledger_event"),
    )
    op.create_index(
        "ix_transactions_ledger_account_ts",
        "transactions_ledger",
        ["exchange_account_id", "event_ts"],
        unique=False,
    )
    op.create_index("ix_transactions_ledger_asset_ts", "transactions_ledger", ["asset_symbol", "event_ts"], unique=False)

    op.create_table(
        "manual_holdings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Numeric(38, 18), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("avg_cost_per_unit", sa.Numeric(38, 18), nullable=False),
        sa.Column("cost_currency", sa.String(length=8), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("manual_holdings")
    op.drop_index("ix_transactions_ledger_asset_ts", table_name="transactions_ledger")
    op.drop_index("ix_transactions_ledger_account_ts", table_name="transactions_ledger")
    op.drop_table("transactions_ledger")
    op.drop_index("ix_wallet_snapshots_asset_ts", table_name="wallets_snapshots")
    op.drop_index("ix_wallet_snapshots_account_ts", table_name="wallets_snapshots")
    op.drop_table("wallets_snapshots")
    op.drop_table("exchange_accounts")
    op.drop_table("users")
