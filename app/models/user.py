from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IdMixin, TimestampMixin


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)

    exchange_accounts = relationship("ExchangeAccount", back_populates="user", cascade="all, delete-orphan")
    manual_holdings = relationship("ManualHolding", back_populates="user", cascade="all, delete-orphan")
