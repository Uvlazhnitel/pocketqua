from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin


class ExchangeAccount(Base, IdMixin, TimestampMixin):
    __tablename__ = "exchange_accounts"
    __table_args__ = (UniqueConstraint("user_id", "exchange", "label", name="uq_exchange_account_user_exchange_label"),)

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exchange: Mapped[str] = mapped_column(String(32), nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    api_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="exchange_accounts")
    wallet_snapshots = relationship("WalletSnapshot", back_populates="exchange_account", cascade="all, delete-orphan")
    ledger_events = relationship("TransactionsLedger", back_populates="exchange_account", cascade="all, delete-orphan")
