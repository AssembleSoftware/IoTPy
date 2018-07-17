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
from sink import sink_element
from stream import Stream
from multicore import single_process_single_source, StreamProcess

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
            self.n += 1
            if self.num_steps and (self.n >= self.num_steps):
                exit()
            # Yield the thread
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
        on out_stream.

        """
        print 'start'
        self.twitter_stream.filter(track=self.trackwords)
        

    def get_thread_object(self):
        self.setup()
        return (threading.Thread(target=self.start),
            self.ready)

def twitter_to_stream(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, out_stream, num_steps):
    obj = TwitterTrackwordsToStream(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, out_stream, num_steps)
    return obj.get_thread_object()

def test():
    # Variables that contain the user credentials to access Twitter API 
    access_token = "put your value here"
    access_token_secret = "put your value here"
    consumer_key = "put your value here"
    consumer_secret = "put your value here"
    # trackwords is the list of words that you want to track on Twitter.
    trackwords=['Trump', 'Clinton']

    # The computational function that operates on a stream s generated
    # by the source.
    def g(s):
        def h(v):
            if 'text' in v: print v['text']
        sink_element(func=h, in_stream=s)

    # The function that generates the source stream.
    def f(s):
        return twitter_to_stream(
            consumer_key, consumer_secret,
            access_token, access_token_secret,
            trackwords, out_stream=s, num_steps=10)

    # Create a single process with a single source
    # specified by function f, and a computational function
    # specified by function g.
    return single_process_single_source(
        source_func=f, compute_func=g)


if __name__ == '__main__':
    test()
