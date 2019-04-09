
import tweepy
import pprint
import json
import threading

import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))

import time
from sink import sink_element
from stream import Stream
from multicore import single_process_single_source

# nltk: Natural Language Toolkit.
# open source, free toolkit
# https://www.nltk.org/
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# Sentiment analysis
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# You should also download Tweepy, an open source, free
# Python library for Twitter.
# http://www.tweepy.org/


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
            trackwords, out_stream, num_steps=0):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.trackwords = trackwords
        self.out_stream = out_stream
        self.num_steps = num_steps
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

            # Put the data in the scheduler's input queue
            Stream.scheduler.input_queue.put(
                (self.out_stream.name, json.loads(data)))
            # Increment the number of puts into the queue
            self.n += 1
            # Exit if enough steps have completed.
            if self.num_steps and (self.n >= self.num_steps):
                sys.exit()
            # Yield the thread
            time.sleep(0)
            return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
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
        self.twitter_stream.filter(track=self.trackwords)
        

    def get_thread_object(self):
        self.setup()
        return threading.Thread(target=self.start)

def twitter_to_stream(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, out_stream, num_steps):
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
       out_stream: Stream
           Tweets are placed as dicts on this output stream.
       num_steps: int, optional
           The number of Tweets that are obtained.
           If left unspecified then the agent does not stop
           execution.

    """
    obj = TwitterTrackwordsToStream(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, out_stream, num_steps)
    return obj.get_thread_object()


def print_text_followers_retweet_friends(
        trackwords, num_steps):
    # Variables that contain the user credentials to access Twitter API 
    access_token = "ENTER YOUR CREDENTIALS"
    access_token_secret = "ENTER YOUR CREDENTIALS"
    consumer_key = "ENTER YOUR CREDENTIALS"
    consumer_secret = "ENTER YOUR CREDENTIALS"
    # trackwords is the list of words that you want to track on Twitter.
    trackwords=['Trump']

    # The computational function that operates on an input stream, s,
    # which is generated by the source.
    def g(s):
        def h(tweet):
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
            print 'Text is: ', text
            print
            print 'followers_count is: ', followers_count
            print 'retweet_count is: ', retweet_count
            print 'friends_count is: ', friends_count
            print '--------------------------------------'
            print

        sink_element(func=h, in_stream=s)

    # The function that generates the source stream.
    def f(stream):
        return twitter_to_stream(
            consumer_key, consumer_secret,
            access_token, access_token_secret,
            trackwords, out_stream=stream, num_steps=num_steps)

    # Create a single process with a single source
    # specified by function f, and a computational function
    # specified by function g.
    return single_process_single_source(
        source_func=f, compute_func=g)


#-----------------------------------------------------------------------
# TEST
#-----------------------------------------------------------------------

if __name__ == '__main__':
    print_text_followers_retweet_friends(
        trackwords=['Trump'], num_steps=5)
