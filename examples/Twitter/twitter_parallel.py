#import re
import pprint
import json
import threading
import time
# Tweepy is an open source free Python library for Twitter.
# http://www.tweepy.org/
import tweepy
# The Natural Language ToolKit
import nltk
#nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# Sentiment analysis
from nltk.sentiment.vader import SentimentIntensityAnalyzer

import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, run
from IoTPy.agent_types.sink import sink_element, stream_to_file
from IoTPy.agent_types.op import map_window, map_element
from IoTPy.agent_types.merge import zip_stream
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.concurrency.multicore import get_processes
from IoTPy.concurrency.multicore import get_processes_and_procs
from IoTPy.concurrency.multicore import extend_stream, terminate_stream
from IoTPy.helper_functions.print_stream import print_stream

from examples.Twitter.twitter import twitter_to_stream, twitter_analysis, check_Twitter_credentials
from examples.Twitter.twitter_sentiment_retweets import get_text
from examples.Twitter.twitter_sentiment_retweets import followers_and_retweets_of_tweet
from examples.Twitter.twitter_sentiment_retweets import sentiment_of_text

#-----------------------------------------------------------------
# Variables that contain the user credentials to access Twitter API
# Create your own variables.
access_token = ""
access_token_secret = ""
consumer_key = ""
consumer_secret = ""

def twitter_parallel(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, num_steps):
    def copy_input_to_output(in_streams, out_streams):
        map_element(lambda x: x, in_streams[0], out_streams[0])

    def output_tweet_sentiment(in_streams, out_streams):
        def get_sentiment(tweet):
            return sentiment_of_text(get_text(tweet))
        map_element(get_sentiment, in_streams[0], out_streams[0])
        print_stream(out_streams[0], 'sentiment')
    
    def output_followers_retweets(in_streams, out_streams):
        map_element(
            followers_and_retweets_of_tweet, in_streams[0], out_streams[0])
        print_stream(out_streams[0], 'followers')

    def zip_everything_and_file(in_streams, out_streams):
        t = Stream()
        zip_stream(in_streams, out_stream=t)
        print_stream(t, 'zipped')
        stream_to_file(in_stream=t, filename='result.dat')

    multicore_specification = [
        # Streams
        [('source', 'x'), ('raw_tweets', 'x'),
         ('tweet_sentiment', 'x'), ('followers_and_retweets', 'x')],
        # Processes
        [
            {'name': 'get_raw_tweets', 'agent': copy_input_to_output,
             'inputs':['source'], 'outputs':['raw_tweets'],
            'sources':['source']},
            {'name': 'get_tweet_sentiment', 'agent': output_tweet_sentiment,
             'inputs':['raw_tweets'], 'outputs':['tweet_sentiment']},
            {'name': 'get_followers_and_retweets', 'agent': output_followers_retweets,
             'inputs':['raw_tweets'], 'outputs':['followers_and_retweets']},
            {'name': 'put_results_in_file', 'agent': zip_everything_and_file,
             'inputs':['tweet_sentiment', 'followers_and_retweets']}
        ]
    ]

    # PROCESSES
    processes, procs = get_processes_and_procs(multicore_specification)
    stream_name = 'source'
    get_tweets_thread = twitter_to_stream(
        consumer_key, consumer_secret, access_token, access_token_secret,
        trackwords, stream_name, procs, num_steps)
    procs['get_raw_tweets'].threads = [get_tweets_thread]

    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

if __name__ == '__main__':
    twitter_parallel(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords=['Trump'], num_steps=3)
