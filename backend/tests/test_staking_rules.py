from datetime import datetime, timedelta, timezone

from backend.app.db import models
from backend.app.services.rule_engine import run_rules


def _strategy(**kwargs) -> models.Strategy:
    defaults = {
        "id": 1,
        "name": "mvp",
        "base_currency": "EUR",
        "is_active": True,
        "dca_enabled": False,
        "dca_interval_days": 7,
        "staking_unlock_window_days": 3,
        "staking_min_net_reward_eur": 10.0,
        "staking_restake_enabled": True,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return models.Strategy(**defaults)


def _staking_position(**kwargs) -> models.StakingPosition:
    asset = models.Asset(symbol=kwargs.get("symbol", "ETH"), name="Ethereum", asset_class=models.AssetClass.CRYPTO)
    defaults = {
        "id": kwargs.get("id", 1),
        "asset": asset,
        "asset_id": 1,
        "provider": kwargs.get("provider", "Lido"),
        "account": "manual",
        "staked_amount": 10.0,
        "apr_percent": 4.5,
        "fee_percent": 10.0,
        "lockup_days": 0,
        "unbonding_days": 0,
        "is_locked": False,
        "unlock_at": None,
        "next_claim_at": None,
        "pending_rewards_asset": 0.0,
        "pending_rewards_eur": 0.0,
        "last_updated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return models.StakingPosition(**defaults)


def test_unlock_plan_generated_in_window() -> None:
    strategy = _strategy(staking_unlock_window_days=3)
    pos = _staking_position(is_locked=True, unlock_at=datetime.now(timezone.utc) + timedelta(days=1))

    actions = run_rules(strategy=strategy, targets=[], weights={}, staking_positions=[pos])
    action_types = {a.action_type for a in actions}
    assert models.ActionType.STAKING_UNLOCK_PLAN in action_types


def test_unlock_plan_not_generated_outside_window() -> None:
    strategy = _strategy(staking_unlock_window_days=3)
    pos = _staking_position(is_locked=True, unlock_at=datetime.now(timezone.utc) + timedelta(days=10))

    actions = run_rules(strategy=strategy, targets=[], weights={}, staking_positions=[pos])
    action_types = {a.action_type for a in actions}
    assert models.ActionType.STAKING_UNLOCK_PLAN not in action_types
    assert models.ActionType.NOOP in action_types


def test_claim_or_restake_generated_on_due_and_threshold() -> None:
    strategy = _strategy(staking_min_net_reward_eur=10.0, staking_restake_enabled=True)
    pos = _staking_position(
        pending_rewards_eur=20.0,
        fee_percent=10.0,
        next_claim_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    actions = run_rules(strategy=strategy, targets=[], weights={}, staking_positions=[pos])
    action_types = {a.action_type for a in actions}
    assert models.ActionType.STAKING_RESTAKE in action_types


def test_claim_not_generated_if_below_threshold() -> None:
    strategy = _strategy(staking_min_net_reward_eur=50.0)
    pos = _staking_position(
        pending_rewards_eur=20.0,
        fee_percent=10.0,
        next_claim_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    actions = run_rules(strategy=strategy, targets=[], weights={}, staking_positions=[pos])
    action_types = {a.action_type for a in actions}
    assert models.ActionType.STAKING_RESTAKE not in action_types
    assert models.ActionType.STAKING_CLAIM not in action_types
    assert models.ActionType.NOOP in action_types


def test_noop_only_when_no_portfolio_and_no_staking_actions() -> None:
    strategy = _strategy()
    actions = run_rules(strategy=strategy, targets=[], weights={}, staking_positions=[])
    assert len(actions) == 1
    assert actions[0].action_type == models.ActionType.NOOP
