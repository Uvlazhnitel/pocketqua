from datetime import datetime, timedelta, timezone


def test_staking_position_crud(client) -> None:
    create = client.post(
        "/v1/staking/positions",
        json={
            "symbol": "ETH",
            "name": "Ethereum",
            "asset_class": "crypto",
            "provider": "Lido",
            "account": "manual",
            "staked_amount": 12.0,
            "apr_percent": 4.5,
            "fee_percent": 10.0,
            "lockup_days": 0,
            "unbonding_days": 0,
            "is_locked": False,
            "pending_rewards_asset": 0.1,
            "pending_rewards_eur": 25.0,
            "next_claim_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        },
    )
    assert create.status_code == 200
    row = create.json()
    row_id = row["id"]

    listed = client.get("/v1/staking/positions")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    patch = client.patch(
        f"/v1/staking/positions/{row_id}",
        json={"pending_rewards_eur": 30.0},
    )
    assert patch.status_code == 200
    assert patch.json()["pending_rewards_eur"] == 30.0

    delete = client.delete(f"/v1/staking/positions/{row_id}")
    assert delete.status_code == 200
    assert delete.json()["deleted"] is True


def test_staking_actions_generated_without_targets(client) -> None:
    strategy_resp = client.post(
        "/v1/strategy",
        json={
            "name": "StakingOnly",
            "base_currency": "EUR",
            "dca_enabled": False,
            "dca_interval_days": 7,
            "staking_unlock_window_days": 3,
            "staking_min_net_reward_eur": 10.0,
            "staking_restake_enabled": True,
            "targets": [],
        },
    )
    assert strategy_resp.status_code == 200

    client.post(
        "/v1/staking/positions",
        json={
            "symbol": "ETH",
            "name": "Ethereum",
            "asset_class": "crypto",
            "provider": "Lido",
            "account": "manual",
            "staked_amount": 12.0,
            "apr_percent": 4.5,
            "fee_percent": 10.0,
            "is_locked": True,
            "unlock_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "next_claim_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "pending_rewards_asset": 0.1,
            "pending_rewards_eur": 20.0,
        },
    )

    generate = client.post("/v1/actions/generate")
    assert generate.status_code == 200
    assert generate.json()["generated"] >= 1

    actions = client.get("/v1/actions")
    assert actions.status_code == 200
    types = [a["action_type"] for a in actions.json()]
    assert "staking_unlock_plan" in types
    assert "staking_restake" in types


def test_generate_returns_422_without_targets_and_without_staking_actions(client) -> None:
    strategy_resp = client.post(
        "/v1/strategy",
        json={
            "name": "Empty",
            "base_currency": "EUR",
            "dca_enabled": False,
            "dca_interval_days": 7,
            "targets": [],
        },
    )
    assert strategy_resp.status_code == 200

    generate = client.post("/v1/actions/generate")
    assert generate.status_code == 422
