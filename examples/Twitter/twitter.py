import pprint
import json
import threading
import time
# Tweepy is an open source free Python library for Twitter.
# http://www.tweepy.org/
import tweepy
# The Natural Language ToolKit
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# Sentiment analysis
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, run
from IoTPy.agent_types.sink import sink_element
from IoTPy.agent_types.merge import weave
from IoTPy.agent_types.op import map_window, map_element, filter_element
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.helper_functions.print_stream import print_stream
from IoTPy.concurrency.multicore import get_processes
from IoTPy.concurrency.multicore import get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream, extend_stream
import ctypes



# Create sentiment analyzer to compute sentiments of tweets.
sentiment_analyzer = SentimentIntensityAnalyzer()

#-----------------------------------------------------------------
# Variables that contain the user credentials to access Twitter API
# Create your own variables.

## access_token = ""
## access_token_secret = ""
## consumer_key = ""
## consumer_secret = ""

access_token = "999118734320009216-jaE4Rmc6fU11sMmBKb566YTFAJoMPV5"
access_token_secret = "6ZxqJdK2RU6iridMX1MzSqr3uNpQsC9fv1E6otpZquLiF"
consumer_key = "Iv6RTiO7Quw3ivH0GWPWqbiD4"
consumer_secret = "theWmGwcKFG76OtTerxwhrxfX5nSDqGDWB2almLlp2ndRpxACm"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
#-----------------------------------------------------------------
def check_Twitter_credentials():
    """
    Verify your Twitter credentials.

    """
    try:
        api.verify_credentials()
        print("Authentication OK")
    except:
        print("Error during authentication")

#-----------------------------------------------------------------
class TwitterTrackwordsToStream(tweepy.streaming.StreamListener):
    """
    Tweets are converted to dictionary objects and placed on a stream.

    Parameters
    ----------
    out_stream: Stream
       The stream on which Tweet dicts are placed.
    trackwords: list of Str
       The list of words in Twitter that are tracked to create this
       stream.
    num_tweets: int, optional
       If num_tweets is non-zero, then num_tweets is the number of
       Tweet dicts placed on out_stream, after which the function
       closes. If num_tweets is zero, the class is persistent until
       an error occurs.
    proc: 

    Attributes
    ----------
    ready: threading.Event
        Signals that the setup for Twitter is complete. This is
        helpful to ensure that all source streams start getting
        values at about the same time.
    n: int
       The number of Tweets placed on out_stream so far.

    """

    def __init__(
            self, consumer_key, consumer_secret,
            access_token, access_token_secret,
            trackwords, stream_name, procs, num_tweets=0):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.trackwords = trackwords
        self.stream_name = stream_name
        self.num_tweets = num_tweets
        self.procs = procs
        self.ready = threading.Event()
        self.n = 0
        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def on_error(self, status):
        """
        Call back by Twitter

        """
    def on_status(self, status):
        """
        This function is a callback by Twitter.

        """
        # Check empty status
        if status is None: return

        # Get extended text if it exists.
        if hasattr(status, 'retweeted_status'):
            try:
                tweet_text = status.retweeted_status.extended_tweet["full_text"]
            except:
                tweet_text = status.retweeted_status.text
        else:
            try:
                tweet_text = status.extended_tweet["full_text"]
            except AttributeError:
                tweet_text = status.text

        #-----------------------------------------------
        # Get data from the status object. data is a dict.
        data = status._json
        # Add the extended text as a separate key-value pair to
        # data.
        data['tweet_text'] = tweet_text
        try:
            # Put the tweet into the stream called stream_name.
            extend_stream(self.procs, [data], self.stream_name)
            # Increment the number of times data is copied into the stream
            self.n += 1
            # Exit if enough steps have completed. 
            # Don't stop if self.num_tweets is None.
            if self.num_tweets and (self.n >= self.num_tweets):
                terminate_stream(self.procs, self.stream_name)
                sys.exit()
            # Yield the thread
            time.sleep(0.0001)
            return True
        except BaseException as e:
            print (' ')
            if not e or str(e) == '':
                print ('No data from Twitter')
            else:
                print("Error on_data from Twitter: %s" % str(e))
                print ("See TwitterTrackwordsToStream.on_data()")
            print (' ')
            sys.exit()


    def setup(self):
        """
        Sets up the connection to Twitter. You must get
        consumer_key, consumer_secret, access_token, and
        access_token_secret from Twitter. See tweepy.

        """
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_token_secret)
        self.twitter_stream = tweepy.Stream(self.auth, self)
        self.ready.set()

    def start(self):
        """
        This is the thread target. This thread will put Tweets
        on out_stream.

        """
        self.twitter_stream.filter(track=self.trackwords, languages=['en'])

    def get_thread_object(self):
        self.setup()
        return threading.Thread(target=self.start)

