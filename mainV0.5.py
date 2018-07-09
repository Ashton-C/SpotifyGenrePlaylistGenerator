# Spotify Genre Playlist Generator by Ashton Christensen
import sys
import os
import pygn
import spotipy
import time
import spotipy.util as sp_util
from config import *
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOauthError
from spotipy.client import SpotifyException

scope = 'user-library-read, playlist-modify-public'
SPOTIPY_CLIENT_ID = '6bf27521c6ff4eb2bf72698c63a1d9e8'
SPOTIPY_REDIRECT_URI = 'http://localhost/'
clientID = '1984033224-5834A5143CE87D68376F48BF28A6BEE4'
userID3 = '280167715556773759-7E254039A6A562F4E93D2BE60834523E'
start_time = time.time()


class Song():
    def __init__(self, title, artist, id):
        self.id = id
        self.title = title
        self.artist = artist

    def get_genre(self, genre1, genre2):
        self.genre1 = genre1
        self.genre2 = genre2


class Genre():
    def __init__(self, genre):
        self.name = genre
        self.playlist = []

    def add_song(self, song_id):
        self.playlist.append(song_id)


def main():
    print_header()
    username, spotify = authenticate_user()
    answer = input("What would you like to do? Your options are: Delete playlists from last time, Create new playlists. Please enter 1 or 2.\n")
    if answer == '1':
        to_del = input("How many playlists would you like deleted?\n")
        for i in range(0, int(to_del)+1):
            temp_id = spotify.user_playlists(username, 1, 0)
            for item in temp_id['items']:
                list_id = item['id']
            spotify.user_playlist_unfollow(username, list_id)
        continue_ = input("Deleted {} playlists! Would you like to now create playlists? Y/N?\n".format(to_del))
        if continue_.upper() == 'Y':
            answer = '2'
        else:
            pass
    if answer == '2':
        more_less = input("Would you like broad playlists (less) or narrow playlists (more)? Broad/Narrow?\n")
        total_songs_in_lib = get_total_tracks(spotify)
#    songs = make_songs(total_songs_in_lib, spotify)
        songs = make_songs(total_songs_in_lib, spotify, more_less)
        genres = determine_playlists(songs)
        playlists = set_playlists(genres, songs)
        print(make_playlists(playlists, spotify, username))
        print("--- Execution took {} seconds ---".format(time.time() - start_time))


def print_header():
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print('')
    print('            Spotify Playlist By Genre Generator')
    print('')
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')


def get_data(spotify, offset):
    tracks_response = spotify.current_user_saved_tracks(limit=1,
                                                        offset=offset)
    for item in tracks_response['items']:
        for artist in item['track']['album']['artists']:
            temp_art = artist['name']
        temp_track = item['track']['name']
        temp_id = item['track']['id']
    if temp_id is None or temp_art is None or temp_track is None:
        temp_track = "N/A"
        temp_art = "N/A"
        temp_id = "N/A"
    return temp_track, temp_art, temp_id


def get_total_tracks(spotify):
    total_response = spotify.current_user_saved_tracks(limit=1,
                                                       offset=0)
    temp_total = total_response['total']
    return temp_total


def search_for_song(temp_query, temp_artist):
        try:
            metadata = pygn.search(clientID=clientID, userID=userID3, track=temp_query,
                                   artist=temp_artist)
            temp_genre1 = metadata['genre']['1']['TEXT']
            temp_genre2 = metadata['genre']['2']['TEXT']
            if temp_genre1 is None or temp_genre2 is None:
                temp_genre1 == "N/A"
                temp_genre2 == "N/A"
            return temp_genre1, temp_genre2
        except TypeError as y:
            temp_genre1 = 'N/A'
            temp_genre2 = 'N/A'
        except KeyError as e:
            temp_genre1 = 'N/A'
            temp_genre2 = 'N/A'
        except UnboundLocalError as idk:
            pass


def make_songs(songs_wanted, spotify, broad_narrow):
    songs = []
    counter = 0
    for i in range(songs_wanted):
        temp_data = get_data(spotify, i)
        try:
            temp_genre1, temp_genre2 = search_for_song(temp_data[0], temp_data[1])
        except TypeError as not_found:
            continue
        temp_song = Song(temp_data[0], temp_data[1], temp_data[2])
        if broad_narrow.upper() == "BROAD":
            temp_song.get_genre(temp_genre1, "N/A")
        if broad_narrow.upper() == "NARROW":
            temp_song.get_genre(temp_genre1, temp_genre2)
        songs.append(temp_song)
        counter += 1
        print("Songs data found: {}/{}".format(counter, songs_wanted), end="\r")
    return songs


