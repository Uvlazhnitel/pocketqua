from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application

from bot.client import BackendClient
from bot.formatters import format_daily_digest, format_weekly_digest

WEEKDAY_MAP = {
    "MON": "mon",
    "TUE": "tue",
    "WED": "wed",
    "THU": "thu",
    "FRI": "fri",
    "SAT": "sat",
    "SUN": "sun",
}


async def send_daily_digest(app: Application) -> None:
    client: BackendClient = app.bot_data["backend_client"]
    tz = ZoneInfo(app.bot_data.get("bot_timezone", "UTC"))
    now_local = datetime.now(tz)
    try:
        chats = await client.list_chats()
    except httpx.HTTPError:
        return

    for chat in chats:
        if not chat.get("daily_enabled", True):
            continue
        last_daily = chat.get("last_daily_sent_at")
        if last_daily:
            sent_at = datetime.fromisoformat(last_daily)
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=tz)
            if sent_at.astimezone(tz).date() == now_local.date():
                continue
        try:
            summary = await client.portfolio_summary()
            risk = await client.risk_summary()
            actions = await client.actions(status="new", limit=3)
            staking = await client.staking_positions(limit=3)
            text = format_daily_digest(summary=summary, risk=risk, actions=actions, staking=staking)
            await app.bot.send_message(chat_id=chat["chat_id"], text=text)
            await client.mark_daily_sent(chat["chat_id"])
        except httpx.HTTPError:
            continue


async def send_weekly_digest(app: Application) -> None:
    client: BackendClient = app.bot_data["backend_client"]
    tz = ZoneInfo(app.bot_data.get("bot_timezone", "UTC"))
    now_local = datetime.now(tz)
    try:
        chats = await client.list_chats()
    except httpx.HTTPError:
        return

    for chat in chats:
        if not chat.get("weekly_enabled", True):
            continue
        last_weekly = chat.get("last_weekly_sent_at")
        if last_weekly:
            sent_at = datetime.fromisoformat(last_weekly)
            if sent_at.tzinfo is None:
                sent_at = sent_at.replace(tzinfo=tz)
            sent_week = sent_at.astimezone(tz).isocalendar()[:2]
            now_week = now_local.isocalendar()[:2]
            if sent_week == now_week:
                continue
        try:
            summary = await client.portfolio_summary()
            actions_new = await client.actions(status="new", limit=3)
            done = len(await client.actions(status="done", limit=100))
            postponed = len(await client.actions(status="postponed", limit=100))
            dismissed = len(await client.actions(status="dismissed", limit=100))
            text = format_weekly_digest(
                summary=summary,
                actions_new=actions_new,
                done=done,
                postponed=postponed,
                dismissed=dismissed,
            )
            await app.bot.send_message(chat_id=chat["chat_id"], text=text)
            await client.mark_weekly_sent(chat["chat_id"])
        except httpx.HTTPError:
            continue


def build_scheduler(
    *,
    application: Application,
    bot_timezone: str,
    daily_digest_hour: int,
    weekly_digest_weekday: str,
) -> AsyncIOScheduler:
    tz = ZoneInfo(bot_timezone)
    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(send_daily_digest, "cron", hour=daily_digest_hour, args=[application], id="daily_digest")
    scheduler.add_job(
        send_weekly_digest,
        "cron",
        day_of_week=WEEKDAY_MAP.get(weekly_digest_weekday.upper(), "mon"),
        hour=daily_digest_hour,
        args=[application],
        id="weekly_digest",
    )
    return scheduler


def next_run_info(scheduler: AsyncIOScheduler) -> dict[str, datetime | None]:
    daily = scheduler.get_job("daily_digest")
    weekly = scheduler.get_job("weekly_digest")
    return {
        "daily": daily.next_run_time if daily else None,
        "weekly": weekly.next_run_time if weekly else None,
    }
