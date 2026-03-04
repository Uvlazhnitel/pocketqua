import io


def test_import_positions_csv_dry_run(client) -> None:
    csv_data = "symbol,name,asset_class,account,amount,avg_cost_usd\nBTC,Bitcoin,crypto,spot,1,30000\n"
    files = {"file": ("positions.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    data = {"dry_run": "true"}

    response = client.post("/v1/import/positions", files=files, data=data)
    assert response.status_code == 200
    payload = response.json()
    assert payload["rows_total"] == 1
    assert payload["rows_imported"] == 1
    assert payload["dry_run"] is True

    summary = client.get("/v1/portfolio/summary")
    assert summary.status_code == 200
    assert summary.json()["total_value_usd"] == 0.0


def test_import_positions_csv_persist(client) -> None:
    csv_data = "symbol,name,asset_class,account,amount,avg_cost_usd\nBTC,Bitcoin,crypto,spot,2,25000\n"
    files = {"file": ("positions.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}

    response = client.post("/v1/import/positions", files=files)
    assert response.status_code == 200
    payload = response.json()
    assert payload["rows_imported"] == 1

    # add price and verify position valuation exists
    client.post("/v1/portfolio/prices", json={"symbol": "BTC", "price_usd": 10000})
    summary = client.get("/v1/portfolio/summary").json()
    assert summary["total_value_usd"] == 20000.0
