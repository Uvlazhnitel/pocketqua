from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
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
    STAKING_CLAIM = "staking_claim"
    STAKING_RESTAKE = "staking_restake"
    STAKING_UNLOCK_PLAN = "staking_unlock_plan"
    RISK_ASSET_CONCENTRATION = "risk_asset_concentration"
    RISK_PROVIDER_CONCENTRATION = "risk_provider_concentration"
    RISK_MODE_CHANGE = "risk_mode_change"
    RISK_FEE_WARNING = "risk_fee_warning"


class RecommendationStatus(str, Enum):
    NEW = "new"
    DONE = "done"
    POSTPONED = "postponed"
    DISMISSED = "dismissed"


class RiskMode(str, Enum):
    NORMAL = "normal"
    CAUTION = "caution"
    DEFENSE = "defense"


class PriceSource(str, Enum):
    MANUAL = "manual"
    COINGECKO = "coingecko"


class PriceSyncRunStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"


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
    avg_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    asset: Mapped[Asset] = relationship()


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("asset_id", "source", name="uq_price_asset_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    price_usd: Mapped[float] = mapped_column(Float)
    source: Mapped[PriceSource] = mapped_column(SAEnum(PriceSource), nullable=False)
    is_override: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    asset: Mapped[Asset] = relationship()


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    base_currency: Mapped[str] = mapped_column(String(8), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    dca_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dca_interval_days: Mapped[int] = mapped_column(Integer, default=7)

    staking_unlock_window_days: Mapped[int] = mapped_column(Integer, default=3)
    staking_min_net_reward_usd: Mapped[float] = mapped_column(Float, default=10.0)
    staking_restake_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    max_asset_weight: Mapped[float] = mapped_column(Float, default=0.60)
    max_provider_weight: Mapped[float] = mapped_column(Float, default=0.50)
    drawdown_caution_pct: Mapped[float] = mapped_column(Float, default=0.10)
    drawdown_defense_pct: Mapped[float] = mapped_column(Float, default=0.20)
    min_trade_value_usd: Mapped[float] = mapped_column(Float, default=50.0)

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


class StakingPosition(Base):
    __tablename__ = "staking_positions"
    __table_args__ = (UniqueConstraint("asset_id", "provider", "account", name="uq_staking_identity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    provider: Mapped[str] = mapped_column(String(128), index=True)
    account: Mapped[str] = mapped_column(String(128), default="manual")

    staked_amount: Mapped[float] = mapped_column(Float, default=0.0)
    apr_percent: Mapped[float] = mapped_column(Float, default=0.0)
    fee_percent: Mapped[float] = mapped_column(Float, default=0.0)

    lockup_days: Mapped[int] = mapped_column(Integer, default=0)
    unbonding_days: Mapped[int] = mapped_column(Integer, default=0)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    unlock_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_claim_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    pending_rewards_asset: Mapped[float] = mapped_column(Float, default=0.0)
    pending_rewards_usd: Mapped[float] = mapped_column(Float, default=0.0)

    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

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


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    total_value_usd: Mapped[float] = mapped_column(Float)
    peak_value_usd: Mapped[float] = mapped_column(Float)
    drawdown_pct: Mapped[float] = mapped_column(Float)
    risk_mode: Mapped[RiskMode] = mapped_column(SAEnum(RiskMode), default=RiskMode.NORMAL)


class DecisionJournal(Base):
    __tablename__ = "decision_journal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.id"), index=True)
    old_status: Mapped[RecommendationStatus] = mapped_column(SAEnum(RecommendationStatus))
    new_status: Mapped[RecommendationStatus] = mapped_column(SAEnum(RecommendationStatus))
    note: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class TelegramChat(Base):
    __tablename__ = "telegram_chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    daily_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_daily_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_weekly_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class PriceSyncRun(Base):
    __tablename__ = "price_sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PriceSyncRunStatus] = mapped_column(SAEnum(PriceSyncRunStatus), default=PriceSyncRunStatus.OK)
    updated_assets_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_summary: Mapped[str | None] = mapped_column(String(2048), nullable=True)
