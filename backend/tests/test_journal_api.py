def test_action_status_writes_journal(client) -> None:
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
                        "band_min": 0.4,
                        "band_max": 1.0,
                    }
                ],
            },
        )

    gen = client.post("/v1/actions/generate")
    assert gen.status_code == 200

    actions = client.get("/v1/actions").json()
    action_id = actions[0]["id"]

    upd = client.post(f"/v1/actions/{action_id}/status", json={"new_status": "done", "note": "executed"})
    assert upd.status_code == 200
    assert upd.json()["status"] == "done"

    journal = client.get("/v1/journal")
    assert journal.status_code == 200
    rows = journal.json()
    assert len(rows) == 1
    assert rows[0]["recommendation_id"] == action_id
    assert rows[0]["new_status"] == "done"
