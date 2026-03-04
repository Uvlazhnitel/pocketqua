import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.pnl_repository import PnLRepository
from app.schemas.pnl import PnLBreakdownItem, PnLResponse
from app.services.ledger_normalizer import normalize_event


@dataclass
class AssetState:
    qty: Decimal = Decimal("0")
    cost_basis_usd: Decimal = Decimal("0")
    realized_pnl_usd: Decimal = Decimal("0")
    fees_usd: Decimal = Decimal("0")
    staking_yield_usd: Decimal = Decimal("0")


class PnLService:
    def __init__(self, db: Session):
        self.repo = PnLRepository(db)

    def get_pnl(self, user_id: uuid.UUID, start: datetime | None = None, end: datetime | None = None) -> PnLResponse:
        warnings: list[str] = []

        latest_wallet_rows = self.repo.latest_wallet_rows(user_id)
        latest_prices: dict[str, Decimal] = {}
        for row in latest_wallet_rows:
            if row.usd_value is not None and row.wallet_balance != 0:
                latest_prices[row.asset_symbol.upper()] = row.usd_value / row.wallet_balance

        events = self.repo.ledger_events(user_id=user_id, start=start, end=end)
        states: dict[str, AssetState] = defaultdict(AssetState)

        for event in events:
            symbol = event.asset_symbol.upper()
            price_hint = latest_prices.get(symbol)
            normalized = normalize_event(event, price_usd=price_hint)
            state = states[symbol]

            state.fees_usd += normalized.fee_usd

            if normalized.kind == "reward":
                reward_usd = normalized.usd_delta
                if reward_usd is None and price_hint is not None:
                    reward_usd = abs(normalized.quantity_delta) * price_hint
                if reward_usd is None:
                    reward_usd = Decimal("0")
                    warnings.append(f"Missing USD valuation for reward event in {symbol}")

                state.staking_yield_usd += abs(reward_usd)
                state.qty += normalized.quantity_delta
                state.cost_basis_usd += Decimal("0")
                continue

            if normalized.kind != "trade":
                continue

            qty = normalized.quantity_delta
            usd = normalized.usd_delta

            if qty == 0:
                continue

            if qty > 0:
                if usd is None:
                    if price_hint is None:
                        warnings.append(f"Cannot infer buy cost for {symbol}; missing USD delta and price")
                        continue
                    cost = abs(qty) * price_hint
                else:
                    cost = abs(usd)

                state.qty += qty
                state.cost_basis_usd += cost
                continue

            sell_qty = abs(qty)
            if state.qty <= 0:
                warnings.append(f"Sell event for {symbol} without inventory; skipped from realized PnL")
                continue

            matched_qty = min(sell_qty, state.qty)
            avg_cost = state.cost_basis_usd / state.qty if state.qty > 0 else Decimal("0")
            matched_cost = matched_qty * avg_cost

            if usd is None:
                if price_hint is None:
                    warnings.append(f"Cannot infer sell proceeds for {symbol}; missing USD delta and price")
                    proceeds = Decimal("0")
                else:
                    proceeds = matched_qty * price_hint
            else:
                proceeds = abs(usd) * (matched_qty / sell_qty)

            state.realized_pnl_usd += proceeds - matched_cost
            state.qty -= matched_qty
            state.cost_basis_usd -= matched_cost

        breakdown: list[PnLBreakdownItem] = []
        realized_total = Decimal("0")
        unrealized_total = Decimal("0")
        fees_total = Decimal("0")
        staking_total = Decimal("0")

        for symbol, state in sorted(states.items()):
            mark_price = latest_prices.get(symbol)
            unrealized = Decimal("0")

            if state.qty > 0:
                if mark_price is not None:
                    unrealized = (state.qty * mark_price) - state.cost_basis_usd
                else:
                    warnings.append(f"Missing mark price for {symbol}; unrealized PnL set to 0")

            realized_total += state.realized_pnl_usd
            unrealized_total += unrealized
            fees_total += state.fees_usd
            staking_total += state.staking_yield_usd

            breakdown.append(
                PnLBreakdownItem(
                    symbol=symbol,
                    realized_pnl_usd=state.realized_pnl_usd,
                    unrealized_pnl_usd=unrealized,
                    fees_usd=state.fees_usd,
                    staking_yield_usd=state.staking_yield_usd,
                    position_qty=state.qty,
                    cost_basis_usd=state.cost_basis_usd,
                    mark_price_usd=mark_price,
                )
            )

        total_pnl = realized_total + unrealized_total + staking_total - fees_total

        return PnLResponse(
            as_of=datetime.now(timezone.utc),
            realized_pnl_usd=realized_total,
            unrealized_pnl_usd=unrealized_total,
            fees_usd=fees_total,
            staking_yield_usd=staking_total,
            total_pnl_usd=total_pnl,
            breakdown=breakdown,
            warnings=sorted(set(warnings)),
        )
