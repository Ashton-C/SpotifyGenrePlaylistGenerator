# How Deadlock Match Data Is Collected

Since Valve provides no public API for Deadlock, the entire data ecosystem is community-built.

## The Pipeline (in order)

### 1. Steam HTTP Cache
When you view replays inside the Deadlock client, Steam caches the replay metadata in:
```
C:\Program Files (x86)\Steam\appcache\httpcache\
```
These cached files contain URLs of the form:
```
http://replay<cluster>.valve.net/1422450/<match_id>_<salt>.dem.bz2
```
The `match_id` and `salt` are all that's needed to fetch a full replay.

### 2. Ingest Tool
The open-source tool at https://github.com/deadlock-api/deadlock-api-ingest (Rust binary)
reads your Steam cache directory, extracts `{match_id, salt}` pairs, and submits them to
`api.deadlock-api.com`. It collects **no personal data** — only match identifiers.

**To ensure your own games are always tracked:**
1. Download the latest release from https://github.com/deadlock-api/deadlock-api-ingest/releases
2. Run it after each gaming session (or keep it running in the background)
3. Your matches will appear in the database within minutes

### 3. Replay Fetch & Parse
The deadlock-api backend uses the submitted salts to download `.dem.bz2` replay files from
Valve's CDN and parses them with the `haste` Rust parser. This extracts:
- Per-player stats (kills, deaths, assists, net worth, hero damage, etc.)
- Item build timings
- Ability upgrade choices
- Kill/damage events

### 4. REST API
Parsed data is stored in ClickHouse (analytics) and PostgreSQL (transactional) and served via
`https://api.deadlock-api.com`. No API key required for basic endpoints.

## Deep Stats via Local Replay Parsing

For stats not available through the API (per-tick positions, item timing, etc.), you can parse
replays locally using [boon-deadlock](https://github.com/pnxenopoulos/boon):

```bash
pip install boon-deadlock
```

```python
from boon import Demo

# Download .dem file from replay<cluster>.valve.net/1422450/<match_id>_<salt>.dem.bz2
demo = Demo("match.dem")
print(demo.kills)          # Polars DataFrame of all kill events
print(demo.player_ticks)   # Per-tick player state (position, health, net worth, ...)
print(demo.item_purchases) # Item buy/sell timestamps
```

## Coverage Limitations

- Only matches where at least one player ran the ingest tool are captured
- MMR/rank is estimated — Valve does not expose an official rank endpoint
- The ingest tool only sees replays cached by the Deadlock client (must view replay tab)
- Data completeness improves as more community members run the ingest tool
