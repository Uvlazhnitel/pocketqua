import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.manual_holdings_repository import ManualHoldingsRepository
from app.repositories.pnl_repository import PnLRepository
from app.schemas.holdings import CryptoHoldingItem, HoldingsResponse, ManualHoldingValuedItem
from app.services.market_data_service import MarketDataService

OZ_IN_GRAM = Decimal("31.1034768")


class HoldingsService:
    def __init__(self, db: Session):
        self.pnl_repo = PnLRepository(db)
        self.manual_repo = ManualHoldingsRepository(db)
        self.market_data = MarketDataService()

    def get_holdings(self, user_id: uuid.UUID) -> HoldingsResponse:
        warnings: list[str] = []
        wallet_rows = self.pnl_repo.latest_wallet_rows(user_id)

        crypto_items: list[CryptoHoldingItem] = []
        total_crypto = Decimal("0")

        for row in wallet_rows:
            price = None
            if row.usd_value is not None and row.wallet_balance != 0:
                price = row.usd_value / row.wallet_balance

            usd_value = row.usd_value
            if usd_value is not None:
                total_crypto += usd_value
            else:
                warnings.append(f"Missing USD valuation for crypto asset {row.asset_symbol}")

            crypto_items.append(
                CryptoHoldingItem(
                    symbol=row.asset_symbol,
                    amount=row.wallet_balance,
                    price_usd=price,
                    usd_value=usd_value,
                )
            )

        manual_holdings = self.manual_repo.active_for_user(user_id)
        metal_prices, metal_warnings = self.market_data.get_metal_spot_prices_usd()
        warnings.extend(metal_warnings)

        manual_items: list[ManualHoldingValuedItem] = []
        total_manual = Decimal("0")

        for item in manual_holdings:
            spot_oz = metal_prices.get(item.asset_type.lower())
            qty_oz = item.quantity if item.unit.lower() == "oz" else (item.quantity / OZ_IN_GRAM)
            value = qty_oz * spot_oz if spot_oz is not None else None

            if value is not None:
                total_manual += value
            else:
                warnings.append(f"Missing market valuation for manual holding {item.asset_type}")

            manual_items.append(
                ManualHoldingValuedItem(
                    asset_type=item.asset_type,
                    quantity=item.quantity,
                    unit=item.unit,
                    spot_price_usd_per_oz=spot_oz,
                    estimated_usd_value=value,
                    valuation_source="metals.live" if spot_oz is not None else None,
                    note=item.note,
                )
            )

        total = total_crypto + total_manual

        return HoldingsResponse(
            as_of=datetime.now(timezone.utc),
            total_crypto_usd=total_crypto,
            total_manual_usd=total_manual,
            total_portfolio_usd=total,
            crypto=crypto_items,
            manual_holdings=manual_items,
            warnings=warnings,
        )
