"""HTTP regression tests for calculator and static browser delivery."""
from fastapi.testclient import TestClient

from agents.api import app

client = TestClient(app)


def test_api_duke_reference_example():
    response = client.post("/api/duke", json={
        "exercise_minutes": 9,
        "st_deviation_mm": 1,
        "angina_index": 1,
    })
    assert response.status_code == 200
    assert response.json()["score"] == 0
    assert response.json()["tier"] == "moderate"


def test_api_rejects_missing_invalid_and_nonfinite_inputs():
    cases = [
        {"exercise_minutes": 9, "st_deviation_mm": 1},
        {"exercise_minutes": -1, "st_deviation_mm": 0, "angina_index": 0},
        {"exercise_minutes": 9, "st_deviation_mm": 1, "angina_index": 3},
        {"exercise_minutes": 9, "st_deviation_mm": 1, "angina_index": True},
        {"exercise_minutes": "NaN", "st_deviation_mm": 1, "angina_index": 0},
    ]
    for data in cases:
        assert client.post("/api/duke", json=data).status_code == 422


def test_browser_assets_are_served():
    page = client.get("/")
    assert page.status_code == 200
    assert "Exercise duration (minutes)" in page.text
    script = client.get("/calculator.js")
    assert script.status_code == 200
    assert "calculateDukeScore" in script.text


def test_legacy_health_and_audit_endpoints_remain_available():
    assert client.get("/health").status_code == 200
    assert client.get("/metrics").status_code == 200
    payload = {
        "task_id": "T-001", "target_identifier": "KEY-001",
        "primary_metric": 10, "secondary_metric": 2,
    }
    assert client.post("/api/audit", json=payload).status_code == 200
