from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.actions import router as actions_router
from backend.app.api.portfolio import router as portfolio_router
from backend.app.api.strategy import router as strategy_router
from backend.app.core.logging import configure_logging
from backend.app.core.settings import settings
from backend.app.db.base import Base, engine

@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings.log_level)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="pocketquant API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(portfolio_router)
app.include_router(strategy_router)
app.include_router(actions_router)
