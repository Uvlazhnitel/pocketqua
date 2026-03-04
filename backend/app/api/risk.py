from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db import crud
from backend.app.db.base import get_db
from backend.app.db.schemas import RiskBreachOut, RiskSummaryOut
from backend.app.services.portfolio_calc import build_portfolio_snapshot, snapshot_weights
from backend.app.services.risk_mode import calculate_risk_state

router = APIRouter(prefix="/v1/risk", tags=["risk"])


@router.get("/summary", response_model=RiskSummaryOut)
def risk_summary(db: Session = Depends(get_db)) -> RiskSummaryOut:
    strategy = crud.get_active_strategy(db)
    if not strategy:
        raise HTTPException(status_code=404, detail="active strategy not found")

    snapshot = build_portfolio_snapshot(db)
    weights = snapshot_weights(snapshot)
    latest_snapshot = crud.get_latest_portfolio_snapshot(db)

    peak_value_usd, drawdown_pct, risk_mode, _ = calculate_risk_state(
        current_total_value_usd=snapshot["total_value_usd"],
        previous_snapshot=latest_snapshot,
        strategy=strategy,
    )

    asset_breaches: list[RiskBreachOut] = []
    for symbol, weight in weights.items():
        if weight > strategy.max_asset_weight:
            asset_breaches.append(
                RiskBreachOut(key=symbol, current_weight=weight, limit=strategy.max_asset_weight)
            )

    prices = crud.get_prices_by_symbol(db)
    provider_values: dict[str, float] = {}
    for pos in crud.list_staking_positions(db):
        price = prices.get(pos.asset.symbol)
        if price is None:
            continue
        provider_values[pos.provider] = provider_values.get(pos.provider, 0.0) + (pos.staked_amount * price)

    provider_total = sum(provider_values.values())
    provider_breaches: list[RiskBreachOut] = []
    if provider_total > 0:
        for provider, value in provider_values.items():
            weight = value / provider_total
            if weight > strategy.max_provider_weight:
                provider_breaches.append(
                    RiskBreachOut(key=provider, current_weight=weight, limit=strategy.max_provider_weight)
                )

    return RiskSummaryOut(
        current_total_value_usd=snapshot["total_value_usd"],
        peak_total_value_usd=peak_value_usd,
        drawdown_pct=drawdown_pct,
        risk_mode=risk_mode.value,
        asset_concentration_breaches=asset_breaches,
        provider_concentration_breaches=provider_breaches,
    )
