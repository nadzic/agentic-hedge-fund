# PR Summary: Add Market Status Endpoint

## What
Added `GET /api/v1/market-status` endpoint returning `{"market": "open"}`.

## Changes
- **New file**: `app/api/routes/market_status.py` — simple GET route with Pydantic response model
- **Modified**: `app/api/router.py` — registered new route under `/api/v1` with tag `["market"]`
- **Modified**: `tests/api/integration/test_router_integration.py` — added route registration assertion + functional test

## Tests
- All 19 tests pass
- Coverage: 92% (threshold: 85%)
- Lint: passed (ruff)
- Type check: passed (basedpyright, 0 errors)

## Architecture
Follows existing pattern from `meta.py` — minimal route with no external dependencies.
