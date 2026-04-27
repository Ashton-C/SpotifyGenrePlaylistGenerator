import os
import httpx

STEAM_API_BASE = "https://api.steampowered.com"
STEAM_ID_OFFSET = 76561197960265728


def account_id_to_steam64(account_id: int) -> int:
    return account_id + STEAM_ID_OFFSET


def steam64_to_account_id(steam64: int) -> int:
    return steam64 - STEAM_ID_OFFSET


async def get_player_summary(steam64_id: int) -> dict | None:
    key = os.getenv("STEAM_API_KEY", "")
    if not key:
        return None
    async with httpx.AsyncClient(base_url=STEAM_API_BASE, timeout=10.0) as client:
        r = await client.get(
            "/ISteamUser/GetPlayerSummaries/v2/",
            params={"key": key, "steamids": steam64_id},
        )
        r.raise_for_status()
        players = r.json().get("response", {}).get("players", [])
        return players[0] if players else None


async def resolve_vanity_url(vanity: str) -> int | None:
    """Resolve a Steam vanity URL to a Steam64 ID."""
    key = os.getenv("STEAM_API_KEY", "")
    if not key:
        return None
    async with httpx.AsyncClient(base_url=STEAM_API_BASE, timeout=10.0) as client:
        r = await client.get(
            "/ISteamUser/ResolveVanityURL/v1/",
            params={"key": key, "vanityurl": vanity},
        )
        r.raise_for_status()
        resp = r.json().get("response", {})
        if resp.get("success") == 1:
            return int(resp["steamid"])
        return None
