
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

# nltk: Natural Language Toolkit
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# Sentiment analysis
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


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



#-----------------------------------------------------------------------
# TEST
#-----------------------------------------------------------------------

def test():
    # Variables that contain the user credentials to access Twitter API 
    access_token = "999118734320009216-jaE4Rmc6fU11sMmBKb566YTFAJoMPV5"
    access_token_secret = "6ZxqJdK2RU6iridMX1MzSqr3uNpQsC9fv1E6otpZquLiF"
    consumer_key = "Iv6RTiO7Quw3ivH0GWPWqbiD4"
    consumer_secret = "theWmGwcKFG76OtTerxwhrxfX5nSDqGDWB2almLlp2ndRpxACm"
    # trackwords is the list of words that you want to track on Twitter.
    trackwords=['Trump']

    # The computational function that operates on a stream s generated
    # by the source.
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
            print 'text is ', text
            print 'followers_count is ', followers_count
            print 'retweet_count is ', retweet_count
            print 'friends_count is ', friends_count
            print

            ## # convert tweet text to tokens
            ## tokens = word_tokenize(tweet)   

            ## # tweet must be long enough, popular enough, and not a retweet
            ## cleaned_tweet = str()
            ## if (len(tokens) > 5 and 'RT' not in tweet and
            ##     followers_count> 100 and retwee_count > 1):
            ##     print('Tweet:', text)
            ##     print('followers_count:', followers_count) 
            ##     print('retweet_count:', retweet_count)

            ##     sentences = sent_tokenize(text)
            ##     for sentence in sentences:
            ##         # clean sentence
            ##         for tok in word_tokenize(sentence):
            ##             if ('http' in tok or
            ##                 tok[0] not in string.ascii_letters
            ##                 or tok in stop_words):
            ##                 tokens.remove(tok)
            ##             # convert filtered tokens back to text
            ##             cleaned_tweet + untokenize(words)

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
