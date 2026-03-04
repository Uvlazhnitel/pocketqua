import asyncio
from types import SimpleNamespace

from bot.scheduler import build_scheduler, next_run_info


async def _run() -> None:
    app = SimpleNamespace(bot_data={})
    scheduler = build_scheduler(
        application=app,
        bot_timezone="UTC",
        daily_digest_hour=9,
        weekly_digest_weekday="MON",
    )
    scheduler.start(paused=True)
    info = next_run_info(scheduler)
    assert info["daily"] is not None
    assert info["weekly"] is not None
    scheduler.shutdown(wait=False)


def test_scheduler_next_runs() -> None:
    asyncio.run(_run())
