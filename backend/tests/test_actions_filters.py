def seed_action(client) -> int:
    client.post(
        "/v1/portfolio/positions",
        json={
            "symbol": "BTC",
            "name": "Bitcoin",
            "asset_class": "crypto",
            "account": "spot",
            "amount": 1.0,
        },
    )
    client.post("/v1/portfolio/prices", json={"symbol": "BTC", "price_usd": 10000})
    client.post(
        "/v1/strategy",
        json={
            "name": "Core",
            "targets": [
                {
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "asset_class": "crypto",
                    "target_weight": 1.0,
                    "band_min": 0.5,
                    "band_max": 1.0,
                }
            ],
        },
    )
    client.post("/v1/actions/generate")
    actions = client.get("/v1/actions?status=new&limit=5").json()
    return actions[0]["id"]


def test_actions_filter_and_get_by_id(client) -> None:
    action_id = seed_action(client)

    filtered = client.get("/v1/actions?status=new&limit=1")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    one = client.get(f"/v1/actions/{action_id}")
    assert one.status_code == 200
    assert one.json()["id"] == action_id

    update = client.post(f"/v1/actions/{action_id}/status", json={"new_status": "done"})
    assert update.status_code == 200

    done = client.get("/v1/actions?status=done&limit=5")
    assert done.status_code == 200
    assert any(row["id"] == action_id for row in done.json())
