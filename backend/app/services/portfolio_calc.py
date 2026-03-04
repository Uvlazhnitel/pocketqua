from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db import crud, models


def build_portfolio_snapshot(db: Session) -> dict:
    positions = list(db.scalars(select(models.Position)))
    prices = crud.get_effective_prices_by_asset_id(db)
    assets = {a.id: a for a in db.scalars(select(models.Asset))}

    by_symbol: dict[str, dict] = {}
    warnings: list[str] = []

    for pos in positions:
        asset = assets.get(pos.asset_id)
        if not asset:
            continue

        if asset.symbol not in by_symbol:
            by_symbol[asset.symbol] = {
                "symbol": asset.symbol,
                "asset_id": asset.id,
                "amount": 0.0,
                "value_usd": 0.0,
            }
        by_symbol[asset.symbol]["amount"] += pos.amount

    for symbol, row in by_symbol.items():
        price = prices.get(row["asset_id"])
        if not price:
            warnings.append(f"Missing USD price for {symbol}; excluded from valuation")
            continue
        row["value_usd"] = row["amount"] * price.price_usd

    total = sum(row["value_usd"] for row in by_symbol.values())

    assets_out: list[dict] = []
    for row in sorted(by_symbol.values(), key=lambda x: x["symbol"]):
        value = row["value_usd"]
        weight = (value / total) if total > 0 else 0.0
        assets_out.append({"symbol": row["symbol"], "value_usd": value, "weight": weight})

    return {"total_value_usd": total, "assets": assets_out, "warnings": warnings}


def snapshot_weights(snapshot: dict) -> dict[str, float]:
    return {item["symbol"]: item["weight"] for item in snapshot["assets"]}