#-----------------------------------------------------------------
def twitter_to_stream(
        consumer_key, consumer_secret, access_token, access_token_secret,
        trackwords, stream_name, procs, num_tweets):
    """
                      
    Get Tweets from Twitter and put them on out_stream.

    Parameters
    ----------
       consumer_key, consumer_secret: str
           Credentials that you must establish on Twitter
       access_token, access_token_secret: str
           Credentials that you must establish on Twitter
       trackwords: list of str
           The list of words that you want to track on Twitter.
       stream_name: str
           Tweets are placed as dicts on this output stream.
       procs: dict
           Generated by get_procs
       num_tweets: int, optional
           The number of Tweets that are obtained.
           If left unspecified then the agent does not stop
           execution.
    Returns
    -------
        thread
        The thread that puts tweets into the stream with name stream_name.

    """
    obj = TwitterTrackwordsToStream(
        consumer_key, consumer_secret, access_token, access_token_secret,
        trackwords, stream_name, procs, num_tweets)
    return obj.get_thread_object()

def get_tweet_fields(tweet, fields=None):
    """
    This function retains only those parts of tweet that are
    specified in fields.

    Parameters
    ----------
    tweet: dict
       A JSON loaded tweet object.
    fields: dict
       field is a dict. A key of field is either '-' or a string
       that is a key of the tweet.
       An example of fields:
            {'-': ['created_at', 'text'],
             'user': ['name', 'followers_count', 'friends_count'],
             'coordinates': ['coordinates'],
             'place': ['country', 'full_name'],
             'entities':['hashtags'],
             }
       'user', 'coordinates', ... are keys of a tweet.
       The value for a given key of fields is a list of strings.
       In the above example, the value for key 'user' in fields is
       the list:
           ['name', 'followers_count', 'friends_count'].
       Each of the elements in the list will be extracted from the
       tweet.
    Returns
    -------
      result: dict
        result retains only those fields of the tweet that are
        specified in fields.
        In the above example, the result will have keys for
        'created_at' and 'text', and also for
        'user', and result['user'] is also a dict and 'name' is
        a key in result['user'].

    """
    result = {}
    if fields == None:
        return tweet
    for key in fields.keys():
        if key == '-':
            # This is the top-level field in a tweet.
            # Examples are 'created_at' and 'text'.
            for subfield in fields['-']:
                # Special treatment for 'sentiment' because it is not
                # part of a tweet. It has to be computed from the
                # text.
                if subfield == 'sentiment':
                    continue
                if subfield in tweet.keys():
                    # Special situation for 'text'. Get
                    # 'extended_tweet' if it is in the tweet.
                    if subfield == 'text':
                        if 'tweet_text' in tweet.keys():
                            # In this case, the extended tweet has been
                            # already obtained by on_status, and entered
                            # into the tweet with the key: 'tweet_text'.
                            text = tweet['tweet_text']
                        elif 'extended_tweet' in tweet.keys():
                            text = tweet['extended_tweet']['full_text']
                        else:
                            text = tweet['text']
                        result['text'] = text
                    else:
                        result[subfield] = tweet[subfield]
        else:
            # This is a lower-level field in a tweet.
            # Examples are 'user'['name']. In this example, 'user is in
            # tweet.keys(), and 'name' is a category in the list
            # fields['user']
            if key in tweet.keys():
                result[key] = {}
                for category in fields[key]:
                    if tweet[key] and (type(tweet[key]) == dict):
                        if category in tweet[key].keys():
                            result[key][category] = tweet[key][category]
                    else:
                        result[key][category] = None

    # Special case where subfield is 'sentiment'.
    if '-' in fields.keys():
        if 'sentiment' in fields['-']:
            sentiment = sentiment_of_text(result['text'])
            # Add sentiment to result
            result['sentiment'] = sentiment
    return result
                        
#-----------------------------------------------------------------
def print_tweets(tweet):
    """
    Print tweets nicely.

    """
    print ('---------------------------------------')
    for key, value in tweet.items():
        if type(value) == dict:
            print (' ')
            print ('    ' + key)
            for k, v in value.items():
                if type(v) == dict:
                    print (' ')
                    print (k)
                    for kk, vv in v.items():
                        print (' ')
                        print ('    ' + str(kk) + ' : ' + str(vv))
                else:
                    print ('    ' + str(k) + ' : ' + str(v))
        else:
            print ('    ' + str(key) + ' : ' + str(value))
    print ('---------------------------------------')
    print (' ')


def filter_tweet(tweet, required_phrases, avoid_phrases=[]):
    """
    Filter that keeps tweets that have at least one required phrase
    and does not have any of the avoid phrases.

    Parameters
    ----------
    required_phrases: list of str
       list of required phrases
    avoid_phrases: list of str
       list of phrases that must not be in relevant tweet.

    """
    tweet_text = tweet['text']
    # If the required phrase is NOT in the text then
    # return False.
    required_phrase_in_text = False
    for required_phrase in required_phrases:
        if required_phrase in tweet_text:
            # This text has at least one required phrase.
            required_phrase_in_text = True
            break
    if not required_phrase_in_text:
        # This text has no required phrases.
        return False

    # If one or more of the avoid phrases is in the
    # text then return False.
    avoid_phrase_in_text = False
    for avoid_phrase in avoid_phrases:
        if avoid_phrase in tweet_text:
            # At least one avoid phrase is in the text.
            avoid_phrase_in_text = True
            break
    if avoid_phrase_in_text:
        return False
    #
    # Text has at least one required phrase and has none
    # of the avoid phrases. So, return True
    return True

