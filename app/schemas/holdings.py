from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CryptoHoldingItem(BaseModel):
    symbol: str
    amount: Decimal
    price_usd: Decimal | None
    usd_value: Decimal | None


class ManualHoldingValuedItem(BaseModel):
    asset_type: str
    quantity: Decimal
    unit: str
    spot_price_usd_per_oz: Decimal | None
    estimated_usd_value: Decimal | None
    valuation_source: str | None
    note: str | None


class HoldingsResponse(BaseModel):
    as_of: datetime
    total_crypto_usd: Decimal
    total_manual_usd: Decimal
    total_portfolio_usd: Decimal
    crypto: list[CryptoHoldingItem]
    manual_holdings: list[ManualHoldingValuedItem]
    warnings: list[str]
