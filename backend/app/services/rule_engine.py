from dataclasses import dataclass
from datetime import datetime, timezone

from backend.app.db import models
from backend.app.services.recommendations import build_action_payload
from backend.app.services.staking_rules import build_staking_actions


@dataclass
class EngineAction:
    action_type: models.ActionType
    title: str
    reason: str
    payload_json: dict


ACTION_ORDER = {
    models.ActionType.STAKING_UNLOCK_PLAN: 1,
    models.ActionType.STAKING_CLAIM: 2,
    models.ActionType.STAKING_RESTAKE: 2,
    models.ActionType.REBALANCE: 3,
    models.ActionType.DCA: 4,
    models.ActionType.NOOP: 5,
}


def _today_ordinal() -> int:
    return datetime.now(timezone.utc).date().toordinal()


def _portfolio_actions(
    *, strategy: models.Strategy, targets: list[models.StrategyTarget], weights: dict[str, float]
) -> list[EngineAction]:
    actions: list[EngineAction] = []

    for target in targets:
        symbol = target.asset.symbol
        current_weight = weights.get(symbol, 0.0)

        if current_weight < target.band_min or current_weight > target.band_max:
            delta = target.target_weight - current_weight
            delta_pct = abs(delta) * 100
            direction = "increase" if delta > 0 else "decrease"
            title = f"Rebalance {symbol} by {delta_pct:.2f}%"
            reason = (
                f"{symbol} at {current_weight:.4f}, target {target.target_weight:.4f}, "
                f"allowed band [{target.band_min:.4f}, {target.band_max:.4f}]"
            )
            payload = build_action_payload(
                effect=f"{direction} {symbol} to align with strategy target",
                estimated_cost_eur=None,
                risk_note=None,
                calculation={
                    "symbol": symbol,
                    "current_weight": current_weight,
                    "target": target.target_weight,
                    "delta": delta,
                },
            )
            actions.append(
                EngineAction(
                    action_type=models.ActionType.REBALANCE,
                    title=title,
                    reason=reason,
                    payload_json=payload,
                )
            )

    dca_due = strategy.dca_enabled and (_today_ordinal() % strategy.dca_interval_days == 0)
    if dca_due and targets:
        below_target = []
        for target in targets:
            symbol = target.asset.symbol
            current_weight = weights.get(symbol, 0.0)
            if current_weight < target.target_weight:
                below_target.append(
                    {
                        "symbol": symbol,
                        "current_weight": current_weight,
                        "target": target.target_weight,
                        "delta": target.target_weight - current_weight,
                    }
                )

        if below_target:
            symbols = ", ".join(item["symbol"] for item in below_target)
            actions.append(
                EngineAction(
                    action_type=models.ActionType.DCA,
                    title=f"DCA buy candidates: {symbols}",
                    reason="DCA interval is due and selected assets are below target",
                    payload_json=build_action_payload(
                        effect="Add funds to assets below strategy target",
                        estimated_cost_eur=None,
                        risk_note=None,
                        calculation={"candidates": below_target},
                    ),
                )
            )

    return actions


def run_rules(
    *,
    strategy: models.Strategy,
    targets: list[models.StrategyTarget],
    weights: dict[str, float],
    staking_positions: list[models.StakingPosition],
) -> list[EngineAction]:
    actions: list[EngineAction] = []

    actions.extend(_portfolio_actions(strategy=strategy, targets=targets, weights=weights))

    staking_actions = build_staking_actions(strategy=strategy, staking_positions=staking_positions)
    actions.extend(
        [
            EngineAction(
                action_type=a.action_type,
                title=a.title,
                reason=a.reason,
                payload_json=a.payload_json,
            )
            for a in staking_actions
        ]
    )

    if not actions:
        actions.append(
            EngineAction(
                action_type=models.ActionType.NOOP,
                title="No action required",
                reason="Portfolio within strategy bands",
                payload_json=build_action_payload(
                    effect="No rebalance, DCA, or staking action required",
                    estimated_cost_eur=None,
                    risk_note=None,
                    calculation={},
                ),
            )
        )

    actions.sort(key=lambda a: ACTION_ORDER.get(a.action_type, 99))
    return actions
