"""
core.py — Shared business logic for Spotify Genre Playlist Generator.
Used by both main_opt_test.py (CLI) and app.py (Flask web app).
No I/O here — all printing/progress is the caller's responsibility.
"""
import os
import concurrent.futures

import spotipy
import pylast
from dotenv import load_dotenv

load_dotenv()

_lastfm_key = os.environ.get('LASTFM_API_KEY')
lastfm_network = pylast.LastFMNetwork(api_key=_lastfm_key) if _lastfm_key else None


class Song:
    def __init__(self, title, artist, track_id):
        self.id = track_id
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


def get_total_tracks(spotify):
    """Returns total number of tracks in the user's Liked Songs."""
    response = spotify.current_user_saved_tracks(limit=1, offset=0)
    return response['total']


def fetch_batch(spotify, offset):
    """Fetches a batch of 20 liked songs starting at offset."""
    response = spotify.current_user_saved_tracks(limit=20, offset=offset)
    songs = []
    for item in response['items']:
        track = item['track']
        if not track:
            continue
        artist = track['artists'][0]['name']
        songs.append(Song(track['name'], artist, track['id']))
    return songs


def search_for_song(title, artist):
    """
    Returns (genre1, genre2) from Last.fm top tags, or (None, None) if not found.
    genre2 may be None if there's only one tag.
    """
    if not lastfm_network:
        return None, None
    try:
        track = lastfm_network.get_track(artist, title)
        tags = track.get_top_tags(limit=5)
        if not tags:
            return None, None
        genre1 = tags[0].item.get_name()
        genre2 = tags[1].item.get_name() if len(tags) > 1 else None
        return genre1, genre2
    except Exception:
        return None, None


def fetch_and_tag_songs(total, spotify, broad_narrow, on_progress=None):
    """
    Fetches all liked songs in batches and tags them with Last.fm genres concurrently.

    Args:
        total: total number of songs in the library
        spotify: authenticated Spotipy client
        broad_narrow: 'BROAD' (genre1 only) or 'NARROW' (genre1 + genre2)
        on_progress: optional callback(processed: int, total: int) called after each song

    Returns:
        (tagged: list[Song], untagged: list[Song])
    """
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
                if on_progress:
                    on_progress(counter, total)

    return tagged, untagged


def assign_genres_by_audio(untagged_songs, tagged_songs, spotify):
    """
    Assigns untagged songs to the nearest genre centroid using Spotify audio features
    (danceability, energy, valence, acousticness, instrumentalness, speechiness, tempo).
    Modifies untagged_songs in place.
    """
    if not tagged_songs or not untagged_songs:
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
        distances = [sum((a - b) ** 2 for a, b in zip(vec, c)) for c in centroids]
        song.genre1 = genres[distances.index(min(distances))]


def determine_playlists(songs):
    """Returns a list of Genre objects, one per unique genre found across all songs."""
    genre_names = set()
    for song in songs:
        if song.genre1:
            genre_names.add(song.genre1)
        if song.genre2:
            genre_names.add(song.genre2)
    return [Genre(g) for g in genre_names]


def set_playlists(genres, songs):
    """Populates each Genre's playlist list with the IDs of matching songs."""
    for genre in genres:
        for song in songs:
            if song.genre1 == genre.name or song.genre2 == genre.name:
                genre.add_song(song.id)
    return genres


def make_playlists(playlists, spotify, user):
    """
    Creates playlists on Spotify and populates them with songs.
    Returns (count, list of created playlist dicts with name/id/track_count).
    """
    created = []
    for genre in playlists:
        if not genre.playlist:
            continue
        new_pl = spotify.user_playlist_create(user, genre.name, public=True)
        playlist_id = new_pl['id']
        ids = genre.playlist
        for i in range(0, len(ids), 99):
            spotify.playlist_add_items(playlist_id, ids[i:i + 99])
        created.append({
            'name': genre.name,
            'id': playlist_id,
            'track_count': len(ids),
            'url': new_pl['external_urls']['spotify']
        })
    return created
