# What does this program do?
#
# This program streams Twitter for tweets including a certain keyword.
# That keyword can be any word, hashtag, phrase, emoji, etc.
# The idea is that a user would tweet the keyword along with song lyrics to an unknown song.
# The program takes that input, runs it throught the genius.com API to determine which song it is.
# It then takes the result from Genius and sends it to Spotify to get a URL to the specfic song.
# It then tweets back to the original user with the title and artist of the song, along with the Spotify link.
#

# Function Descriptions
#
# Class MyStreamListener: Listens for the tweets and parses the text to remove the keyword.
#   It then passes the parsed tweet along with the ID of the original tweet and the username of the user sending original tweet.
#
# genisuSearch: Accepts (tweet, id, user). It uses sends the Genius.com search API the tweet. The Genius API returns the title of
#   the song and the name of the artist. The title and the artist are passed to the next function along with the original ID and Username from previous function.
#
# spotifySearch: Accepts (title, artist, id, username). It searches Spotify for (title + artist) and returns a list of the top 3 results.
#   The results are looped through looking for one whose "artist" matches the artist we received from Genius. This is to verify we aren't
#   getting a cover of an original song. If we don't find a matching artist in the first 3 results, we pass along the top result, regardless of artist.
#   We pass along the title, artist, Spotify URL, ID, and Username.
#
# tweetBack: Accepts (title, artist url, id, username). The message back to the original user is being formed. When we get to add the artist's name
#   in the tweet, we call a function which will be described below called findArtistUsername. When the message has been written, we tweet it!
#   It replies in a thread to the original user's tweet.
#
# findArtistUsername: Accepts (artist). This function searches Twitter for the name of artist/band/musician (whatever is returned from Genius). If it can't
#   find a user based on that, it returns the original artist name back. If it does find a result, it stores the username and if the account is verified.
#   If the account is verified, it returns the username of the artist. This is assuming Twitter has found the @ handle of the original artist of the song.
#   If the account is not verified, we once again return back the original artist's name.
#   This is cool because in the message sent back to the user, if the artist has a Twitter, it will tag and link directly to their account.

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


def findArtistUsername(artist):
    users = api.search_users(artist, count=1)

    if (users):
        for user in users:
            artistUsername = (user.screen_name)
            isArtistVerified = (user.verified)
    else:
        return (artist)

    if (isArtistVerified):
        return ('@' + artistUsername)
    else:
        return (artist)


def tweetBack(title, artist, url, id, username):
    message = ""
    if (title == "error"):
        message += ("@" + username)
        message += (" I wasn't able to find the song you were thinking of.")
        message += (" Try tweeting again, with slightly different lyrics.")
    else:
        message += ("@" + username)
        message += (" You might be thinking of " + title)
        message += (" by " + findArtistUsername(artist))
        message += (". You can listen to it here: " + url)
        print(message)
        #api.update_status(status=message, in_reply_to_status_id=id)


def spotifySearch(title, artist, id, username):
    if len(sys.argv) > 1:
        try:
            search_str = sys.argv[1]
        except:
            tweetBack("error", "", "", id, username)
    else:
        try:
            search_str = (title + " " + artist)
        except:
            tweetBack("error", "", "", id, username)

    result = sp.search(search_str, limit=3, market='US', type="track")

    for i in range(3):
        if (result['tracks']['items'][i]['artists'][0]['name']) == artist:
            url = (result['tracks']['items'][i]['external_urls']['spotify'])
            break
        else:
            url = (result['tracks']['items'][0]['external_urls']['spotify'])

    tweetBack(title, artist, url, id, username)


def geniusSearch(tweet, id, username):
    try:
        song = genius.search_song(tweet)
        title = (song.title)
        artist = (song.artist)
        spotifySearch(title, artist, id, username)
    except:
        tweetBack("error", "", "", id, username)


keyword = "when ariana said"


class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):

        id = status.id
        tweet = status.text
        username = status.user.screen_name

        parsedTweet = (tweet.replace(keyword, ''))
        geniusSearch(parsedTweet, id, username)


myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
myStream.filter(track=[keyword])
