# PR Summary: Add Server Time Endpoint

## What was done

Added a `GET /api/v1/meta/server-time` endpoint that returns the current server timestamp in ISO 8601 format.

## Changes

- **`app/api/routes/server_time.py`** (new) — Route handler with `ServerTimeResponse` Pydantic model
- **`app/api/router.py`** — Registered the new router under `/meta` prefix
- **`tests/api/unit/test_server_time_unit.py`** (new) — Unit test verifying response shape and ISO format parseability
- **`tests/api/integration/test_router_integration.py`** — Added route path assertion

## Response example

```json
{
  "timestamp": "2026-05-17T18:00:00.000000+00:00"
}
```

## Tests

- All 3 new/modified tests pass
- All 6 unit tests pass
- Ruff lint: clean
- Basedpyright type check: clean
