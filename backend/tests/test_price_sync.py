from backend.app.db import crud
from backend.app.db.base import SessionLocal
from backend.app.db.schemas import PositionUpsertIn
from backend.app.services.price_sync import run_price_sync


def test_price_sync_partial_for_unmapped(monkeypatch) -> None:
    def fake_fetch_prices_usd(*, base_url, coin_ids, timeout_sec):
        del base_url, timeout_sec
        return {coin_id: 100.0 for coin_id in coin_ids}

    monkeypatch.setattr("backend.app.services.price_sync.fetch_prices_usd", fake_fetch_prices_usd)

    db = SessionLocal()
    try:
        crud.upsert_position(
            db,
            PositionUpsertIn(
                symbol="BTC",
                name="Bitcoin",
                asset_class="crypto",
                amount=1,
                account="spot",
            ),
        )
        crud.upsert_position(
            db,
            PositionUpsertIn(
                symbol="ZZZ",
                name="Unknown",
                asset_class="crypto",
                amount=1,
                account="spot",
            ),
        )
        db.commit()

        result = run_price_sync(db)
        db.commit()

        assert result["updated_assets_count"] == 1
        assert result["skipped_assets_count"] == 1
        assert result["status"] == "partial"
    finally:
        db.close()
