import config

import tweepy
import lyricsgenius
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import sys

auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
api = tweepy.API(auth)

genius = lyricsgenius.Genius(config.genius_token)

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    config.SPOTIPY_CLIENT_ID, config.SPOTIPY_CLIENT_SECRET))

# this takes in an full artist name and searches for it on Twitter. It takes the first result
# a.k.a the most popular account (hopefully) and also checks if that account is verified.
# if account is verified, then it returns the artists' @. if not verified, it returns artist plain name.


def findArtistUsername(artist):
    print(artist)
    users = api.search_users(artist, count=1)

    if (users):
        for user in users:
            artistUsername = (user.screen_name)
            isArtistVerified = (user.verified)
    else:
        return (artist)

    print(artistUsername)
    print(isArtistVerified)

    if (isArtistVerified):
        return ('@' + artistUsername)
    else:
        return (artist)

# this compiles the message that is sent back on Twitter


def tweetBack(title, artist, url, id, username):
    message = ""
    message += ("@" + username)
    message += (" You might be thinking of " + title)
    # the "findArtistUsername" function is described above
    message += (" by " + findArtistUsername(artist))
    message += (". You can listen to it here: " + url)

    print(message)
    api.update_status(status=message, in_reply_to_status_id=id)

# this takes the info and finds the Spotify URL


def spotifySearch(title, artist, id, username):
    if len(sys.argv) > 1:
        search_str = sys.argv[1]
    else:
        search_str = (title + " " + artist)

    # shows the top 3 results based on the title and artist from Genius
    result = sp.search(search_str, limit=3, market='US', type="track")

    # looks at the 3 and determines which one's artist is the correct one.
    # problem was it was finding covers instead of originals
    for i in range(3):
        if (result['tracks']['items'][i]['artists'][0]['name']) == artist:
            url = (result['tracks']['items'][i]['external_urls']['spotify'])
            break
        else:
            url = (result['tracks']['items'][0]['external_urls']['spotify'])

    # sends the title, artist, url, og tweet id, og tweeter handle
    tweetBack(title, artist, url, id, username)

# this takes the tweet and sends it through to Genius to determine the song title and artist


def geniusSearch(tweet, id, username):
    song = genius.search_song(tweet)
    title = (song.title)
    artist = (song.artist)
    #print(title + " by " + artist)
    # sends the title and artst of the song as well as the id of the original tweet and original tweeter
    spotifySearch(title, artist, id, username)


# this streams live tweets that include the keyword defined below

keyword = "#SongLookup"


class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):

        # get user ID, tweet string, and username handle
        id = status.id
        tweet = status.text
        username = status.user.screen_name

        # cleans tweet of search keywords
        parsedTweet = (tweet.replace(keyword, ''))
        # sends the tweet without the keyword, ID of the original tweet and the username of the original tweeter
        geniusSearch(parsedTweet, id, username)


myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
myStream.filter(track=[keyword])
