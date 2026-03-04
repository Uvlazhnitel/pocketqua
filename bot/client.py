from __future__ import annotations

from typing import Any

import httpx


class BackendClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(f"{self._base_url}{path}", params=params)
            response.raise_for_status()
            return response.json()

    async def _post(self, path: str, payload: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()

    async def _patch(self, path: str, payload: dict[str, Any]) -> Any:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.patch(f"{self._base_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()

    async def portfolio_summary(self) -> dict[str, Any]:
        return await self._get("/v1/portfolio/summary")

    async def risk_summary(self) -> dict[str, Any]:
        return await self._get("/v1/risk/summary")

    async def actions(self, *, status: str = "new", limit: int = 5) -> list[dict[str, Any]]:
        return await self._get("/v1/actions", params={"status": status, "limit": limit})

    async def action_by_id(self, action_id: int) -> dict[str, Any]:
        return await self._get(f"/v1/actions/{action_id}")

    async def staking_positions(self, *, limit: int = 5) -> list[dict[str, Any]]:
        return await self._get("/v1/staking/positions", params={"limit": limit})

    async def register_chat(
        self,
        *,
        chat_id: int,
        timezone: str,
        daily_enabled: bool = True,
        weekly_enabled: bool = True,
    ) -> dict[str, Any]:
        return await self._post(
            "/v1/telegram/chats/register",
            {
                "chat_id": chat_id,
                "timezone": timezone,
                "daily_enabled": daily_enabled,
                "weekly_enabled": weekly_enabled,
            },
        )

    async def list_chats(self) -> list[dict[str, Any]]:
        return await self._get("/v1/telegram/chats")

    async def patch_chat(self, chat_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._patch(f"/v1/telegram/chats/{chat_id}", payload)

    async def mark_daily_sent(self, chat_id: int) -> dict[str, Any]:
        return await self._post(f"/v1/telegram/chats/{chat_id}/mark-daily", {})

    async def mark_weekly_sent(self, chat_id: int) -> dict[str, Any]:
        return await self._post(f"/v1/telegram/chats/{chat_id}/mark-weekly", {})
