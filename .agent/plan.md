# Plan: Add Server Time Endpoint

## Steps

1. **Create `app/api/routes/server_time.py`** — new route file with:
   - Pydantic response model `ServerTimeResponse` with `timestamp: str`
   - `GET /server-time` handler returning `datetime.now(timezone.utc).isoformat()`

2. **Register route in `app/api/router.py`** — include with prefix `/meta` alongside existing meta routes (fits the pattern of simple utility endpoints)

3. **Add unit test `tests/api/unit/test_server_time_unit.py`** — verify response shape and ISO format

4. **Update `tests/api/integration/test_router_integration.py`** — add assertion for `/api/v1/meta/server-time`
