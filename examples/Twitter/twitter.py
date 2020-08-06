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
from IoTPy.agent_types.op import map_window
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.concurrency.multicore import get_processes
from IoTPy.concurrency.multicore import get_processes_and_procs
from IoTPy.concurrency.multicore import extend_stream, terminate_stream
import ctypes

#-----------------------------------------------------------------
# Variables that contain the user credentials to access Twitter API
# Create your own variables.
access_token = "999118734320009216-jaE4Rmc6fU11sMmBKb566YTFAJoMPV5"
access_token_secret = "6ZxqJdK2RU6iridMX1MzSqr3uNpQsC9fv1E6otpZquLiF"
consumer_key = "Iv6RTiO7Quw3ivH0GWPWqbiD4"
consumer_secret = "theWmGwcKFG76OtTerxwhrxfX5nSDqGDWB2almLlp2ndRpxACm"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
#-----------------------------------------------------------------
def check_Twitter_credentials():
    try:
        api.verify_credentials()
        print("Authentication OK")
    except:
        print("Error during authentication")

    # Get the User object for twitter...
    user = api.get_user('twitter')
    print (user.followers_count)
    for friend in user.friends():
       print (friend.screen_name)


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
    num_steps: int, optional
       If num_steps is non-zero, then num_steps is the number of
       Tweet dicts placed on out_stream, after which the function
       closes. If num_steps is zero, the class is persistent until
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
            trackwords, stream_name, procs, num_steps=0):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.trackwords = trackwords
        self.stream_name = stream_name
        self.num_steps = num_steps
        self.procs = procs
        self.ready = threading.Event()
        self.n = 0

    def on_error(self, status):
        """
        Call back by Twitter

        """
        print(status)

    def on_data(self, data):
        """
        Call back by Twitter.
        Appends a dict object containing the Tweet to
        the out_stream. Runs forever if num_steps is
        0. Halts after num_steps if it is non-zero.

        """
        try:
            if data is None: return True
            #Stream.scheduler.input_queue.put((self.stream_name, json.loads(data)))
            print ('data is:')
            print (data)
            #data = bytes(data, 'utf-8')
            #extend_stream(self.procs, [data], self.stream_name)
            extend_stream(self.procs, data, self.stream_name)
            # Increment the number of times data is copied into the stream
            self.n += 1
            # Exit if enough steps have completed. 
            # Don't stop if self.num_steps is None.
            if self.num_steps and (self.n >= self.num_steps):
                print ('FINISHED')
                print ('----------------------------')
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
        print ('in class. in start()')
        self.twitter_stream.filter(track=self.trackwords)

    def get_thread_object(self):
        self.setup()
        return threading.Thread(target=self.start)

#-----------------------------------------------------------------
def twitter_to_stream(
        consumer_key, consumer_secret, access_token, access_token_secret,
        trackwords, stream_name, procs, num_steps):
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
       num_steps: int, optional
           The number of Tweets that are obtained.
           If left unspecified then the agent does not stop
           execution.

    """
    print ('twitter to stream')
    obj = TwitterTrackwordsToStream(
        consumer_key, consumer_secret, access_token, access_token_secret,
        trackwords, stream_name, procs, num_steps)
    return obj.get_thread_object()

#-----------------------------------------------------------------
def print_tweets(tweet):
    print ('in print_tweets 1')
    print ('tweet is ')
    print (tweet)
    tweet = json.loads(tweet)
    print ('in print_tweets 2')
    print ('tweet is ')
    print (tweet)
    if 'extended_tweet' in tweet:
        text = tweet['extended_tweet']['full_text']
    elif 'text' in tweet:
        text = tweet['text']
    else:
        text = str()
    followers_count = 0
    retweet_count = 0
    if 'user' in tweet:
        tweet_user = tweet['user']
        if 'followers_count' in tweet_user:
            followers_count = tweet_user['followers_count']
        if 'friends_count' in tweet_user:
            friends_count = tweet_user['friends_count']
    if 'retweet_count' in tweet:
        retweet_count = tweet['retweet_count']

    # print output
    print ('Text is: ', text)
    print (' ')
    print ('followers_count is: ', followers_count)
    print ('retweet_count is: ', retweet_count)
    print ('friends_count is: ', friends_count)
    print ('--------------------------------------')
    print (' ')

#-----------------------------------------------------------------
def twitter_analysis(
        consumer_key, consumer_secret, access_token, access_token_secret,
        trackwords, tweet_analyzer, stream_name, num_tweets):
    print ('twitter_analysis')
    # Agent function for process named 'p0'
    def f(in_streams, out_streams):
        s = Stream('s')
        def convert_bytes_to_string(window):
            return_value = ''.join(window)
            print ('return_value is', return_value)
            return str(return_value)
        map_window(
            func=convert_bytes_to_string, in_stream=in_streams[0], out_stream=s,
            window_size=2000, step_size=2000)
        print(recent_values(s))

    multicore_specification = [
        # Streams
        [('x', ctypes.c_wchar)],
        # Processes
        [{'name': 'p0', 'agent': f, 'inputs':['x'], 'sources':['x']}]]

    # PROCESSES
    processes, procs = get_processes_and_procs(multicore_specification)
    print ('source_thread')
    source_thread = twitter_to_stream(
        consumer_key, consumer_secret, access_token, access_token_secret,
        trackwords, stream_name, procs, num_tweets)

    procs['p0'].threads = [source_thread]

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
    consumer_key, consumer_secret, access_token, access_token_secret,
    trackwords=['Trump'], tweet_analyzer=print_tweets, stream_name='x', num_tweets=3)

