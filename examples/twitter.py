#Import the necessary methods from tweepy library
#from tweepy.streaming import StreamListener
#from tweepy import OAuthHandler
#from tweepy import Stream
import tweepy
import pprint
import json
import threading

import sys
import os
sys.path.append(os.path.abspath("../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../IoTPy/core"))
sys.path.append(os.path.abspath("../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../IoTPy/multiprocessing"))

import time

from sink import stream_to_file, sink_element
from multicore import single_process_single_source
from stream import Stream
from recent_values import recent_values

#Variables that contains the user credentials to access Twitter API 
access_token = "put your value here"
access_token_secret = "put your value here"
consumer_key = "put your value here"
consumer_secret = "put your value here"

class TwitterTrackwordsToStream(tweepy.streaming.StreamListener):
    """
    Tweets are converted to dictionary objects and placed on a stream.

    Parameters
    ----------
    source_stream: Stream
       The stream on which Tweet dicts are placed.
    trackwords: list of Str
       The list of words in Twitter that are tracked to create this
       stream.
    num_steps: int, optional
       If num_steps is non-zero, then num_steps is the number of
       Tweet dicts placed on source_stream, after which the function
       closes. If num_steps is zero, the class is persistent until
       an error occurs.

    Attributes
    ----------
    ready: threading.Event
        Signals that the setup for Twitter is complete. This is
        helpful to ensure that all source streams start getting
        values at about the same time.
    n: int
       The number of Tweets placed on source_stream so far.

    """

    def __init__(
            self, consumer_key, consumer_secret,
            access_token, access_token_secret,
            trackwords, source_stream, num_steps=0):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.trackwords = trackwords
        self.source_stream = source_stream
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
        the source_stream. Runs forever if num_steps is
        0. Halts after num_steps if it is non-zero.

        """
        try:
            if data is None: return True
            self.source_stream.append(json.loads(data))
            self.n += 1
            if self.num_steps and (self.n >= self.num_steps):
                exit()
            time.sleep(0)
            return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
            exit()

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
        on source_stream.

        """
        self.twitter_stream.filter(track=self.trackwords)


def source_twitter_trackwords(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, stream, time_interval=0, num_steps=0):
    obj = TwitterTrackwordsToStream(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords=trackwords, source_stream=stream, 
        num_steps=num_steps)
    obj.setup()
    return (threading.Thread(target=obj.start),
            obj.ready)


def twitter_trackwords_computation(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, compute_func, time_interval=0, num_steps=0):
    """
    Creates a persistent computation (if num_steps is 0). This
    computation gets a stream of Tweets and executes the function
    compute_func on the stream. If num_steps is non-zero, the
    computation halts after num_steps.

    """
    # Create:
    # (1) s, the stream from the source to the computational
    #     network.
    # (2) The twitter thread and ready (which signals that the
    #     thread is ready).
    # (3) The computation network
    
    s = Stream('source_computation')
    twitter_thread, twitter_ready = source_twitter_trackwords(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, s, time_interval, num_steps)
    compute_func(s)

    # Start and join the twitter thread
    # and the computational thread, Stream.scheduler.
    twitter_thread.start()
    twitter_ready.wait()
    Stream.scheduler.start()
    twitter_thread.join()
    Stream.scheduler.join()
    

def test():
    def compute_func(stream):
        def h(v):
            if 'text' in v:
                print v['text']
        sink_element(func=h, in_stream=stream)

    twitter_trackwords_computation(
        consumer_key="Put your value here",
        consumer_secret="Put your value here",
        access_token="Put your value here",
        access_token_secret="Put your value here",
        trackwords=['Trump'],
        compute_func=compute_func, num_steps=4)

if __name__ == '__main__':
    test()
