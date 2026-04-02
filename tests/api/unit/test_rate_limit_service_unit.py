from starlette.requests import Request

from app.services import rate_limit_service


def _build_request(headers: dict[str, str] | None = None) -> Request:
    headers = headers or {}
    raw_headers = [
        (key.lower().encode("utf-8"), value.encode("utf-8"))
        for key, value in headers.items()
    ]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": raw_headers,
        "query_string": b"",
        "client": ("127.0.0.1", 1234),
    }
    return Request(scope)


def test_sign_and_verify_guest_id_roundtrip() -> None:
    guest_id = "guest-123"
    signed = rate_limit_service._sign_guest_id(guest_id)

    assert rate_limit_service._verify_signed_guest_id(signed) == guest_id
    assert rate_limit_service._verify_signed_guest_id("bad.value") is None


def test_extract_bearer_token_handles_valid_and_invalid_values() -> None:
    with_token = _build_request({"authorization": "Bearer test-token"})
    without_prefix = _build_request({"authorization": "Basic abc"})
    missing_header = _build_request()

    assert rate_limit_service._extract_bearer_token(with_token) == "test-token"
    assert rate_limit_service._extract_bearer_token(without_prefix) is None
    assert rate_limit_service._extract_bearer_token(missing_header) is None


def test_safe_int_parses_known_types_with_fallback() -> None:
    assert rate_limit_service._safe_int(5, fallback=9) == 5
    assert rate_limit_service._safe_int(2.8, fallback=9) == 2
    assert rate_limit_service._safe_int("7", fallback=9) == 7
    assert rate_limit_service._safe_int("invalid", fallback=9) == 9
