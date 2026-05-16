import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_test_endpoint_returns_ok(app: FastAPI) -> None:
    client = TestClient(app)
    response = client.get("/api/v1/test")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
