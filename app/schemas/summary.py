from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SummaryAssetItem(BaseModel):
    symbol: str
    amount: Decimal
    usd_value: Decimal | None
    share_pct: Decimal


class SummaryManualHoldingItem(BaseModel):
    asset_type: str
    quantity: Decimal
    unit: str
    estimated_usd_value: Decimal | None
    note: str | None


class SummaryFreshness(BaseModel):
    last_sync_at: datetime | None
    lag_seconds: int | None


class SummaryResponse(BaseModel):
    as_of: datetime
    total_value_usd: Decimal
    assets: list[SummaryAssetItem]
    manual_holdings: list[SummaryManualHoldingItem]
    data_freshness: SummaryFreshness
    warnings: list[str]
