from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from backend.app.api.actions import router as actions_router
from backend.app.api.imports import router as imports_router
from backend.app.api.journal import router as journal_router
from backend.app.api.portfolio import router as portfolio_router
from backend.app.api.prices import router as prices_router
from backend.app.api.risk import router as risk_router
from backend.app.api.staking import router as staking_router
from backend.app.api.strategy import router as strategy_router
from backend.app.api.telegram import router as telegram_router
from backend.app.core.logging import configure_logging
from backend.app.core.settings import settings
from backend.app.db.base import Base, SessionLocal, engine
from backend.app.services.price_sync import run_price_sync


def _run_sync_job() -> None:
    db = SessionLocal()
    try:
        run_price_sync(db)
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    Base.metadata.create_all(bind=engine)
    scheduler = None
    if settings.price_sync_enabled:
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            _run_sync_job,
            "interval",
            hours=max(1, settings.price_sync_interval_hours),
            id="prices_sync_job",
            replace_existing=True,
        )
        scheduler.start()
        app.state.price_sync_scheduler = scheduler
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(title="pocketquant API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(portfolio_router)
app.include_router(strategy_router)
app.include_router(staking_router)
app.include_router(actions_router)
app.include_router(risk_router)
app.include_router(journal_router)
app.include_router(telegram_router)
app.include_router(imports_router)
app.include_router(prices_router)
