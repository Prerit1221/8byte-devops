import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Use SQLite for testing (no PostgreSQL needed in CI)
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ── Unit Tests ──────────────────────────────────────────────

class TestHealthEndpoints:
    def test_root(self):
        res = client.get("/")
        assert res.status_code == 200
        assert "running" in res.json()["message"]

    def test_health(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

    def test_health_db(self):
        res = client.get("/health/db")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

    def test_metrics_exposed(self):
        res = client.get("/metrics")
        assert res.status_code == 200


# ── Integration Tests ────────────────────────────────────────

class TestItemsCRUD:
    def test_create_item(self):
        res = client.post("/items/", json={"title": "Test Item", "description": "A test"})
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Test Item"
        assert data["id"] is not None

    def test_get_items_empty(self):
        res = client.get("/items/")
        assert res.status_code == 200
        assert res.json() == []

    def test_get_items(self):
        client.post("/items/", json={"title": "Item 1"})
        client.post("/items/", json={"title": "Item 2"})
        res = client.get("/items/")
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_get_single_item(self):
        created = client.post("/items/", json={"title": "Single"}).json()
        res = client.get(f"/items/{created['id']}")
        assert res.status_code == 200
        assert res.json()["title"] == "Single"

    def test_get_item_not_found(self):
        res = client.get("/items/9999")
        assert res.status_code == 404

    def test_update_item(self):
        created = client.post("/items/", json={"title": "Old Title"}).json()
        res = client.put(f"/items/{created['id']}", json={"title": "New Title"})
        assert res.status_code == 200
        assert res.json()["title"] == "New Title"

    def test_update_item_not_found(self):
        res = client.put("/items/9999", json={"title": "X"})
        assert res.status_code == 404

    def test_delete_item(self):
        created = client.post("/items/", json={"title": "To Delete"}).json()
        res = client.delete(f"/items/{created['id']}")
        assert res.status_code == 204

    def test_delete_item_not_found(self):
        res = client.delete("/items/9999")
        assert res.status_code == 404

    def test_item_is_active_default(self):
        res = client.post("/items/", json={"title": "Active Item"})
        assert res.json()["is_active"] is True
