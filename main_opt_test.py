# Spotify Genre Playlist Generator by Ashton Christensen
import sys
import os
import pygn
import spotipy
import time
import spotipy.util as sp_util
import generate_gn_user_id
import config
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOauthError, SpotifyOAuth
from spotipy.client import SpotifyException

gn_client_ID = '1984033224-5834A5143CE87D68376F48BF28A6BEE4'
start_time = time.time()
test_amount = 45


class Song():
    # this is the basic data structure for all the song data
    def __init__(self, title, artist, id):
        self.id = id
        self.title = title
        self.artist = artist

    def get_genre(self, genre1, genre2):
        self.genre1 = genre1
        self.genre2 = genre2


class Genre():
    # this class is used for holding the song id's to put back into spotify.
    def __init__(self, genre):
        self.name = genre
        self.playlist = []

    def add_song(self, song_id):
        self.playlist.append(song_id)


def main():
    print_header()
    username, spotify, token = authenticate_user()
    gn_user_ID = get_gn_id()
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
        songs = make_songs(total_songs_in_lib, spotify, more_less, gn_user_ID, token)
#        songs = make_songs(test_amount, spotify, more_less, gn_user_ID)
        genres = determine_playlists(songs)
        playlists = set_playlists(genres, songs)
        print(make_playlists(playlists, spotify, username))
        print("--- Execution took {} seconds ---".format(time.time() - start_time))


def print_header():
    ''' Prints the header for the program... pretty basic tbh '''
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    print('')
    print('            Spotify Playlist By Genre Generator')
    print('')
    print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')


def get_gn_id():
    if os.path.exists('grace_note_user_id.txt'):
        f = open('grace_note_user_id.txt', 'r')
        gn_user_id = f.readline()
        return gn_user_id
        print("You GN user ID is: {}".format(gn_user_id))
    else:
        generate_gn_user_id.main()
        f = open('grace_note_user_id.txt', 'r')
        gn_user_id = f.readline()
        return gn_user_id
        print("You GN user ID is: {}".format(gn_user_id))


def get_data(spotify, offset):
    ''' This function calls the Spotify API for each song, one at a time
        to find the artist, track name, and Spotify ID, and returns them. '''
    songs = []
    tracks_response = spotify.current_user_saved_tracks(limit=20,
                                                        offset=offset)
    for item in tracks_response['items']:
        for artist in item['track']['album']['artists']:
            temp_art = artist['name']
        temp_track = item['track']['name']
        temp_id = item['track']['id']
        temp_song = Song(temp_track, temp_art, temp_id)
        songs.append(temp_song)
        print("Song Found!")
    return songs


def get_total_tracks(spotify):
    ''' Simple function to get the total tracks to look for, this is used
    in the make_songs() function '''
    total_response = spotify.current_user_saved_tracks(limit=1,
                                                       offset=0)
    temp_total = total_response['total']
    print("Total songs to make: {}".format(temp_total))
    return temp_total


def search_for_song(temp_query, temp_artist, gn_user_ID):
    ''' This function takes all the Spotify data retrieved and sends it through
        GraceNote in order to get the proper genres for each song. '''
    # It is in a large try/except block because of an error that would pop
    # up when GraceNote couldnt find a song.
    try:
        metadata = pygn.search(clientID=gn_client_ID, userID=gn_user_ID, track=temp_query,
                               artist=temp_artist)
        # GraceNote has 3 seperate genres for every song, more and more specific
        # when running, option 1(Broad), will only use the first line,
        # where as the 'Narrow' option will use the second line and the first line.
        temp_genre1 = metadata['genre']['1']['TEXT']
        temp_genre2 = metadata['genre']['2']['TEXT']
        print("Genre Found!")
        if temp_genre1 is None or temp_genre2 is None:
            temp_genre1 == "N/A"
            temp_genre2 == "N/A"
        return temp_genre1, temp_genre2
    # these type errors are when the song is not found
    except TypeError as y:
        temp_genre1 = 'N/A'
        temp_genre2 = 'N/A'
    # these key errors are when the song is found but has no genre
    except KeyError as e:
        temp_genre1 = 'N/A'
        temp_genre2 = 'N/A'
    # I kept getting this, I didnt know what to do, so I just pass it...
    except UnboundLocalError as idk:
        pass


