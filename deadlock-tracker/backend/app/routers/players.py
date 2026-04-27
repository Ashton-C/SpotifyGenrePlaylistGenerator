from fastapi import APIRouter, HTTPException, Query
from app.services import deadlock_api, steam_api

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("/{account_id}")
async def get_player(account_id: int):
    steam64 = steam_api.account_id_to_steam64(account_id)
    steam_profile, match_history = await _gather(
        steam_api.get_player_summary(steam64),
        deadlock_api.get_match_history(account_id, limit=5),
    )
    return {
        "account_id": account_id,
        "steam64": steam64,
        "steam_profile": steam_profile,
        "recent_matches": match_history,
    }


@router.get("/{account_id}/matches")
async def get_matches(
    account_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await deadlock_api.get_match_history(account_id, limit=limit, offset=offset)


@router.get("/{account_id}/rank-history")
async def get_rank_history(account_id: int):
    return await deadlock_api.get_mmr_history(account_id)


@router.get("/{account_id}/heroes")
async def get_hero_stats(account_id: int):
    """Aggregate per-hero performance from match history."""
    matches = await deadlock_api.get_match_history(account_id, limit=100)

    if not isinstance(matches, list):
        matches = matches.get("matches", []) if isinstance(matches, dict) else []

    hero_map: dict[int, dict] = {}
    for m in matches:
        hero_id = m.get("hero_id")
        if hero_id is None:
            continue
        if hero_id not in hero_map:
            hero_map[hero_id] = {
                "hero_id": hero_id,
                "games": 0,
                "wins": 0,
                "kills": 0,
                "deaths": 0,
                "assists": 0,
            }
        entry = hero_map[hero_id]
        entry["games"] += 1
        # match_result is the winning team index; compare to player_team
        if m.get("match_result") == m.get("player_team"):
            entry["wins"] += 1
        entry["kills"] += m.get("player_kills", 0)
        entry["deaths"] += m.get("player_deaths", 0)
        entry["assists"] += m.get("player_assists", 0)

    results = []
    for entry in hero_map.values():
        g = entry["games"]
        d = entry["deaths"] or 1
        results.append({
            **entry,
            "win_rate": round(entry["wins"] / g, 4) if g else 0,
            "avg_kills": round(entry["kills"] / g, 2) if g else 0,
            "avg_deaths": round(entry["deaths"] / g, 2) if g else 0,
            "avg_assists": round(entry["assists"] / g, 2) if g else 0,
            "avg_kda": round((entry["kills"] + entry["assists"]) / d, 2),
        })
    return sorted(results, key=lambda x: x["games"], reverse=True)


@router.get("/{account_id}/live")
async def get_live_match(account_id: int):
    active = await deadlock_api.get_active_match(account_id)
    if active is None:
        raise HTTPException(status_code=404, detail="Player is not in an active match")
    return active


async def _gather(*coros):
    import asyncio
    return await asyncio.gather(*coros, return_exceptions=True)
