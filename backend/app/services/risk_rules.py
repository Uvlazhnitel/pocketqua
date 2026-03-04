from dataclasses import dataclass

from backend.app.db import models
from backend.app.services.recommendations import build_action_payload


@dataclass
class RiskEngineAction:
    action_type: models.ActionType
    title: str
    reason: str
    payload_json: dict


def build_risk_actions(
    *,
    strategy: models.Strategy,
    weights: dict[str, float],
    staking_positions: list[models.StakingPosition],
    price_by_symbol: dict[str, float],
    total_value_usd: float,
    risk_mode: models.RiskMode,
    previous_risk_mode: models.RiskMode | None,
) -> list[RiskEngineAction]:
    actions: list[RiskEngineAction] = []

    if previous_risk_mode is not None and previous_risk_mode != risk_mode:
        actions.append(
            RiskEngineAction(
                action_type=models.ActionType.RISK_MODE_CHANGE,
                title=f"Risk mode changed to {risk_mode.value}",
                reason=f"Previous mode was {previous_risk_mode.value}",
                payload_json=build_action_payload(
                    effect="Adjust behavior to risk mode",
                    estimated_cost_usd=None,
                    risk_note=None,
                    calculation={
                        "previous_risk_mode": previous_risk_mode.value,
                        "risk_mode": risk_mode.value,
                    },
                ),
            )
        )

    for symbol, weight in weights.items():
        if weight > strategy.max_asset_weight:
            actions.append(
                RiskEngineAction(
                    action_type=models.ActionType.RISK_ASSET_CONCENTRATION,
                    title=f"Asset concentration high: {symbol}",
                    reason=f"{symbol} weight {weight:.4f} exceeds limit {strategy.max_asset_weight:.4f}",
                    payload_json=build_action_payload(
                        effect="Reduce single-asset concentration",
                        estimated_cost_usd=None,
                        risk_note=None,
                        calculation={
                            "symbol": symbol,
                            "current_weight": weight,
                            "limit": strategy.max_asset_weight,
                        },
                    ),
                )
            )

    provider_values: dict[str, float] = {}
    missing_price_providers: set[str] = set()
    for pos in staking_positions:
        symbol = pos.asset.symbol
        if symbol not in price_by_symbol:
            missing_price_providers.add(pos.provider)
            continue
        provider_values[pos.provider] = provider_values.get(pos.provider, 0.0) + (
            pos.staked_amount * price_by_symbol[symbol]
        )

    provider_total = sum(provider_values.values())
    if provider_total > 0:
        for provider, value in provider_values.items():
            weight = value / provider_total
            if weight > strategy.max_provider_weight:
                note = None
                if missing_price_providers:
                    missing = ", ".join(sorted(missing_price_providers))
                    note = f"Missing prices for providers: {missing}"
                actions.append(
                    RiskEngineAction(
                        action_type=models.ActionType.RISK_PROVIDER_CONCENTRATION,
                        title=f"Provider concentration high: {provider}",
                        reason=(
                            f"Provider weight {weight:.4f} exceeds limit "
                            f"{strategy.max_provider_weight:.4f}"
                        ),
                        payload_json=build_action_payload(
                            effect="Reduce provider concentration",
                            estimated_cost_usd=None,
                            risk_note=note,
                            calculation={
                                "provider": provider,
                                "current_weight": weight,
                                "limit": strategy.max_provider_weight,
                            },
                        ),
                    )
                )

    return actions
