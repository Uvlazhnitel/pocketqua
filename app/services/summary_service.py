import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.summary_repository import SummaryRepository
from app.schemas.summary import SummaryAssetItem, SummaryFreshness, SummaryManualHoldingItem, SummaryResponse


class SummaryService:
    def __init__(self, db: Session):
        self.repo = SummaryRepository(db)

    def get_summary(self, user_id: uuid.UUID) -> SummaryResponse:
        wallet_rows = self.repo.latest_wallet_rows(user_id)
        manual_holdings = self.repo.manual_holdings(user_id)
        last_sync_at = self.repo.user_last_sync(user_id)

        warnings: list[str] = []
        if not wallet_rows:
            warnings.append("No wallet snapshots found")
        if any(row.usd_value is None for row in wallet_rows):
            warnings.append("Some assets have no USD valuation; totals are partial")

        total_usd = sum((row.usd_value or Decimal("0")) for row in wallet_rows)

        asset_items: list[SummaryAssetItem] = []
        for row in wallet_rows:
            usd_value = row.usd_value
            share = Decimal("0")
            if usd_value is not None and total_usd > 0:
                share = (usd_value / total_usd) * Decimal("100")
            asset_items.append(
                SummaryAssetItem(
                    symbol=row.asset_symbol,
                    amount=row.wallet_balance,
                    usd_value=usd_value,
                    share_pct=share.quantize(Decimal("0.0001")),
                )
            )

        manual_items = [
            SummaryManualHoldingItem(
                asset_type=item.asset_type,
                quantity=item.quantity,
                unit=item.unit,
                estimated_usd_value=None,
                note=item.note,
            )
            for item in manual_holdings
        ]
        if manual_items:
            warnings.append("Manual holdings are included without market valuation in Phase 1")

        lag_seconds = None
        if last_sync_at:
            lag_seconds = int((datetime.now(timezone.utc) - last_sync_at).total_seconds())
            if lag_seconds > 3600:
                warnings.append("Data is stale (last sync older than 1 hour)")

        return SummaryResponse(
            as_of=datetime.now(timezone.utc),
            total_value_usd=total_usd,
            assets=asset_items,
            manual_holdings=manual_items,
            data_freshness=SummaryFreshness(last_sync_at=last_sync_at, lag_seconds=lag_seconds),
            warnings=warnings,
        )