def determine_playlists(song_list):
    genres = []
    for song in song_list:
        genres.append(song.genre1)
        genres.append(song.genre2)
    genres = list(set(genres))
    genre_objects = []
    for genre in genres:
        temp_genre = Genre(genre)
        genre_objects.append(temp_genre)
    return genre_objects


def set_playlists(genres, songs):
    for genre in genres:
        for song in songs:
            if song.genre1 == genre.name or song.genre2 == genre.name:
                genre.add_song(song.id)
    return genres


def choose_playlists_to_make(playlists):
    print("What playlists would you like to add to your Spotify account?")
    ptm = input("Your options are {}".format(playlists.keys()))
    ptm = ptm.title()
    return ptm


def make_playlists(playlists, spotify, user):
    counter = 0
    print("Now making playlists by genres. Here are the playlists we are making: {}".format(playlists))
    for list in playlists:
        counter += 1
        spotify.user_playlist_create(user, list.name, public=True)
        temp_list_data = spotify.user_playlists(user, 1, 0)
        for item in temp_list_data['items']:
            list_id = item['id']
#        time.sleep(0.015)
        offset = 0
        playlist_length = len(list.playlist)
        if playlist_length > 100:
            while offset < playlist_length:
                spotify.user_playlist_add_tracks(user, playlist_id=list_id, tracks=list.playlist[offset:offset+99])
                offset += 99
        else:
            spotify.user_playlist_add_tracks(user, playlist_id=list_id, tracks=list.playlist)
    return "All done!!! Your playlists are created and populated! Created {} playlists.".format(counter)


def authenticate_client():
    """
    Using credentials from the environment variables, attempt to authenticate
    with the spotify web API.  If successful,
    create a spotipy instance and return it.
    :return: An authenticated Spotipy instance
    """
    try:
        # Get an auth token for this user
        client_credentials = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                      client_secret=SPOTIPY_CLIENT_SECRET)

        spotify = spotipy.Spotify(client_credentials_manager=client_credentials)
        return spotify
    except SpotifyOauthError as e:
        print('API credentials not set.  Please see README for instructions on setting credentials.')
        sys.exit(1)


def authenticate_user():
    """
    Prompt the user for their username and authenticate them against the
    Spotify API. (NOTE: You will have to paste the URL from your browser back
    into the terminal) :return: (username, spotify) Where username is the
    user's username and spotify is an authenticated spotify (spotipy) client
    """
    # Prompt the user for their username
    username = input('\nWhat is your Spotify username: ')

    cache_path = ".cache-" + username

    if not os.path.isfile(cache_path):
        print("""
    You will now be directed to your browser in order to authenticate with
    Spotify.
    Once you log into Spotify, you will be redirected to a
    "http://localhost/?code=..." URL.  Please copy that URL and
    paste it back here in order to complete authentication.
     """)
        input("Press <Enter> to continue...")

    try:
        # Get an auth token for this user
        token = sp_util.prompt_for_user_token(username, scope=scope,
                                              client_id=SPOTIPY_CLIENT_ID,
                                              client_secret=SPOTIPY_CLIENT_SECRET,
                                              redirect_uri=SPOTIPY_REDIRECT_URI)

        spotify = spotipy.Spotify(auth=token)
        return username, spotify

    except SpotifyException as e:
        print('API credentials not set.  Please see README for instructions on setting credentials.')
        sys.exit(1)
    except SpotifyOauthError as e:
        redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')
        if redirect_uri is not None:
            print("""
    Uh oh! It doesn't look like that URI was registered as a redirect URI for
    your application.
    Please check to make sure that "{}" is listed as a Redirect URI and then
    Try again.'
            """.format(redirect_uri))
        else:
            print("""
    Uh oh! It doesn't look like you set a redirect URI for your application.
    Please add
    export SPOTIPY_REDIRECT_URI='http://localhost/'
    to your `credentials.sh`, and then add "http://localhost/" as a Redirect
    URI in your Spotify Application page.
    Once that's done, try again.'""")
        sys.exit(1)


if __name__ == '__main__':
    main()
