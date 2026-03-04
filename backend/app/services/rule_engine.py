from dataclasses import dataclass
from datetime import datetime, timezone

from backend.app.db import models
from backend.app.services.recommendations import build_action_payload
from backend.app.services.risk_rules import build_risk_actions
from backend.app.services.staking_rules import build_staking_actions


@dataclass
class EngineAction:
    action_type: models.ActionType
    title: str
    reason: str
    payload_json: dict


ACTION_ORDER = {
    models.ActionType.RISK_MODE_CHANGE: 1,
    models.ActionType.RISK_ASSET_CONCENTRATION: 2,
    models.ActionType.RISK_PROVIDER_CONCENTRATION: 2,
    models.ActionType.RISK_FEE_WARNING: 2,
    models.ActionType.STAKING_UNLOCK_PLAN: 3,
    models.ActionType.STAKING_CLAIM: 4,
    models.ActionType.STAKING_RESTAKE: 4,
    models.ActionType.REBALANCE: 5,
    models.ActionType.DCA: 6,
    models.ActionType.NOOP: 99,
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
            actions.append(
                EngineAction(
                    action_type=models.ActionType.REBALANCE,
                    title=f"Rebalance {symbol} by {delta_pct:.2f}%",
                    reason=(
                        f"{symbol} at {current_weight:.4f}, target {target.target_weight:.4f}, "
                        f"allowed band [{target.band_min:.4f}, {target.band_max:.4f}]"
                    ),
                    payload_json=build_action_payload(
                        effect=f"{direction} {symbol} to align with strategy target",
                        estimated_cost_usd=None,
                        risk_note=None,
                        calculation={
                            "symbol": symbol,
                            "current_weight": current_weight,
                            "target": target.target_weight,
                            "delta": delta,
                        },
                    ),
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
                        estimated_cost_usd=None,
                        risk_note=None,
                        calculation={"candidates": below_target},
                    ),
                )
            )

    return actions


def _apply_fee_guard(
    *,
    strategy: models.Strategy,
    total_value_usd: float,
    actions: list[EngineAction],
) -> list[EngineAction]:
    output: list[EngineAction] = []
    for action in actions:
        if action.action_type != models.ActionType.REBALANCE:
            output.append(action)
            continue

        delta = abs(float(action.payload_json.get("calculation", {}).get("delta", 0.0)))
        trade_value_usd = delta * total_value_usd
        if trade_value_usd < strategy.min_trade_value_usd:
            calc = action.payload_json.get("calculation", {})
            output.append(
                EngineAction(
                    action_type=models.ActionType.RISK_FEE_WARNING,
                    title=f"Skip small rebalance for {calc.get('symbol', 'asset')}",
                    reason=(
                        f"Estimated trade value {trade_value_usd:.2f} USD is below min trade "
                        f"value {strategy.min_trade_value_usd:.2f} USD"
                    ),
                    payload_json=build_action_payload(
                        effect="Avoid fee drag from tiny rebalance",
                        estimated_cost_usd=None,
                        risk_note=None,
                        calculation={
                            "symbol": calc.get("symbol"),
                            "trade_value_usd": trade_value_usd,
                            "min_trade_value_usd": strategy.min_trade_value_usd,
                        },
                    ),
                )
            )
            continue

        output.append(action)
    return output


def _apply_defense_mode(
    *,
    risk_mode: models.RiskMode,
    actions: list[EngineAction],
) -> list[EngineAction]:
    if risk_mode != models.RiskMode.DEFENSE:
        return actions

    filtered: list[EngineAction] = []
    suppressed_count = 0
    for action in actions:
        if action.action_type == models.ActionType.DCA:
            suppressed_count += 1
            continue

        if action.action_type == models.ActionType.STAKING_RESTAKE:
            suppressed_count += 1
            continue

        if action.action_type == models.ActionType.REBALANCE:
            delta = float(action.payload_json.get("calculation", {}).get("delta", 0.0))
            if delta > 0:
                suppressed_count += 1
                continue

        filtered.append(action)

    if suppressed_count > 0:
        filtered.append(
            EngineAction(
                action_type=models.ActionType.RISK_MODE_CHANGE,
                title="Defense mode filter applied",
                reason=f"Suppressed {suppressed_count} risk-on actions",
                payload_json=build_action_payload(
                    effect="Restrict risk-on actions in defense mode",
                    estimated_cost_usd=None,
                    risk_note=None,
                    calculation={"suppressed_actions": suppressed_count, "risk_mode": "defense"},
                ),
            )
        )

    return filtered


def run_rules(
    *,
    strategy: models.Strategy,
    targets: list[models.StrategyTarget],
    weights: dict[str, float],
    staking_positions: list[models.StakingPosition],
    total_value_usd: float,
    price_by_symbol: dict[str, float],
    risk_mode: models.RiskMode,
    previous_risk_mode: models.RiskMode | None,
) -> list[EngineAction]:
    actions: list[EngineAction] = []

    actions.extend(_portfolio_actions(strategy=strategy, targets=targets, weights=weights))
    actions.extend(
        [
            EngineAction(
                action_type=a.action_type,
                title=a.title,
                reason=a.reason,
                payload_json=a.payload_json,
            )
            for a in build_staking_actions(strategy=strategy, staking_positions=staking_positions)
        ]
    )
    actions.extend(
        [
            EngineAction(
                action_type=a.action_type,
                title=a.title,
                reason=a.reason,
                payload_json=a.payload_json,
            )
            for a in build_risk_actions(
                strategy=strategy,
                weights=weights,
                staking_positions=staking_positions,
                price_by_symbol=price_by_symbol,
                total_value_usd=total_value_usd,
                risk_mode=risk_mode,
                previous_risk_mode=previous_risk_mode,
            )
        ]
    )

    actions = _apply_fee_guard(strategy=strategy, total_value_usd=total_value_usd, actions=actions)
    actions = _apply_defense_mode(risk_mode=risk_mode, actions=actions)

    if not actions:
        actions.append(
            EngineAction(
                action_type=models.ActionType.NOOP,
                title="No action required",
                reason="Portfolio within strategy bands",
                payload_json=build_action_payload(
                    effect="No rebalance, DCA, staking, or risk action required",
                    estimated_cost_usd=None,
                    risk_note=None,
                    calculation={},
                ),
            )
        )

    actions.sort(key=lambda a: ACTION_ORDER.get(a.action_type, 999))
    return actions
