from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.core.settings import settings
from backend.app.db import crud, models
from backend.app.services.coingecko_client import coingecko_id_for_symbol, fetch_prices_usd


def run_price_sync(db: Session) -> dict:
    run = crud.create_price_sync_run(db)

    assets = crud.list_assets(db)
    id_to_symbols: dict[str, list[str]] = {}
    skipped = 0
    errors: list[str] = []

    for asset in assets:
        coin_id = coingecko_id_for_symbol(asset.symbol)
        if coin_id is None:
            skipped += 1
            errors.append(f"unmapped symbol: {asset.symbol}")
            continue
        id_to_symbols.setdefault(coin_id, []).append(asset.symbol)

    updated_assets_count = 0
    error_count = 0

    try:
        prices = fetch_prices_usd(
            base_url=settings.coingecko_base_url,
            coin_ids=list(id_to_symbols.keys()),
            timeout_sec=settings.coingecko_timeout_sec,
        )

        for coin_id, symbols in id_to_symbols.items():
            price = prices.get(coin_id)
            if price is None:
                error_count += len(symbols)
                errors.append(f"missing price for coin id: {coin_id}")
                continue
            for symbol in symbols:
                crud.upsert_price_from_coingecko(db, symbol=symbol, price_usd=price)
                updated_assets_count += 1

        status = models.PriceSyncRunStatus.OK
        if error_count > 0 or skipped > 0:
            status = models.PriceSyncRunStatus.PARTIAL

        crud.finish_price_sync_run(
            db,
            run_id=run.id,
            status=status,
            updated_assets_count=updated_assets_count,
            error_count=error_count,
            error_summary=("; ".join(errors[:10]) if errors else None),
        )
        db.flush()
        return {
            "run_id": run.id,
            "status": status.value,
            "updated_assets_count": updated_assets_count,
            "skipped_assets_count": skipped,
            "errors_count": error_count,
        }
    except Exception as exc:
        crud.finish_price_sync_run(
            db,
            run_id=run.id,
            status=models.PriceSyncRunStatus.FAILED,
            updated_assets_count=updated_assets_count,
            error_count=error_count + 1,
            error_summary=str(exc),
        )
        db.flush()
        return {
            "run_id": run.id,
            "status": models.PriceSyncRunStatus.FAILED.value,
            "updated_assets_count": updated_assets_count,
            "skipped_assets_count": skipped,
            "errors_count": error_count + 1,
        }
