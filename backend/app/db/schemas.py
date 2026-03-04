from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class AssetClassSchema(str, Enum):
    crypto = "crypto"
    metal = "metal"
    cash = "cash"
    stable = "stable"


class PositionUpsertIn(BaseModel):
    symbol: str
    name: str
    asset_class: AssetClassSchema
    account: str = "manual"
    amount: float
    avg_cost_eur: float | None = None

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("symbol must not be empty")
        return value


class PriceUpsertIn(BaseModel):
    symbol: str
    price_eur: float = Field(gt=0)

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
    base_currency: str = "EUR"
    dca_enabled: bool = False
    dca_interval_days: int = Field(default=7, ge=1)
    staking_unlock_window_days: int = Field(default=3, ge=1)
    staking_min_net_reward_eur: float = Field(default=10.0, ge=0)
    staking_restake_enabled: bool = True
    targets: list[TargetIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_weights(self) -> "StrategyUpsertIn":
        if not self.targets:
            return self
        total = sum(t.target_weight for t in self.targets)
        if abs(total - 1.0) > 1e-9:
            raise ValueError("sum of target_weight must equal 1.0")
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
    pending_rewards_eur: float = Field(default=0.0, ge=0)

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
    pending_rewards_eur: float | None = Field(default=None, ge=0)


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
    pending_rewards_eur: float
    last_updated_at: datetime


class AssetValuationOut(BaseModel):
    symbol: str
    value_eur: float
    weight: float


class PortfolioSummaryOut(BaseModel):
    total_value_eur: float
    assets: list[AssetValuationOut]
    warnings: list[str]


class ActionOut(BaseModel):
    id: int
    action_type: str
    title: str
    reason: str
    effect: str
    estimated_cost_eur: float | None
    risk_note: str | None
    calculation: dict
    created_at: datetime
    status: str
