def test_portfolio_summary_api(client) -> None:
    response = client.post(
        "/v1/portfolio/positions",
        json={
            "symbol": "BTC",
            "name": "Bitcoin",
            "asset_class": "crypto",
            "account": "spot",
            "amount": 1.0,
            "avg_cost_usd": 15000.0,
        },
    )
    assert response.status_code == 200

    response = client.post(
        "/v1/portfolio/positions",
        json={
            "symbol": "ETH",
            "name": "Ethereum",
            "asset_class": "crypto",
            "account": "spot",
            "amount": 2.0,
        },
    )
    assert response.status_code == 200

    assert client.post("/v1/portfolio/prices", json={"symbol": "BTC", "price_usd": 20000}).status_code == 200
    assert client.post("/v1/portfolio/prices", json={"symbol": "ETH", "price_usd": 1000}).status_code == 200

    summary = client.get("/v1/portfolio/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["total_value_usd"] == 22000.0

    weights = {row["symbol"]: row["weight"] for row in payload["assets"]}
    assert round(weights["BTC"], 6) == round(20000 / 22000, 6)
    assert round(weights["ETH"], 6) == round(2000 / 22000, 6)


def test_generate_actions_and_list(client) -> None:
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
    client.post(
        "/v1/portfolio/positions",
        json={
            "symbol": "ETH",
            "name": "Ethereum",
            "asset_class": "crypto",
            "account": "spot",
            "amount": 1.0,
        },
    )
    client.post("/v1/portfolio/prices", json={"symbol": "BTC", "price_usd": 20000})
    client.post("/v1/portfolio/prices", json={"symbol": "ETH", "price_usd": 20000})

    strategy_resp = client.post(
        "/v1/strategy",
        json={
            "name": "Core",
            "base_currency": "USD",
            "dca_enabled": False,
            "dca_interval_days": 7,
            "targets": [
                {
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "asset_class": "crypto",
                    "target_weight": 0.8,
                    "band_min": 0.75,
                    "band_max": 0.85,
                },
                {
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "asset_class": "crypto",
                    "target_weight": 0.2,
                    "band_min": 0.15,
                    "band_max": 0.25,
                },
            ],
        },
    )
    assert strategy_resp.status_code == 200

    generate_resp = client.post("/v1/actions/generate")
    assert generate_resp.status_code == 200
    assert generate_resp.json()["generated"] >= 1

    actions_resp = client.get("/v1/actions")
    assert actions_resp.status_code == 200
    actions = actions_resp.json()
    assert len(actions) >= 1

    first = actions[0]
    assert "action_type" in first
    assert "title" in first
    assert "reason" in first
    assert "effect" in first
    assert "calculation" in first