def sentiment_of_text(text):
    """
    Helper function that analyzes sentiment of a tweet

    Parameters
    ----------
       text: str
          cleaned text of tweet

    Returns
    -------
        sentiment: float
           sentiment ranging from -1.0 (negative) to
           1.0 (positive)
    """
    sentiment = sentiment_analyzer.polarity_scores(text)['compound']

    return sentiment
    
#-----------------------------------------------------------------
"""
The next example shows how tweets are used with multiple processes.
The first two processes get streams of tweets and carry out analyses on them.
The third process merely joins the two steams and prints the joined stream.

This multicore application has the following streams between processes.
(See multicore_specification. Streams)
['TrumpStream', 'CovidStream', TrumpFiltered', 'CovidFiltered']
Each stream is of type 'x' which indicates that the stream is not a ctype
such as int (represented as 'i') or a double (represented as 'd'). In this
case the stream elements are dicts which are not a c type; so we use 'x' as
its type.

This application has three processes called 'TrumpProcess', 'CovidProcess'
and 'FuseProcess'.

TrumpProcess has a single input stream called 'TrumpStream'.
A source thread called 'source_thread_Trump' feeds the source 'TrumpStream'.
The specification for TrumpProcess identifies TrumpStream as an input of
the process and also as a source that runs in the same process.

TrumProcess has a map_element agent which extracts the specified fields
from each tweet.
The output of the map_element agent is fed to a filter_element agent which
filters tweets to have at least one of the required phrases and none of the
avoid phrases.
The output of filter_tweets is out_stream[0] which is given the name
'TrumpFiltered'.

CovidProcess is identical to TrumpProcess except that it has different fields and
different filters.

The FuseProcess gets weaves the two input streams into a single stream and
prints the results.
"""

def twitter_analysis(consumer_key, consumer_secret, access_token, access_token_secret):
    # Agent function for process named 'TrumpProcess'
    def f(in_streams, out_streams):
        s = Stream('s')
        t = Stream('t')
        map_element(
            get_tweet_fields, in_streams[0], out_stream=s,
            fields={'-': ['text', 'created_at', 'sentiment'],
                    'user':['name', 'screen_name', 'description',
                            'favorites_count', 'followers_count']})
        filter_element(filter_tweet, in_stream=s, out_stream=out_streams[0],
                       required_phrases=['Biden'],
                       avoid_phrases=['#MAGA', '@thedemocrat', 'stable genius'])

    # Agent function for process named 'CovidProcess'
    def g(in_streams, out_streams):
        s = Stream('s')
        t = Stream('t')
        map_element(
            get_tweet_fields, in_streams[0], out_stream=s,
            fields={'-': ['text', 'sentiment'],
                    'user':['name', 'screen_name', 'description',
                            'favorites_count', 'followers_count']})
        filter_element(filter_tweet, in_stream=s, out_stream=out_streams[0],
                       required_phrases=['covid', 'vaccine', 'Fauci', 'Birks'],
                       avoid_phrases=['evil'])

    # Agent function for process named 'FuseTweets'
    def h(in_streams, out_streams):
        s = Stream('s')
        weave(in_streams, out_stream=s)
        sink_element(print_tweets, s)

    multicore_specification = [
        # Streams
        [('TrumpStream', 'x'), ('CovidStream', 'x'), ('TrumpFiltered', 'x'),  ('CovidFiltered', 'x')],
        # Processes
        [{'name': 'TrumpProcess', 'agent':f, 'inputs':['TrumpStream'], 'sources':['TrumpStream'],
          'outputs': ['TrumpFiltered']},
         {'name': 'CovidProcess', 'agent':g, 'inputs':['CovidStream'], 'sources':['CovidStream'],
          'outputs': ['CovidFiltered']},
         {'name': 'FuseTweets', 'agent':h, 'inputs':['TrumpFiltered', 'CovidFiltered']}]
        ]

    # PROCESSES
    processes, procs = get_processes_and_procs(multicore_specification)
    # SOURCE THREADS
    source_thread_Trump = twitter_to_stream(
        consumer_key, consumer_secret, access_token, access_token_secret,
        trackwords=['Trump'], stream_name='TrumpStream', procs=procs, num_tweets=50)
    
    source_thread_Covid = twitter_to_stream(
        consumer_key, consumer_secret, access_token, access_token_secret,
        trackwords=['Covid'], stream_name='CovidStream', procs=procs, num_tweets=20)

    procs['TrumpProcess'].threads = [source_thread_Trump]
    procs['CovidProcess'].threads = [source_thread_Covid]

    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

#-----------------------------------------------------------------------
# TEST
#-----------------------------------------------------------------------

if __name__ == '__main__':
    check_Twitter_credentials()
    print ('Finished checking Twitter credentials')
                                    
    twitter_analysis(
        consumer_key, consumer_secret, access_token, access_token_secret)

