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
    targets: list[TargetIn]

    @model_validator(mode="after")
    def validate_weights(self) -> "StrategyUpsertIn":
        total = sum(t.target_weight for t in self.targets)
        if abs(total - 1.0) > 1e-9:
            raise ValueError("sum of target_weight must equal 1.0")
        return self


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
