from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IdMixin


class WalletSnapshot(Base, IdMixin):
    __tablename__ = "wallets_snapshots"
    __table_args__ = (
        Index("ix_wallet_snapshots_account_ts", "exchange_account_id", "snapshot_ts"),
        Index("ix_wallet_snapshots_asset_ts", "asset_symbol", "snapshot_ts"),
    )

    exchange_account_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("exchange_accounts.id", ondelete="CASCADE"), nullable=False)
    snapshot_ts: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    wallet_balance: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    available_balance: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    locked_balance: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    usd_value: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    source_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    exchange_account = relationship("ExchangeAccount", back_populates="wallet_snapshots")
