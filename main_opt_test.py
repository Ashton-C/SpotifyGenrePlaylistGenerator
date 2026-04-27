# Spotify Genre Playlist Generator by Ashton Christensen
import os
import sys
import time
import concurrent.futures

import spotipy
import pylast
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from spotipy.client import SpotifyException

load_dotenv()

start_time = time.time()

_lastfm_key = os.environ.get('LASTFM_API_KEY')
lastfm_network = pylast.LastFMNetwork(api_key=_lastfm_key) if _lastfm_key else None


class Song:
    def __init__(self, title, artist, id):
        self.id = id
        self.title = title
        self.artist = artist
        self.genre1 = None
        self.genre2 = None


class Genre:
    def __init__(self, name):
        self.name = name
        self.playlist = []

    def add_song(self, song_id):
        self.playlist.append(song_id)


def main():
    if not lastfm_network:
        print("Error: LASTFM_API_KEY not set in .env")
        sys.exit(1)

    print_header()
    username, spotify = authenticate_user()

    answer = input(
        "\nWhat would you like to do?\n"
        "  1) Delete playlists from last time\n"
        "  2) Create new playlists\n"
        "Enter 1 or 2: "
    ).strip()

    if answer == '1':
        to_del = int(input("How many playlists would you like deleted? "))
        for _ in range(to_del):
            result = spotify.current_user_playlists(limit=1)
            for item in result['items']:
                spotify.current_user_unfollow_playlist(item['id'])
        print(f"Deleted {to_del} playlists!")
        if input("Create playlists now? Y/N: ").strip().upper() == 'Y':
            answer = '2'

    if answer == '2':
        broad_narrow = input(
            "Broad (fewer playlists, top genre only) or Narrow (more playlists, two genres per track)? "
            "Broad/Narrow: "
        ).strip().upper()
        total = get_total_tracks(spotify)
        tagged, untagged = fetch_and_tag_songs(total, spotify, broad_narrow)

        if untagged:
            print(f"\nRunning audio feature fallback for {len(untagged)} untagged songs...")
            assign_genres_by_audio(untagged, tagged, spotify)

        all_songs = tagged + [s for s in untagged if s.genre1]
        genres = determine_playlists(all_songs)
        playlists = set_playlists(genres, all_songs)
        print(make_playlists(playlists, spotify, username))
        print(f"--- Execution took {time.time() - start_time:.1f} seconds ---")


def print_header():
    print('=' * 66)
    print('')
    print('            Spotify Playlist By Genre Generator')
    print('')
    print('=' * 66)


def authenticate_user():
    scope = 'user-library-read playlist-modify-public playlist-modify-private'
    auth_manager = SpotifyOAuth(
        client_id=os.environ['SPOTIPY_CLIENT_ID'],
        client_secret=os.environ['SPOTIPY_CLIENT_SECRET'],
        redirect_uri=os.environ['SPOTIPY_REDIRECT_URI'],
        scope=scope
    )
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    username = spotify.current_user()['id']
    print(f"Authenticated as: {username}")
    return username, spotify


def get_total_tracks(spotify):
    response = spotify.current_user_saved_tracks(limit=1, offset=0)
    total = response['total']
    print(f"Total songs in library: {total}")
    return total


def search_for_song(title, artist):
    """Returns (genre1, genre2) from Last.fm tags, or (None, None) if not found."""
    try:
        track = lastfm_network.get_track(artist, title)
        tags = track.get_top_tags(limit=5)
        if not tags:
            return None, None
        genre1 = tags[0].item.get_name()
        genre2 = tags[1].item.get_name() if len(tags) > 1 else None
        return genre1, genre2
    except pylast.WSError:
        return None, None
    except Exception:
        return None, None


def fetch_batch(spotify, offset):
    response = spotify.current_user_saved_tracks(limit=20, offset=offset)
    songs = []
    for item in response['items']:
        track = item['track']
        if not track:
            continue
        artist = track['artists'][0]['name']
        songs.append(Song(track['name'], artist, track['id']))
    return songs


def fetch_and_tag_songs(total, spotify, broad_narrow):
    """Fetches all liked songs in batches and looks up Last.fm tags concurrently."""
    tagged, untagged = [], []
    counter = 0
    offset = 0

    while offset < total:
        batch = fetch_batch(spotify, offset)
        offset += 20

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_song = {
                executor.submit(search_for_song, s.title, s.artist): s
                for s in batch
            }
            for future, song in future_to_song.items():
                genre1, genre2 = future.result()
                if genre1 is None:
                    untagged.append(song)
                else:
                    song.genre1 = genre1
                    song.genre2 = genre2 if broad_narrow == 'NARROW' else None
                    tagged.append(song)
                counter += 1
                print(f"Songs processed: {counter}/{total}", end="\r")

    print()
    print(f"  Tagged by Last.fm: {len(tagged)} | Needs audio fallback: {len(untagged)}")
    return tagged, untagged


def assign_genres_by_audio(untagged_songs, tagged_songs, spotify):
    """Assigns untagged songs to the nearest genre centroid using Spotify audio features."""
    if not tagged_songs:
        return

    genre_track_ids = {}
    for song in tagged_songs:
        if song.genre1:
            genre_track_ids.setdefault(song.genre1, []).append(song.id)

    if not genre_track_ids:
        return

    feature_keys = [
        'danceability', 'energy', 'valence', 'acousticness',
        'instrumentalness', 'speechiness', 'tempo'
    ]
    max_tempo = 250.0

    def normalize(feat):
        return [feat[k] / (max_tempo if k == 'tempo' else 1.0) for k in feature_keys]

    def batch_audio_features(ids):
        results = {}
        for i in range(0, len(ids), 50):
            batch = spotify.audio_features(ids[i:i + 50]) or []
            for f in batch:
                if f:
                    results[f['id']] = f
        return results

    # Build centroid per genre from tagged songs' audio features
    genre_centroids = {}
    for genre, ids in genre_track_ids.items():
        features = batch_audio_features(ids)
        if not features:
            continue
        vecs = [normalize(f) for f in features.values()]
        dim = len(feature_keys)
        centroid = [sum(v[i] for v in vecs) / len(vecs) for i in range(dim)]
        genre_centroids[genre] = centroid

    if not genre_centroids:
        return

    untagged_features = batch_audio_features([s.id for s in untagged_songs])

    genres = list(genre_centroids.keys())
    centroids = [genre_centroids[g] for g in genres]

    for song in untagged_songs:
        feat = untagged_features.get(song.id)
        if not feat:
            continue
        vec = normalize(feat)
        distances = [
            sum((a - b) ** 2 for a, b in zip(vec, c)) for c in centroids
        ]
        song.genre1 = genres[distances.index(min(distances))]


def determine_playlists(songs):
    genre_names = set()
    for song in songs:
        if song.genre1:
            genre_names.add(song.genre1)
        if song.genre2:
            genre_names.add(song.genre2)
    return [Genre(g) for g in genre_names]


def set_playlists(genres, songs):
    for genre in genres:
        for song in songs:
            if song.genre1 == genre.name or song.genre2 == genre.name:
                genre.add_song(song.id)
    return genres


def make_playlists(playlists, spotify, user):
    counter = 0
    for genre in playlists:
        if not genre.playlist:
            continue
        counter += 1
        new_pl = spotify.user_playlist_create(user, genre.name, public=True)
        playlist_id = new_pl['id']
        ids = genre.playlist
        for i in range(0, len(ids), 99):
            spotify.playlist_add_items(playlist_id, ids[i:i + 99])

    return f"All done! Created {counter} playlists."


if __name__ == '__main__':
    main()
