import pytest
from httpx import AsyncClient

from app.api.schemas.signal import SignalResponse
from app.services.rate_limit_service import GUEST_COOKIE_NAME, RateLimitDecision


def _allowed_decision(guest_cookie_value: str | None = None) -> RateLimitDecision:
    return RateLimitDecision(
        allowed=True,
        identity_type="anon",
        limit=2,
        remaining=1,
        reset_at=None,
        upgrade_required=True,
        guest_cookie_value=guest_cookie_value,
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyze_success_sets_guest_cookie(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.routes import analyze as analyze_route

    monkeypatch.setattr(
        analyze_route,
        "check_analyze_rate_limit",
        lambda request, response: _allowed_decision("guest.signed"),
    )
    monkeypatch.setattr(
        analyze_route,
        "run_signal_sync",
        lambda payload: SignalResponse(
            symbol="AAPL",
            signal="buy",
            confidence=0.8,
            reasoning="Strong setup",
        ),
    )

    response = await async_client.post(
        "/api/v1/signals/analyze",
        json={"query": "Please analyze AAPL for swing setup", "symbol": "AAPL", "horizon": "swing"},
    )

    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
    assert GUEST_COOKIE_NAME in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyze_returns_429_when_rate_limited(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api.routes import analyze as analyze_route

    monkeypatch.setattr(
        analyze_route,
        "check_analyze_rate_limit",
        lambda request, response: RateLimitDecision(
            allowed=False,
            identity_type="anon",
            limit=2,
            remaining=0,
            reset_at=None,
            upgrade_required=True,
            guest_cookie_value=None,
        ),
    )

    response = await async_client.post(
        "/api/v1/signals/analyze",
        json={"query": "Please analyze TSLA for swing setup", "symbol": "TSLA", "horizon": "swing"},
    )

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "rate_limit_exceeded"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_analyze_maps_timeouts_to_504(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import time

    from app.api.routes import analyze as analyze_route

    monkeypatch.setattr(
        analyze_route,
        "check_analyze_rate_limit",
        lambda request, response: _allowed_decision(),
    )
    monkeypatch.setattr(analyze_route, "ANALYZE_TIMEOUT_SECONDS", 0.001)
    monkeypatch.setattr(analyze_route, "run_signal_sync", lambda payload: time.sleep(0.02))

    response = await async_client.post(
        "/api/v1/signals/analyze",
        json={"query": "Please analyze NVDA for swing setup", "symbol": "NVDA", "horizon": "swing"},
    )

    assert response.status_code == 504
    assert "timed out" in response.json()["detail"]
