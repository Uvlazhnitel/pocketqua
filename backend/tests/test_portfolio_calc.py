from backend.app.db import crud
from backend.app.db.base import SessionLocal
from backend.app.db.schemas import PositionUpsertIn, PriceUpsertIn
from backend.app.services.portfolio_calc import build_portfolio_snapshot


def test_portfolio_snapshot_value_and_weights() -> None:
    db = SessionLocal()
    try:
        crud.upsert_position(
            db,
            PositionUpsertIn(
                symbol="BTC",
                name="Bitcoin",
                asset_class="crypto",
                account="spot",
                amount=1.0,
            ),
        )
        crud.upsert_position(
            db,
            PositionUpsertIn(
                symbol="ETH",
                name="Ethereum",
                asset_class="crypto",
                account="spot",
                amount=10.0,
            ),
        )
        crud.upsert_price(db, PriceUpsertIn(symbol="BTC", price_usd=20000.0))
        crud.upsert_price(db, PriceUpsertIn(symbol="ETH", price_usd=2000.0))
        db.commit()

        snapshot = build_portfolio_snapshot(db)
        assert snapshot["total_value_usd"] == 40000.0

        weights = {a["symbol"]: a["weight"] for a in snapshot["assets"]}
        assert weights["BTC"] == 0.5
        assert weights["ETH"] == 0.5
        assert snapshot["warnings"] == []
    finally:
        db.close()
