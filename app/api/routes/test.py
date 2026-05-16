from fastapi import APIRouter

router = APIRouter()


@router.get("/test")
async def test_endpoint() -> dict[str, str]:
    return {"status": "ok"}
