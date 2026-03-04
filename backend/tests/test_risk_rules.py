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


def _strategy(**kwargs) -> models.Strategy:
    defaults = {
        "id": 1,
        "name": "risk",
        "base_currency": "USD",
        "is_active": True,
        "dca_enabled": True,
        "dca_interval_days": 1,
        "staking_unlock_window_days": 3,
        "staking_min_net_reward_usd": 10.0,
        "staking_restake_enabled": True,
        "max_asset_weight": 0.55,
        "max_provider_weight": 0.50,
        "drawdown_caution_pct": 0.10,
        "drawdown_defense_pct": 0.20,
        "min_trade_value_usd": 5000.0,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return models.Strategy(**defaults)


def test_fee_guard_suppresses_small_rebalance() -> None:
    strategy = _strategy(min_trade_value_usd=1000)
    targets = [_target("BTC", 0.51, 0.45, 0.55)]

    actions = run_rules(
        strategy=strategy,
        targets=targets,
        weights={"BTC": 0.56},
        staking_positions=[],
        total_value_usd=1000,
        price_by_symbol={},
        risk_mode=models.RiskMode.NORMAL,
        previous_risk_mode=models.RiskMode.NORMAL,
    )
    types = {a.action_type for a in actions}
    assert models.ActionType.REBALANCE not in types
    assert models.ActionType.RISK_FEE_WARNING in types


def test_defense_blocks_risk_on_actions() -> None:
    strategy = _strategy()
    targets = [_target("BTC", 0.6, 0.55, 0.65)]

    actions = run_rules(
        strategy=strategy,
        targets=targets,
        weights={"BTC": 0.5},
        staking_positions=[],
        total_value_usd=10000,
        price_by_symbol={},
        risk_mode=models.RiskMode.DEFENSE,
        previous_risk_mode=models.RiskMode.DEFENSE,
    )

    types = {a.action_type for a in actions}
    assert models.ActionType.DCA not in types


def test_asset_concentration_action() -> None:
    strategy = _strategy(max_asset_weight=0.4)
    actions = run_rules(
        strategy=strategy,
        targets=[],
        weights={"BTC": 0.7},
        staking_positions=[],
        total_value_usd=10000,
        price_by_symbol={},
        risk_mode=models.RiskMode.NORMAL,
        previous_risk_mode=models.RiskMode.NORMAL,
    )
    types = {a.action_type for a in actions}
    assert models.ActionType.RISK_ASSET_CONCENTRATION in types
