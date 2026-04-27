from fastapi import APIRouter
from app.services import deadlock_api

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("/{match_id}")
async def get_match(match_id: int):
    return await deadlock_api.get_match_metadata(match_id)
