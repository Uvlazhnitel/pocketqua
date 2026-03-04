from __future__ import annotations

import asyncio

from telegram.ext import Application, CommandHandler

from backend.app.core.settings import settings
from bot.client import BackendClient
from bot.handlers import cmd_actions, cmd_explain, cmd_portfolio, cmd_staking
from bot.scheduler import build_scheduler


async def run_bot() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set. Add it to your .env file.")

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["backend_client"] = BackendClient(settings.backend_base_url)
    app.bot_data["bot_timezone"] = settings.bot_timezone

    app.add_handler(CommandHandler("portfolio", cmd_portfolio))
    app.add_handler(CommandHandler("actions", cmd_actions))
    app.add_handler(CommandHandler("staking", cmd_staking))
    app.add_handler(CommandHandler("explain", cmd_explain))

    scheduler = build_scheduler(
        application=app,
        bot_timezone=settings.bot_timezone,
        daily_digest_hour=settings.daily_digest_hour,
        weekly_digest_weekday=settings.weekly_digest_weekday,
    )

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    scheduler.start()

    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown(wait=False)
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(run_bot())
