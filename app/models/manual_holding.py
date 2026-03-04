from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin


class ManualHolding(Base, IdMixin, TimestampMixin):
    __tablename__ = "manual_holdings"

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    avg_cost_per_unit: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    cost_currency: Mapped[str] = mapped_column(String(8), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="manual_holdings")
