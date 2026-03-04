def test_risk_summary_endpoint(client) -> None:
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
            "name": "Risk",
            "max_asset_weight": 0.5,
            "max_provider_weight": 0.5,
            "targets": [],
        },
    )

    risk = client.get("/v1/risk/summary")
    assert risk.status_code == 200
    payload = risk.json()
    assert payload["current_total_value_usd"] == 10000.0
    assert payload["risk_mode"] in {"normal", "caution", "defense"}
    assert len(payload["asset_concentration_breaches"]) == 1
