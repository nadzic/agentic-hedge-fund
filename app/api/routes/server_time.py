from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ServerTimeResponse(BaseModel):
    timestamp: str


@router.get("/server-time", response_model=ServerTimeResponse)
async def get_server_time() -> ServerTimeResponse:
    return ServerTimeResponse(timestamp=datetime.now(UTC).isoformat())
