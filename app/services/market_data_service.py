import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)


class MarketDataService:
    METALS_SPOT_URL = "https://api.metals.live/v1/spot"

    def get_metal_spot_prices_usd(self) -> tuple[dict[str, Decimal], list[str]]:
        warnings: list[str] = []
        prices: dict[str, Decimal] = {}

        try:
            response = requests.get(self.METALS_SPOT_URL, timeout=8)
            response.raise_for_status()
            data = response.json()

            # Expected shape: [{"gold": 2912.1}, {"silver": 32.5}, ...]
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if "gold" in item:
                            prices["gold"] = Decimal(str(item["gold"]))
                        if "silver" in item:
                            prices["silver"] = Decimal(str(item["silver"]))

            if "gold" not in prices or "silver" not in prices:
                warnings.append("Metal prices unavailable or partial from metals.live")
        except Exception as exc:  # noqa: BLE001
            logger.warning("metal_price_fetch_failed", extra={"error": str(exc)})
            warnings.append("Failed to fetch metal spot prices")

        return prices, warnings
