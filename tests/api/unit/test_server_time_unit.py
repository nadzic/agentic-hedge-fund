from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.mark.unit
def test_server_time_returns_iso_timestamp() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/meta/server-time")

    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
