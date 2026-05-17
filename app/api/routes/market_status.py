from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class MarketStatusResponse(BaseModel):
    market: str


@router.get("/market-status", response_model=MarketStatusResponse)
async def get_market_status() -> MarketStatusResponse:
    return MarketStatusResponse(market="open")
