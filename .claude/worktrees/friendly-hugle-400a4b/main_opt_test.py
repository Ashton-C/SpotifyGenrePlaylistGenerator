# Spotify Genre Playlist Generator — CLI entry point
# Business logic lives in core.py. This file is just prompts + wiring.
import os
import sys
import time

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

import core

load_dotenv()

if not core.lastfm_network:
    print("Error: LASTFM_API_KEY not set in .env")
    sys.exit(1)


def main():
    print('=' * 66)
    print('            Spotify Playlist By Genre Generator')
    print('=' * 66)

    scope = 'user-library-read playlist-modify-public playlist-modify-private'
    auth_manager = SpotifyOAuth(
        client_id=os.environ['SPOTIPY_CLIENT_ID'],
        client_secret=os.environ['SPOTIPY_CLIENT_SECRET'],
        redirect_uri=os.environ['SPOTIPY_REDIRECT_URI'],
        scope=scope,
    )
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    username = spotify.current_user()['id']
    print(f"Authenticated as: {username}\n")

    broad_narrow = input(
        "Broad (fewer playlists, top genre only) or Narrow (more playlists, two genres)? "
        "Broad/Narrow: "
    ).strip().upper()

    start = time.time()
    total = core.get_total_tracks(spotify)
    print(f"Total songs in library: {total}")

    def on_progress(processed, total):
        print(f"  Songs tagged: {processed}/{total}", end="\r")

    tagged, untagged = core.fetch_and_tag_songs(total, spotify, broad_narrow, on_progress)
    print()
    print(f"  Tagged by Last.fm: {len(tagged)} | Audio fallback needed: {len(untagged)}")

    if untagged:
        print(f"\nRunning audio feature fallback for {len(untagged)} songs...")
        core.assign_genres_by_audio(untagged, tagged, spotify)

    all_songs = tagged + [s for s in untagged if s.genre1]
    genres = core.determine_playlists(all_songs)
    playlists = core.set_playlists(genres, all_songs)

    print("\nCreating playlists on Spotify...")
    created = core.make_playlists(playlists, spotify, username)
    print(f"\nDone! Created {len(created)} playlists in {time.time() - start:.1f}s")
    for pl in created:
        print(f"  {pl['name']} — {pl['track_count']} tracks  {pl['url']}")


if __name__ == '__main__':
    main()
