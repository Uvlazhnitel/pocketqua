from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class AssetClassSchema(str, Enum):
    crypto = "crypto"
    metal = "metal"
    cash = "cash"
    stable = "stable"


class RecommendationStatusSchema(str, Enum):
    new = "new"
    done = "done"
    postponed = "postponed"
    dismissed = "dismissed"


class PositionUpsertIn(BaseModel):
    symbol: str
    name: str
    asset_class: AssetClassSchema
    account: str = "manual"
    amount: float
    avg_cost_usd: float | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("symbol must not be empty")
        return value


class PriceUpsertIn(BaseModel):
    symbol: str
    price_usd: float = Field(gt=0)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("symbol must not be empty")
        return value


class TargetIn(BaseModel):
    symbol: str
    name: str
    asset_class: AssetClassSchema
    target_weight: float = Field(ge=0, le=1)
    band_min: float = Field(ge=0, le=1)
    band_max: float = Field(ge=0, le=1)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("symbol must not be empty")
        return value

    @model_validator(mode="after")
    def validate_band(self) -> "TargetIn":
        if self.band_min > self.target_weight or self.band_max < self.target_weight:
            raise ValueError("target_weight must be inside [band_min, band_max]")
        return self


class StrategyUpsertIn(BaseModel):
    name: str
    base_currency: str = "USD"
    dca_enabled: bool = False
    dca_interval_days: int = Field(default=7, ge=1)
    staking_unlock_window_days: int = Field(default=3, ge=1)
    staking_min_net_reward_usd: float = Field(default=10.0, ge=0)
    staking_restake_enabled: bool = True

    max_asset_weight: float = Field(default=0.60, ge=0, le=1)
    max_provider_weight: float = Field(default=0.50, ge=0, le=1)
    drawdown_caution_pct: float = Field(default=0.10, ge=0, le=1)
    drawdown_defense_pct: float = Field(default=0.20, ge=0, le=1)
    min_trade_value_usd: float = Field(default=50.0, ge=0)

    targets: list[TargetIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_weights_and_thresholds(self) -> "StrategyUpsertIn":
        if self.targets:
            total = sum(t.target_weight for t in self.targets)
            if abs(total - 1.0) > 1e-9:
                raise ValueError("sum of target_weight must equal 1.0")
        if self.drawdown_caution_pct >= self.drawdown_defense_pct:
            raise ValueError("drawdown_caution_pct must be less than drawdown_defense_pct")
        return self


class StakingPositionUpsertIn(BaseModel):
    symbol: str
    name: str
    asset_class: AssetClassSchema
    provider: str
    account: str = "manual"
    staked_amount: float = Field(ge=0)
    apr_percent: float = Field(ge=0)
    fee_percent: float = Field(default=0.0, ge=0)
    lockup_days: int = Field(default=0, ge=0)
    unbonding_days: int = Field(default=0, ge=0)
    is_locked: bool = False
    unlock_at: datetime | None = None
    next_claim_at: datetime | None = None
    pending_rewards_asset: float = Field(default=0.0, ge=0)
    pending_rewards_usd: float = Field(default=0.0, ge=0)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("symbol must not be empty")
        return value

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("provider must not be empty")
        return value


class StakingPositionPatchIn(BaseModel):
    staked_amount: float | None = Field(default=None, ge=0)
    apr_percent: float | None = Field(default=None, ge=0)
    fee_percent: float | None = Field(default=None, ge=0)
    lockup_days: int | None = Field(default=None, ge=0)
    unbonding_days: int | None = Field(default=None, ge=0)
    is_locked: bool | None = None
    unlock_at: datetime | None = None
    next_claim_at: datetime | None = None
    pending_rewards_asset: float | None = Field(default=None, ge=0)
    pending_rewards_usd: float | None = Field(default=None, ge=0)


class StakingPositionOut(BaseModel):
    id: int
    symbol: str
    provider: str
    account: str
    staked_amount: float
    apr_percent: float
    fee_percent: float
    lockup_days: int
    unbonding_days: int
    is_locked: bool
    unlock_at: datetime | None
    next_claim_at: datetime | None
    pending_rewards_asset: float
    pending_rewards_usd: float
    last_updated_at: datetime


class AssetValuationOut(BaseModel):
    symbol: str
    value_usd: float
    weight: float


class PortfolioSummaryOut(BaseModel):
    total_value_usd: float
    assets: list[AssetValuationOut]
    warnings: list[str]


class ActionOut(BaseModel):
    id: int
    action_type: str
    title: str
    reason: str
    effect: str
    estimated_cost_usd: float | None
    risk_note: str | None
    calculation: dict
    created_at: datetime
    status: str


class ActionQueryIn(BaseModel):
    status: RecommendationStatusSchema | None = None
    limit: int = Field(default=5, ge=1, le=100)


class ActionStatusUpdateIn(BaseModel):
    new_status: RecommendationStatusSchema
    note: str | None = None

    @field_validator("new_status")
    @classmethod
    def disallow_new(cls, value: RecommendationStatusSchema) -> RecommendationStatusSchema:
        if value == RecommendationStatusSchema.new:
            raise ValueError("new_status must be done, postponed, or dismissed")
        return value


class DecisionJournalOut(BaseModel):
    id: int
    recommendation_id: int
    old_status: str
    new_status: str
    note: str | None
    created_at: datetime


class RiskBreachOut(BaseModel):
    key: str
    current_weight: float
    limit: float


class RiskSummaryOut(BaseModel):
    current_total_value_usd: float
    peak_total_value_usd: float
    drawdown_pct: float
    risk_mode: str
    asset_concentration_breaches: list[RiskBreachOut]
    provider_concentration_breaches: list[RiskBreachOut]


class TelegramChatRegisterIn(BaseModel):
    chat_id: int
    timezone: str = "UTC"
    daily_enabled: bool = True
    weekly_enabled: bool = True


class TelegramChatToggleIn(BaseModel):
    daily_enabled: bool | None = None
    weekly_enabled: bool | None = None
    timezone: str | None = None


class TelegramChatOut(BaseModel):
    id: int
    chat_id: int
    timezone: str
    daily_enabled: bool
    weekly_enabled: bool
    last_daily_sent_at: datetime | None
    last_weekly_sent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CSVImportErrorOut(BaseModel):
    row: int
    error: str


class PositionsImportOut(BaseModel):
    rows_total: int
    rows_imported: int
    rows_skipped: int
    errors: list[CSVImportErrorOut]
    dry_run: bool


class PriceSyncRunOut(BaseModel):
    run_id: int
    status: str
    updated_assets_count: int
    skipped_assets_count: int
    errors_count: int


class PriceSyncStatusOut(BaseModel):
    latest_run: dict | None
    next_scheduled_at: str | None
