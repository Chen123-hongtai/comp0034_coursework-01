from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from backend.database import get_session
from backend.main import app
from backend.models import Observation, SeriesMaster


@pytest.fixture
def client(tmp_path: Path):
    db_path = tmp_path / "test_api.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            SeriesMaster(
                series_id=1,
                level=0,
                name="International Visitor Arrivals By Inbound Tourism Markets, (Sea)",
                parent_id=None,
                full_path="International Visitor Arrivals By Inbound Tourism Markets, (Sea)",
            )
        )
        session.add(
            SeriesMaster(
                series_id=2,
                level=1,
                name="Southeast Asia",
                parent_id=1.0,
                full_path="International Visitor Arrivals By Inbound Tourism Markets, (Sea) > Southeast Asia",
            )
        )
        session.add(
            SeriesMaster(
                series_id=3,
                level=2,
                name="Indonesia",
                parent_id=2.0,
                full_path="International Visitor Arrivals By Inbound Tourism Markets, (Sea) > Southeast Asia > Indonesia",
            )
        )

        # region totals for dashboard/yoy/recovery
        session.add(Observation(series_id=2, month="2019Jan", date=datetime(2019, 1, 1), value=100.0))
        session.add(Observation(series_id=2, month="2024Jan", date=datetime(2024, 1, 1), value=120.0))
        session.add(Observation(series_id=2, month="2024Feb", date=datetime(2024, 2, 1), value=130.0))
        session.add(Observation(series_id=2, month="2025Jan", date=datetime(2025, 1, 1), value=150.0))
        session.add(Observation(series_id=2, month="2025Feb", date=datetime(2025, 2, 1), value=160.0))

        # market totals for explorer
        session.add(Observation(series_id=3, month="2024Jan", date=datetime(2024, 1, 1), value=60.0))
        session.add(Observation(series_id=3, month="2024Feb", date=datetime(2024, 2, 1), value=80.0))
        session.add(Observation(series_id=3, month="2025Jan", date=datetime(2025, 1, 1), value=90.0))
        session.add(Observation(series_id=3, month="2025Feb", date=datetime(2025, 2, 1), value=100.0))

        # root series for scenario history
        session.add(Observation(series_id=1, month="2025Jan", date=datetime(2025, 1, 1), value=200.0))
        session.add(Observation(series_id=1, month="2025Feb", date=datetime(2025, 2, 1), value=220.0))
        session.commit()

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_series(client: TestClient):
    response = client.get("/api/v1/series")
    assert response.status_code == 200
    assert len(response.json()) >= 3


def test_get_series_by_id(client: TestClient):
    response = client.get("/api/v1/series/2")
    assert response.status_code == 200
    assert response.json()["name"] == "Southeast Asia"


def test_regions_and_markets(client: TestClient):
    regions = client.get("/api/v1/regions")
    markets = client.get("/api/v1/markets", params={"region": "Southeast Asia"})
    assert regions.status_code == 200
    assert markets.status_code == 200
    assert "Southeast Asia" in regions.json()
    assert "Indonesia" in markets.json()


def test_list_observations(client: TestClient):
    response = client.get("/api/v1/observations", params={"series_id": 2, "limit": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_dashboard_summary(client: TestClient):
    response = client.get("/api/v1/dashboard/summary", params={"region": "Southeast Asia"})
    assert response.status_code == 200
    body = response.json()
    assert body["region"] == "Southeast Asia"
    assert body["total_visitors"] > 0
    assert "monthly_points" in body


def test_market_explorer(client: TestClient):
    response = client.get("/api/v1/market-explorer")
    assert response.status_code == 200
    assert response.json()[0]["market"] == "Indonesia"


def test_scenario_routes(client: TestClient):
    markets = client.get("/api/v1/scenario/markets")
    history = client.get("/api/v1/scenario/history", params={"market": "Total Inbound"})
    assert markets.status_code == 200
    assert history.status_code == 200
    assert "Total Inbound" in markets.json()
    assert len(history.json()["points"]) >= 2


def test_create_update_delete_observation(client: TestClient):
    payload = {
        "series_id": 3,
        "month": "2025Mar",
        "date": "2025-03-01T00:00:00",
        "value": 111.0,
    }
    created = client.post("/api/v1/observations", json=payload)
    assert created.status_code == 201

    updated = client.put("/api/v1/observations/3/2025Mar", params={"value": 222.0})
    assert updated.status_code == 200
    assert updated.json()["value"] == 222.0

    deleted = client.delete("/api/v1/observations/3/2025Mar")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True