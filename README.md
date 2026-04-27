# Spotify Genre Playlist Generator

Takes your Spotify Liked Songs library and automatically sorts them into genre-specific playlists using **Last.fm community tags** — track-level, not artist/album-level, so genres are genuinely specific (think "shoegaze" and "bedroom pop", not just "Rock").

---

## How It Works

1. Authenticates with your Spotify account via OAuth (browser-based, no copy-pasting URLs).
2. Fetches all your Liked Songs in batches of 20.
3. For each song, looks up track-level genre tags from Last.fm (`track.getTopTags`).
4. Songs Last.fm doesn't know get assigned to the nearest genre using Spotify's audio features (danceability, energy, valence, etc.) and euclidean distance to genre centroids.
5. Creates public playlists on your Spotify account, one per genre.

Supports **Broad** mode (top genre tag only → fewer playlists) or **Narrow** mode (top two tags → more specific playlists, songs can appear in two).

---

## Revival Plan

### What Changed
| Problem | Fix |
|---------|-----|
| GraceNote API is defunct (`pygn` unmaintained) | Replaced with Last.fm `track.getTopTags` — free, track-level, community-sourced |
| Secrets hardcoded in `config.py` | Moved to `.env` via `python-dotenv` |
| Broken threading (`executor.submit` misuse) | Fixed — Last.fm lookups now actually run concurrently |
| Deprecated `spotipy.util.prompt_for_user_token` | Replaced with `SpotifyOAuth` — handles browser auth and token refresh |
| No `requirements.txt` | Added |

### Phases

#### Phase 1 — Foundation (done)
- [x] `requirements.txt`
- [x] `.env` pattern for secrets
- [x] Updated `.gitignore`

#### Phase 2 — Core Rewrite (done)
- [x] Replace GraceNote with Last.fm `track.getTopTags`
- [x] Fix threading
- [x] Fix deprecated Spotify auth
- [x] Audio feature fallback for untagged songs

#### Phase 3 — Web App (next)
- [ ] Flask app with `/login`, `/callback`, `/generate` routes
- [ ] Spotify OAuth handled in-browser
- [ ] Simple UI: choose broad/narrow, trigger generation, show results
- [ ] Deploy to Render or Railway (free tier)

---

## Running Locally

**Requirements:** Python 3.9+ and `pip`. A virtual environment is recommended but optional.

### 1. Clone and enter the repo
```bash
git clone https://github.com/Ashton-C/SpotifyGenrePlaylistGenerator.git
cd SpotifyGenrePlaylistGenerator
```

### 2. Get API keys

| Service | URL | Notes |
|---------|-----|-------|
| Spotify | [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) | Create an app, set redirect URI to `http://localhost:5000/callback`, copy Client ID + Secret |
| Last.fm | [last.fm/api/account/create](https://www.last.fm/api/account/create) | Free, instant, no credit card. Copy the API key |

### 3. Configure credentials
```bash
cp .env.example .env
# Edit .env and paste in your Spotify Client ID/Secret and Last.fm API key
```

### 4. Install dependencies
```bash
# (optional but recommended) create a virtual environment first:
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 5. Run it
```bash
python main_opt_test.py
```
On first run, a browser window will open for Spotify OAuth. After you log in, the token caches to `.cache-<your_username>` and subsequent runs skip the browser step.

### Subsequent runs
Just `python main_opt_test.py`. The CLI will prompt you to either:
1. **Delete** previously-created playlists (cleanup before regenerating), or
2. **Generate** new playlists (Broad or Narrow mode)

### Troubleshooting
- **"INVALID_CLIENT: Invalid redirect URI"** — make sure `http://localhost:5000/callback` is registered in your Spotify app dashboard *and* matches `SPOTIPY_REDIRECT_URI` in `.env` exactly.
- **Last.fm tags missing for many tracks** — expected for obscure or newer releases; the audio-feature fallback will route them to the nearest tagged-genre centroid.
- **Auth loop / stale token** — delete the `.cache-*` file in the repo root and re-run.

---

## Dependencies

- [spotipy](https://github.com/spotipy-dev/spotipy) — Spotify Web API
- [pylast](https://github.com/pylast/pylast) — Last.fm API
- [python-dotenv](https://github.com/theskumar/python-dotenv) — `.env` loading
- [flask](https://flask.palletsprojects.com/) — web app (Phase 3)
