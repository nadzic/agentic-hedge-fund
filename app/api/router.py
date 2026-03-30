from fastapi import APIRouter

from app.api.routes.analyze import router as analyze_router
from app.api.routes.health import router as health_router
from app.api.routes.meta import router as meta_router
from app.api.routes.rag_ingest import router as rag_ingest_router
from app.api.routes.rag_query import router as rag_query_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(meta_router, prefix="/meta", tags=["meta"])
api_router.include_router(analyze_router, prefix="/signals", tags=["analyze"])
api_router.include_router(rag_ingest_router, prefix="/rag", tags=["ingest-index"])
api_router.include_router(rag_query_router, prefix="/rag", tags=["query"])