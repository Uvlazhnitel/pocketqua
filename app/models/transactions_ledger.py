from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IdMixin


class TransactionsLedger(Base, IdMixin):
    __tablename__ = "transactions_ledger"
    __table_args__ = (
        UniqueConstraint("exchange_account_id", "source", "external_event_id", name="uq_ledger_event"),
        Index("ix_transactions_ledger_account_ts", "exchange_account_id", "event_ts"),
        Index("ix_transactions_ledger_asset_ts", "asset_symbol", "event_ts"),
    )

    exchange_account_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    amount_usd: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    fee_amount: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    fee_asset_symbol: Mapped[str | None] = mapped_column(String(32), nullable=True)
    event_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    exchange_account = relationship("ExchangeAccount", back_populates="ledger_events")
