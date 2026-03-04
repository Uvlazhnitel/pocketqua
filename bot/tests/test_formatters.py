from bot.formatters import (
    format_action_explain,
    format_actions,
    format_daily_digest,
    format_portfolio,
    format_staking,
    format_weekly_digest,
)


def test_format_actions_basic() -> None:
    text = format_actions([{"id": 1, "action_type": "rebalance", "title": "Rebalance BTC", "reason": "band"}])
    assert "PocketQuant Actions" in text
    assert "#1 [rebalance] Rebalance BTC" in text


def test_format_portfolio_basic() -> None:
    text = format_portfolio(
        {"total_value_usd": 1000, "assets": [{"symbol": "BTC", "value_usd": 1000, "weight": 1.0}], "warnings": []},
        {"risk_mode": "normal", "drawdown_pct": 0.01},
    )
    assert "Total: 1000.00 USD" in text


def test_format_staking_basic() -> None:
    text = format_staking([
        {
            "symbol": "ETH",
            "provider": "Lido",
            "staked_amount": 1,
            "pending_rewards_usd": 2.0,
            "unlock_at": None,
            "next_claim_at": None,
        }
    ])
    assert "Staking" in text
    assert "ETH @ Lido" in text


def test_format_explain_basic() -> None:
    text = format_action_explain(
        {
            "id": 1,
            "action_type": "dca",
            "title": "DCA",
            "reason": "due",
            "effect": "buy",
            "status": "new",
            "created_at": "2026-01-01",
            "calculation": {},
        }
    )
    assert "Action #1" in text


def test_format_digests_basic() -> None:
    daily = format_daily_digest(
        summary={"total_value_usd": 1000},
        risk={"risk_mode": "normal", "drawdown_pct": 0.0},
        actions=[],
        staking=[],
    )
    weekly = format_weekly_digest(summary={"total_value_usd": 1000}, actions_new=[], done=1, postponed=2, dismissed=3)
    assert "Daily" in daily
    assert "Weekly" in weekly
