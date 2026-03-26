from fastapi import FastAPI

from app.api.router import api_router

API_PREFIX = "/api/v1"

def create_app() -> FastAPI:
    app = FastAPI(
        title="Agentic Hedge Fund",
        description="Agentic hedge fund research and decisioning stack"
    )
    app.include_router(api_router, prefix=API_PREFIX)
    return app

app = create_app()