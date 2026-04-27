import time
import os
import httpx
from typing import Any

BASE_URL = "https://api.deadlock-api.com"
CACHE_TTL = 300  # 5 minutes

_cache: dict[str, tuple[float, Any]] = {}


def _api_key_headers() -> dict[str, str]:
    key = os.getenv("DEADLOCK_API_KEY", "")
    return {"X-API-KEY": key} if key else {}


def _get_cached(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < CACHE_TTL:
        return entry[1]
    return None


def _set_cached(key: str, value: Any) -> None:
    _cache[key] = (time.time(), value)


async def _get(path: str) -> Any:
    cached = _get_cached(path)
    if cached is not None:
        return cached
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
        resp = client.build_request("GET", path, headers=_api_key_headers())
        r = await client.send(resp)
        r.raise_for_status()
        data = r.json()
    _set_cached(path, data)
    return data


async def get_match_history(account_id: int, limit: int = 20, offset: int = 0) -> Any:
    return await _get(f"/v1/players/{account_id}/match-history?limit={limit}&offset={offset}")


async def get_match_metadata(match_id: int) -> Any:
    return await _get(f"/v1/matches/{match_id}/metadata")


async def get_mmr_history(account_id: int) -> Any:
    return await _get(f"/v1/players/{account_id}/mmr-history")


async def get_active_match(account_id: int) -> Any:
    # Active match changes frequently — don't cache
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        r = await client.get(
            f"/v1/players/{account_id}/active-match",
            headers=_api_key_headers(),
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


async def get_hero_stats(mode: str = "ranked") -> Any:
    return await _get(f"/v1/analytics/hero-stats?mode={mode}")


async def get_heroes_info() -> Any:
    return await _get("/v1/info/heroes")


async def search_players(query: str, limit: int = 5) -> Any:
    return await _get(f"/v1/players/steam-search?search_query={query}&limit={limit}")
