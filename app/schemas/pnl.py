from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PnLBreakdownItem(BaseModel):
    symbol: str
    realized_pnl_usd: Decimal
    unrealized_pnl_usd: Decimal
    fees_usd: Decimal
    staking_yield_usd: Decimal
    position_qty: Decimal
    cost_basis_usd: Decimal
    mark_price_usd: Decimal | None


class PnLResponse(BaseModel):
    as_of: datetime
    realized_pnl_usd: Decimal
    unrealized_pnl_usd: Decimal
    fees_usd: Decimal
    staking_yield_usd: Decimal
    total_pnl_usd: Decimal
    breakdown: list[PnLBreakdownItem]
    warnings: list[str]
