from fastapi import APIRouter, HTTPException, Query
from app.services import steam_api, deadlock_api

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search_player(q: str = Query(..., min_length=1)):
    """
    Resolve a query to an account_id.
    Accepts:
      - 17-digit Steam64 ID (e.g. 76561198XXXXXXXXX)
      - 32-bit account_id (<= 10 digits)
      - Steam vanity URL / display name (searched via deadlock-api's steam-search)
    """
    q = q.strip()

    # Steam64 ID
    if q.isdigit() and len(q) == 17:
        steam64 = int(q)
        account_id = steam_api.steam64_to_account_id(steam64)
        profile = await steam_api.get_player_summary(steam64)
        return {"account_id": account_id, "steam64": steam64, "steam_profile": profile}

    # 32-bit account_id
    if q.isdigit() and len(q) <= 10:
        account_id = int(q)
        steam64 = steam_api.account_id_to_steam64(account_id)
        profile = await steam_api.get_player_summary(steam64)
        return {"account_id": account_id, "steam64": steam64, "steam_profile": profile}

    # Name search via deadlock-api (no Steam key required, only Deadlock players)
    results = await deadlock_api.search_players(q, limit=5)
    if isinstance(results, list) and results:
        first = results[0]
        account_id = first.get("account_id")
        steam64 = steam_api.account_id_to_steam64(account_id)
        steam_profile = {
            "steamid": str(steam64),
            "personaname": first.get("personaname", ""),
            "avatarfull": first.get("avatarfull", ""),
            "profileurl": first.get("profileurl", ""),
        }
        return {"account_id": account_id, "steam64": steam64, "steam_profile": steam_profile}

    # Fallback: Steam vanity URL resolution (requires STEAM_API_KEY)
    steam64 = await steam_api.resolve_vanity_url(q)
    if steam64:
        account_id = steam_api.steam64_to_account_id(steam64)
        profile = await steam_api.get_player_summary(steam64)
        return {"account_id": account_id, "steam64": steam64, "steam_profile": profile}

    raise HTTPException(status_code=404, detail=f"Could not resolve player: {q}")


@router.get("/search/suggest")
async def suggest_players(q: str = Query(..., min_length=1)):
    """Return multiple player suggestions for autocomplete."""
    q = q.strip()
    results = await deadlock_api.search_players(q, limit=8)
    if not isinstance(results, list):
        return []
    return [
        {
            "account_id": r.get("account_id"),
            "name": r.get("personaname"),
            "avatar": r.get("avatar"),
        }
        for r in results
    ]
