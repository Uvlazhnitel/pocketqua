import hashlib
import hmac
import logging
import threading
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BybitClient:
    _semaphore = threading.BoundedSemaphore(value=8)

    def __init__(self, base_url: str, api_key: str, api_secret: str, recv_window: int = 5000):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.recv_window = recv_window

        self.session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)

    def _sign(self, timestamp: str, query_string: str) -> str:
        payload = f"{timestamp}{self.api_key}{self.recv_window}{query_string}"
        return hmac.new(self.api_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        with self._semaphore:
            ts = str(int(time.time() * 1000))
            query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
            signature = self._sign(ts, query_string)

            headers = {
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-TIMESTAMP": ts,
                "X-BAPI-RECV-WINDOW": str(self.recv_window),
                "X-BAPI-SIGN": signature,
            }
            url = f"{self.base_url}{path}"
            started = time.perf_counter()
            response = self.session.get(url, params=params, headers=headers, timeout=20)
            latency_ms = int((time.perf_counter() - started) * 1000)

            request_id = response.headers.get("Traceid") or response.headers.get("X-Bapi-Limit-Status")
            logger.info(
                "bybit_request",
                extra={
                    "path": path,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "request_id": request_id,
                },
            )

            response.raise_for_status()
            data = response.json()
            if data.get("retCode") != 0:
                raise RuntimeError(f"Bybit API error: {data.get('retCode')} - {data.get('retMsg')}")
            return data

    def get_wallet_balance(self, account_type: str = "UNIFIED") -> dict[str, Any]:
        return self._get("/v5/account/wallet-balance", {"accountType": account_type})

    def get_transaction_log(self, start_ms: int, end_ms: int, limit: int = 50) -> list[dict[str, Any]]:
        cursor = None
        items: list[dict[str, Any]] = []
        while True:
            params = {"startTime": start_ms, "endTime": end_ms, "limit": limit, "cursor": cursor}
            data = self._get("/v5/account/transaction-log", params)
            result = data.get("result", {})
            page_items = result.get("list", [])
            items.extend(page_items)
            cursor = result.get("nextPageCursor")
            if not cursor or not page_items:
                break
        return items

    def get_internal_transfers(self, start_ms: int, end_ms: int, limit: int = 50) -> list[dict[str, Any]]:
        cursor = None
        items: list[dict[str, Any]] = []
        while True:
            params = {"startTime": start_ms, "endTime": end_ms, "limit": limit, "cursor": cursor}
            data = self._get("/v5/asset/transfer/query-inter-transfer-list", params)
            result = data.get("result", {})
            page_items = result.get("list", [])
            items.extend(page_items)
            cursor = result.get("nextPageCursor")
            if not cursor or not page_items:
                break
        return items
