from __future__ import annotations

import csv
import io

from sqlalchemy.orm import Session

from backend.app.db import crud
from backend.app.db.schemas import PositionUpsertIn

REQUIRED_COLUMNS = {"symbol", "name", "asset_class", "amount"}
OPTIONAL_COLUMNS = {"account", "avg_cost_usd"}


def import_positions_csv(*, db: Session, content: str, dry_run: bool) -> dict:
    reader = csv.DictReader(io.StringIO(content))
    headers = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - headers
    if missing:
        return {
            "rows_total": 0,
            "rows_imported": 0,
            "rows_skipped": 0,
            "errors": [{"row": 0, "error": f"missing columns: {', '.join(sorted(missing))}"}],
            "dry_run": dry_run,
        }

    rows_total = 0
    rows_imported = 0
    rows_skipped = 0
    errors: list[dict] = []

    for idx, row in enumerate(reader, start=2):
        rows_total += 1
        try:
            payload = PositionUpsertIn(
                symbol=(row.get("symbol") or "").strip(),
                name=(row.get("name") or "").strip(),
                asset_class=(row.get("asset_class") or "").strip(),
                account=(row.get("account") or "manual").strip() or "manual",
                amount=float(row.get("amount") or 0),
                avg_cost_usd=(float(row["avg_cost_usd"]) if row.get("avg_cost_usd") else None),
            )
        except Exception as exc:
            rows_skipped += 1
            errors.append({"row": idx, "error": str(exc)})
            continue

        if not dry_run:
            try:
                crud.upsert_position(db, payload)
            except Exception as exc:
                rows_skipped += 1
                errors.append({"row": idx, "error": str(exc)})
                continue

        rows_imported += 1

    return {
        "rows_total": rows_total,
        "rows_imported": rows_imported,
        "rows_skipped": rows_skipped,
        "errors": errors,
        "dry_run": dry_run,
    }
