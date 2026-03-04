from __future__ import annotations

from collections.abc import Iterable
import time

import httpx

# MVP symbol map. Extend incrementally as needed.
SYMBOL_TO_COINGECKO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "LINK": "chainlink",
    "LTC": "litecoin",
    "ATOM": "cosmos",
    "XAUT": "tether-gold",
    "PAXG": "pax-gold",
    "XAG": "silver",
}


def coingecko_id_for_symbol(symbol: str) -> str | None:
    return SYMBOL_TO_COINGECKO_ID.get(symbol.upper())


def _chunks(items: list[str], size: int) -> Iterable[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def fetch_prices_usd(
    *,
    base_url: str,
    coin_ids: list[str],
    timeout_sec: float,
) -> dict[str, float]:
    if not coin_ids:
        return {}

    out: dict[str, float] = {}
    for chunk in _chunks(coin_ids, 100):
        ids = ",".join(chunk)
        url = f"{base_url.rstrip('/')}/simple/price"
        params = {"ids": ids, "vs_currencies": "usd"}

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=timeout_sec) as client:
                    response = client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                for coin_id, row in data.items():
                    usd = row.get("usd") if isinstance(row, dict) else None
                    if isinstance(usd, (float, int)):
                        out[coin_id] = float(usd)
                last_error = None
                break
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(0.35)

        if last_error is not None:
            raise last_error

    return out
