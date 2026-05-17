# Plan: Add Market Status Endpoint

## Changes
1. Create `app/api/routes/market_status.py` — simple GET route returning `{"market": "open"}`
2. Register route in `app/api/router.py` at `/market-status`
3. Add integration test in `tests/api/integration/test_router_integration.py` — assert route registered + returns 200

## Architecture
- Follows existing pattern from `meta.py` (simple route, no dependencies)
- Registered at top level (no prefix) under tags `["market"]`
