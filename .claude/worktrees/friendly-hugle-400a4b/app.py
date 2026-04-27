"""
app.py — Flask web app for Spotify Genre Playlist Generator.
Handles OAuth, playlist generation with live progress, and playlist management.
"""
import json
import os

import spotipy
from dotenv import load_dotenv
from flask import (Flask, Response, redirect, render_template,
                   request, session, url_for)
from spotipy.cache_handler import FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyOAuth

import core

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

SCOPE = 'user-library-read playlist-modify-public playlist-modify-private'


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def get_auth_manager():
    cache_handler = FlaskSessionCacheHandler(session)
    return SpotifyOAuth(
        client_id=os.environ['SPOTIPY_CLIENT_ID'],
        client_secret=os.environ['SPOTIPY_CLIENT_SECRET'],
        redirect_uri=os.environ['SPOTIPY_REDIRECT_URI'],
        scope=SCOPE,
        cache_handler=cache_handler,
        show_dialog=False,
    )


def get_spotify():
    """Returns an authenticated Spotipy client, or None if not logged in."""
    auth_manager = get_auth_manager()
    token = auth_manager.cache_handler.get_cached_token()
    if not token or not auth_manager.validate_token(token):
        return None
    return spotipy.Spotify(auth_manager=auth_manager)


# ---------------------------------------------------------------------------
# Routes — auth
# ---------------------------------------------------------------------------

@app.route('/login')
def login():
    auth_manager = get_auth_manager()
    return redirect(auth_manager.get_authorize_url())


@app.route('/callback')
def callback():
    if 'error' in request.args:
        return redirect(url_for('index'))
    auth_manager = get_auth_manager()
    auth_manager.get_access_token(request.args.get('code'))
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Routes — main pages
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    sp = get_spotify()
    user = sp.current_user() if sp else None
    return render_template('index.html', user=user)


@app.route('/generate', methods=['POST'])
def generate():
    if not get_spotify():
        return redirect(url_for('login'))
    session['broad_narrow'] = request.form.get('mode', 'BROAD').upper()
    return redirect(url_for('progress_page'))


@app.route('/progress')
def progress_page():
    if not get_spotify():
        return redirect(url_for('login'))
    mode = session.get('broad_narrow', 'BROAD')
    return render_template('progress.html', mode=mode)


# ---------------------------------------------------------------------------
# Routes — SSE stream
# ---------------------------------------------------------------------------

@app.route('/stream')
def stream():
    sp = get_spotify()
    if not sp:
        def err():
            yield f"data: {json.dumps({'type': 'error', 'msg': 'Not authenticated.'})}\n\n"
        return Response(err(), mimetype='text/event-stream')

    broad_narrow = session.get('broad_narrow', 'BROAD')
    username = sp.current_user()['id']

    def generate():
        try:
            total = core.get_total_tracks(sp)
            yield f"data: {json.dumps({'type': 'total', 'total': total})}\n\n"

            tagged, untagged = [], []
            offset = 0

            # Inline the batch loop here so we can yield progress after every song
            while offset < total:
                batch = core.fetch_batch(sp, offset)
                offset += 20

                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_song = {
                        executor.submit(core.search_for_song, s.title, s.artist): s
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
                        processed = len(tagged) + len(untagged)
                        yield f"data: {json.dumps({'type': 'progress', 'processed': processed, 'total': total})}\n\n"

            yield f"data: {json.dumps({'type': 'status', 'msg': f'Running audio fallback for {len(untagged)} untagged songs...'})}\n\n"

            if untagged:
                core.assign_genres_by_audio(untagged, tagged, sp)

            all_songs = tagged + [s for s in untagged if s.genre1]
            genres = core.determine_playlists(all_songs)
            playlists = core.set_playlists(genres, all_songs)

            yield f"data: {json.dumps({'type': 'status', 'msg': 'Creating playlists on Spotify...'})}\n\n"

            created = core.make_playlists(playlists, sp, username)

            yield f"data: {json.dumps({'type': 'done', 'created': created, 'tagged': len(tagged), 'untagged': len(untagged)})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'msg': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'X-Accel-Buffering': 'no', 'Cache-Control': 'no-cache'},
    )


# ---------------------------------------------------------------------------
# Routes — playlist manager
# ---------------------------------------------------------------------------

@app.route('/manage')
def manage():
    sp = get_spotify()
    if not sp:
        return redirect(url_for('login'))

    playlists = []
    result = sp.current_user_playlists(limit=50)
    while result:
        playlists.extend(result['items'])
        result = sp.next(result) if result['next'] else None

    return render_template('manage.html', playlists=playlists)


@app.route('/delete-playlists', methods=['POST'])
def delete_playlists():
    sp = get_spotify()
    if not sp:
        return redirect(url_for('login'))

    ids = request.form.getlist('playlist_ids')
    for pid in ids:
        sp.current_user_unfollow_playlist(pid)

    return redirect(url_for('manage'))


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=int(os.environ.get('PORT', 5000)))
