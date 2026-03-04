from backend.app.db import crud
from backend.app.db.base import SessionLocal


def test_manual_price_overrides_auto_in_summary(client) -> None:
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

    db = SessionLocal()
    try:
        crud.upsert_price_from_coingecko(db, symbol="BTC", price_usd=5000)
        db.commit()
    finally:
        db.close()

    client.post("/v1/portfolio/prices", json={"symbol": "BTC", "price_usd": 10000})

    summary = client.get("/v1/portfolio/summary")
    assert summary.status_code == 200
    assert summary.json()["total_value_usd"] == 10000.0
