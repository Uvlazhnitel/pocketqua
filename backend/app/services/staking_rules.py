from dataclasses import dataclass
from datetime import datetime, timezone

from backend.app.db import models
from backend.app.services.recommendations import build_action_payload


@dataclass
class StakingEngineAction:
    action_type: models.ActionType
    title: str
    reason: str
    payload_json: dict


def _days_to(ts: datetime, now: datetime) -> int:
    return (ts.date() - now.date()).days


def _as_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def build_staking_actions(
    *,
    strategy: models.Strategy,
    staking_positions: list[models.StakingPosition],
) -> list[StakingEngineAction]:
    now = datetime.now(timezone.utc)
    actions: list[StakingEngineAction] = []

    for position in staking_positions:
        symbol = position.asset.symbol
        provider = position.provider

        if position.is_locked and position.unlock_at is not None:
            unlock_at = _as_utc(position.unlock_at)
            days_to_unlock = _days_to(unlock_at, now)
            if 0 <= days_to_unlock <= strategy.staking_unlock_window_days:
                actions.append(
                    StakingEngineAction(
                        action_type=models.ActionType.STAKING_UNLOCK_PLAN,
                        title=f"Prepare unlock plan for {symbol} at {provider}",
                        reason=(
                            f"Unlock at {unlock_at.isoformat()} in {days_to_unlock} days "
                            f"(window={strategy.staking_unlock_window_days})"
                        ),
                        payload_json=build_action_payload(
                            effect="Prepare rebalance/liquidity action before unlock",
                            estimated_cost_usd=None,
                            risk_note=None,
                            calculation={
                                "position_id": position.id,
                                "symbol": symbol,
                                "provider": provider,
                                "pending_rewards_usd": position.pending_rewards_usd,
                                "estimated_fee_usd": position.pending_rewards_usd
                                * (position.fee_percent / 100),
                                "net_reward_usd": position.pending_rewards_usd
                                - position.pending_rewards_usd * (position.fee_percent / 100),
                                "unlock_at": unlock_at.isoformat(),
                            },
                        ),
                    )
                )

        next_claim_at = _as_utc(position.next_claim_at) if position.next_claim_at else None

        if next_claim_at is not None and next_claim_at <= now:
            estimated_fee_usd = position.pending_rewards_usd * (position.fee_percent / 100)
            net_reward_usd = position.pending_rewards_usd - estimated_fee_usd

            if net_reward_usd >= strategy.staking_min_net_reward_usd:
                action_type = (
                    models.ActionType.STAKING_RESTAKE
                    if strategy.staking_restake_enabled
                    else models.ActionType.STAKING_CLAIM
                )
                verb = "Restake" if action_type == models.ActionType.STAKING_RESTAKE else "Claim"
                actions.append(
                    StakingEngineAction(
                        action_type=action_type,
                        title=f"{verb} rewards for {symbol} at {provider}",
                        reason=(
                            f"Claim due since {next_claim_at.isoformat()}; "
                            f"net reward {net_reward_usd:.2f} USD >= "
                            f"threshold {strategy.staking_min_net_reward_usd:.2f} USD"
                        ),
                        payload_json=build_action_payload(
                            effect=(
                                "Compound staking rewards"
                                if action_type == models.ActionType.STAKING_RESTAKE
                                else "Realize staking rewards"
                            ),
                            estimated_cost_usd=estimated_fee_usd,
                            risk_note=None,
                            calculation={
                                "position_id": position.id,
                                "symbol": symbol,
                                "provider": provider,
                                "pending_rewards_usd": position.pending_rewards_usd,
                                "estimated_fee_usd": estimated_fee_usd,
                                "net_reward_usd": net_reward_usd,
                                "next_claim_at": next_claim_at.isoformat(),
                            },
                        ),
                    )
                )

    return actions
