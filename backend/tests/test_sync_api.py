def test_sync_api_and_status(client, monkeypatch) -> None:
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

    def fake_fetch_prices_usd(*, base_url, coin_ids, timeout_sec):
        del base_url, timeout_sec
        return {coin_id: 12345.0 for coin_id in coin_ids}

    monkeypatch.setattr("backend.app.services.price_sync.fetch_prices_usd", fake_fetch_prices_usd)

    sync = client.post("/v1/prices/sync")
    assert sync.status_code == 200
    payload = sync.json()
    assert payload["status"] in {"ok", "partial", "failed"}

    status = client.get("/v1/prices/sync/status")
    assert status.status_code == 200
    data = status.json()
    assert "latest_run" in data
