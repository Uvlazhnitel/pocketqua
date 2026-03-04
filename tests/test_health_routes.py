from fastapi.testclient import TestClient

from app.main import app


class DummyResult:
    pass


class DummyDB:
    def execute(self, _):
        return DummyResult()


def override_db():
    yield DummyDB()


def test_health_live():
    client = TestClient(app)
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "db": None}
