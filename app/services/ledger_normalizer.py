from dataclasses import dataclass
from decimal import Decimal

from app.models.transactions_ledger import TransactionsLedger

USD_LIKE = {"USD", "USDT", "USDC", "BUSD", "DAI"}
REWARD_HINTS = {"reward", "staking", "interest", "earn", "apr", "apy"}


@dataclass
class NormalizedLedgerEvent:
    symbol: str
    kind: str
    quantity_delta: Decimal
    usd_delta: Decimal | None
    fee_usd: Decimal


def _safe_decimal(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal("0")


def classify_kind(event: TransactionsLedger) -> str:
    raw = (event.event_type or "").lower()
    payload = str(event.source_payload).lower()

    if raw in {"transfer", "deposit", "withdrawal"}:
        return "transfer"
    if raw == "trade":
        return "trade"
    if any(token in raw for token in REWARD_HINTS) or any(token in payload for token in REWARD_HINTS):
        return "reward"
    return "other"


def normalize_event(event: TransactionsLedger, price_usd: Decimal | None = None) -> NormalizedLedgerEvent:
    kind = classify_kind(event)
    qty = _safe_decimal(event.amount)
    usd_delta = event.amount_usd

    fee_usd = Decimal("0")
    if event.fee_amount:
        if (event.fee_asset_symbol or "").upper() in USD_LIKE:
            fee_usd = abs(event.fee_amount)
        elif price_usd is not None:
            fee_usd = abs(event.fee_amount) * price_usd

    if kind == "reward" and usd_delta is None and price_usd is not None:
        usd_delta = abs(qty) * price_usd

    return NormalizedLedgerEvent(
        symbol=event.asset_symbol.upper(),
        kind=kind,
        quantity_delta=qty,
        usd_delta=usd_delta,
        fee_usd=fee_usd,
    )
