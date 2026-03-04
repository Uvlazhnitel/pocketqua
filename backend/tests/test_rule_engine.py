from datetime import datetime, timezone

from backend.app.db import models
from backend.app.services.rule_engine import run_rules


def _target(symbol: str, target: float, band_min: float, band_max: float) -> models.StrategyTarget:
    asset = models.Asset(symbol=symbol, name=symbol, asset_class=models.AssetClass.CRYPTO)
    return models.StrategyTarget(
        asset=asset,
        target_weight=target,
        band_min=band_min,
        band_max=band_max,
        strategy_id=1,
        asset_id=1,
    )


def _strategy(dca_enabled: bool = False, dca_interval_days: int = 7) -> models.Strategy:
    return models.Strategy(
        id=1,
        name="mvp",
        base_currency="EUR",
        is_active=True,
        dca_enabled=dca_enabled,
        dca_interval_days=dca_interval_days,
        staking_unlock_window_days=3,
        staking_min_net_reward_eur=10.0,
        staking_restake_enabled=True,
        created_at=datetime.now(timezone.utc),
    )


def test_rebalance_rule_triggered() -> None:
    strategy = _strategy()
    targets = [_target("BTC", 0.5, 0.45, 0.55)]
    actions = run_rules(strategy=strategy, targets=targets, weights={"BTC": 0.6}, staking_positions=[])
    assert len(actions) == 1
    assert actions[0].action_type == models.ActionType.REBALANCE


def test_noop_rule_when_within_band() -> None:
    strategy = _strategy()
    targets = [_target("BTC", 0.5, 0.45, 0.55)]
    actions = run_rules(strategy=strategy, targets=targets, weights={"BTC": 0.5}, staking_positions=[])
    assert len(actions) == 1
    assert actions[0].action_type == models.ActionType.NOOP


def test_dca_rule_due_generates_action() -> None:
    today_mod = datetime.now(timezone.utc).date().toordinal()
    interval = today_mod if today_mod > 0 else 1

    strategy = _strategy(dca_enabled=True, dca_interval_days=interval)
    targets = [_target("BTC", 0.6, 0.55, 0.65)]
    actions = run_rules(strategy=strategy, targets=targets, weights={"BTC": 0.5}, staking_positions=[])
    action_types = {a.action_type for a in actions}
    assert models.ActionType.DCA in action_types
