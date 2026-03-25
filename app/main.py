from fastapi import FastAPI
from app.api.router import api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Agentic Hedge Fund",
        description="Agentic hedge fund research and decisioning stack"
    )
    app.include_router(api_router)
    return app

app = create_app()