def make_songs(songs_wanted, spotify, broad_narrow, gn_user_ID, token):
    ''' Here we take all the gathered data, song title, Spotify ID, Artists,
        and genre, and put it all into a Song object. '''
    songs = []
    counter = 0
    i = 0
    # gets the songs data together
    while int(i) < int(songs_wanted):
        temp_data = get_data(spotify, i)
        i += 20
        for x in temp_data:
            # here is where we actually see if a song is found or not.
            try:
                temp_genre1, temp_genre2 = search_for_song(x.title, x.artist, gn_user_ID)
            except TypeError as not_found:
                continue
            # logic for Narrow playlists or broad playlists
            if broad_narrow.upper() == "BROAD":
                x.get_genre(temp_genre1, "N/A")
            if broad_narrow.upper() == "NARROW":
                x.get_genre(temp_genre1, temp_genre2)
            songs.append(x)
            # this line will be replaced by an actual loading bar, but works for now
            counter += 1
#            if counter == 2:
#                SpotifyOAuth.get_access_token(token)
            print("Songs data found: {}/{}".format(counter, songs_wanted), end="\r")
    return songs


def determine_playlists(song_list):
    ''' This function creates all the genre objects, so that the next function
        can populate their playlist arrays. '''
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
    ''' Simply takes the genre objects and fills their playlist arrays via the
        add_song() method. '''
    for genre in genres:
        for song in songs:
            if song.genre1 == genre.name or song.genre2 == genre.name:
                genre.add_song(song.id)
    return genres


def choose_playlists_to_make(playlists):
    ''' NOT USED CURRENTLY '''
    # I would like to use this when I implement a GUI, but the program has
    # changed significantly since I wrote it, so I will most likely rewrite it.
    print("What playlists would you like to add to your Spotify account?")
    ptm = input("Your options are {}".format(playlists.keys()))
    ptm = ptm.title()
    return ptm


def make_playlists(playlists, spotify, user):
    ''' Final function in the main program, this connects with Spotify to create
        the new playlists. It uses the Genre objects which contain the name of
        the new playlist, as well as a list of all the songs in their playlist
        arrays. '''
    counter = 0
    for list in playlists:
        counter += 1
        spotify.user_playlist_create(user, list.name, public=True)
        temp_list_data = spotify.user_playlists(user, 1, 0)
        for item in temp_list_data['items']:
            list_id = item['id']
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
    # I didn't write this function, and for the first bit I didn't even understand it
    # at this point it works and I'd rather not mess with it.
    """
    Using credentials from the environment variables, attempt to authenticate
    with the spotify web API.  If successful,
    create a spotipy instance and return it.
    :return: An authenticated Spotipy instance
    """
    try:
        # Get an auth token for this user
        client_credentials = SpotifyClientCredentials(client_id=config.SPOTIPY_CLIENT_ID,
                                                      client_secret=config.SPOTIPY_CLIENT_SECRET)

        spotify = spotipy.Spotify(client_credentials_manager=client_credentials)
        return spotify
    except SpotifyOauthError as e:
        print('API credentials not set.  Please see README for instructions on setting credentials.')
        sys.exit(1)


def authenticate_user():
    # Same as above, didn't write, and I don't feel like messing with it.
    # Written by
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
        token = sp_util.prompt_for_user_token(username, scope=config.scope,
                                              client_id=config.SPOTIPY_CLIENT_ID,
                                              client_secret=config.SPOTIPY_CLIENT_SECRET,
                                              redirect_uri=config.SPOTIPY_REDIRECT_URI)

        spotify = spotipy.Spotify(auth=token)
        return username, spotify, token

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
