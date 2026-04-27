# CLAUDE.md — Spotify Genre Playlist Generator

## What This Project Does
Reads a user's Spotify Liked Songs and auto-sorts them into genre playlists using **Last.fm track-level community tags**. Songs Last.fm doesn't know get assigned to the nearest genre via Spotify audio feature similarity. Currently a Python CLI; being converted to a Flask web app.

## Tech Stack
- **Python 3.x**
- **spotipy** — Spotify Web API client
- **pylast** — Last.fm API client
- **flask** — web app (Phase 3)
- **python-dotenv** — loads `.env` credentials

## Key Files
| File | Role |
|------|------|
| `main_opt_test.py` | Main entry point — batch fetch + concurrent Last.fm lookups + audio fallback |
| `mainV0.5.py` | Old sequential version with GraceNote, kept for git history reference only |
| `.env` | Local credentials (never commit) |
| `.env.example` | Template — copy this to `.env` and fill in keys |
| `requirements.txt` | `pip install -r requirements.txt` |

## Credentials
All secrets live in `.env`. Copy `.env.example` to get started:
```
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://localhost:5000/callback
LASTFM_API_KEY=...
```
Loaded at startup with `load_dotenv()` — no config.py, no hardcoded values.

## Genre Data Sources

### Primary — Last.fm `track.getTopTags`
True track-level community tags, not album/artist-level. Extremely granular (e.g. "shoegaze", "bedroom pop", "post-punk revival").
```python
track = lastfm_network.get_track(artist, title)
tags = track.get_top_tags(limit=5)
genre1 = tags[0].item.get_name()
```
- Rate limit: ~5 req/sec. Code uses `max_workers=5` in ThreadPoolExecutor to stay safe.
- Returns `(None, None)` when track not found — used as the fallback trigger.

### Fallback — Spotify Audio Features + Euclidean Distance
For songs Last.fm doesn't know, fetches Spotify audio features and finds the nearest tagged genre by centroid distance.
- Features used: `danceability`, `energy`, `valence`, `acousticness`, `instrumentalness`, `speechiness`, `tempo` (tempo normalized to 0–1 by dividing by 250)
- Centroid computed per genre from tagged songs
- No ML library needed — plain Python euclidean distance in 7 dimensions

## Spotify OAuth Scopes
```
user-library-read playlist-modify-public playlist-modify-private
```
Auth is handled by `SpotifyOAuth` — opens browser automatically, caches token in `.cache`.

## Spotify API Limits
- Saved tracks: 20 per request (using `limit=20`)
- `audio_features`: max 50 IDs per call (batched accordingly)
- Playlist add: max 100 tracks per call (batched at 99)

## Broad vs Narrow Mode
- **Broad**: `song.genre1` only (top Last.fm tag). Fewer, larger playlists.
- **Narrow**: `song.genre1` + `song.genre2` (top two Last.fm tags). More specific playlists, songs can appear in two.

## Web App Plan (Phase 3)
Flask routes:
- `GET /` — landing page
- `GET /login` — redirects to Spotify OAuth
- `GET /callback` — handles OAuth code exchange
- `POST /generate` — triggers playlist generation (broad/narrow param)

Redirect URI for local dev: `http://localhost:5000/callback` — must be registered in Spotify Developer Dashboard.

## Running Locally
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python main_opt_test.py
```
