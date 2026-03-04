import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.holdings import router as holdings_router
from app.api.routes.pnl import router as pnl_router
from app.api.routes.summary import router as summary_router
from app.api.routes.sync import _run_sync_task, router as sync_router
from app.config import get_settings
from app.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="PocketQuant API", version="0.1.0")
app.include_router(health_router)
app.include_router(sync_router)
app.include_router(summary_router)
app.include_router(pnl_router)
app.include_router(holdings_router)

scheduler = BackgroundScheduler(timezone="UTC")


@app.on_event("startup")
def startup_event() -> None:
    scheduler.add_job(_run_sync_task, "interval", seconds=settings.sync_interval_seconds, id="bybit_sync", replace_existing=True)
    scheduler.start()
    logger.info("scheduler_started", extra={"sync_interval_seconds": settings.sync_interval_seconds})


@app.on_event("shutdown")
def shutdown_event() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
