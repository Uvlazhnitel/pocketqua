import pytest
from fastapi.testclient import TestClient

from backend.app.db.base import Base, engine
from backend.app.main import app


@pytest.fixture(autouse=True)
def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
