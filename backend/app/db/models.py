from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class AssetClass(str, Enum):
    CRYPTO = "crypto"
    METAL = "metal"
    CASH = "cash"
    STABLE = "stable"


class ActionType(str, Enum):
    REBALANCE = "rebalance"
    DCA = "dca"
    NOOP = "noop"


class RecommendationStatus(str, Enum):
    NEW = "new"
    DONE = "done"
    POSTPONED = "postponed"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    asset_class: Mapped[AssetClass] = mapped_column(SAEnum(AssetClass), nullable=False)


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    account: Mapped[str] = mapped_column(String(128), default="manual")
    amount: Mapped[float] = mapped_column(Float)
    avg_cost_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    asset: Mapped[Asset] = relationship()


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    price_eur: Mapped[float] = mapped_column(Float)
    as_of: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    asset: Mapped[Asset] = relationship()


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    base_currency: Mapped[str] = mapped_column(String(8), default="EUR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    dca_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dca_interval_days: Mapped[int] = mapped_column(Integer, default=7)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class StrategyTarget(Base):
    __tablename__ = "strategy_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id"), index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    target_weight: Mapped[float] = mapped_column(Float)
    band_min: Mapped[float] = mapped_column(Float)
    band_max: Mapped[float] = mapped_column(Float)

    asset: Mapped[Asset] = relationship()


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id"), index=True)
    action_type: Mapped[ActionType] = mapped_column(SAEnum(ActionType), nullable=False)
    title: Mapped[str] = mapped_column(String(256))
    reason: Mapped[str] = mapped_column(String(512))
    payload_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        SAEnum(RecommendationStatus), default=RecommendationStatus.NEW
    )
