import sys
import os
import re
import tweepy
import json
import threading

from nltk.sentiment.vader import SentimentIntensityAnalyzer

sys.path.append(os.path.abspath('../../IoTPy/agent_types'))
sys.path.append(os.path.abspath('../../IoTPy/multiprocessing'))
sys.path.append(os.path.abspath('../../IoTPy/core'))
sys.path.append(os.path.abspath('../../IoTPy/helper_functions'))
from stream import Stream
from multicore import shared_memory_process, Multiprocess
from sink import sink_element, stream_to_file
from op import map_element
from merge import zip_stream
from twitter import twitter_to_stream, twitter_analysis

from twitter_sentiment_retweets import get_text
from twitter_sentiment_retweets import followers_and_retweets_of_tweet
from twitter_sentiment_retweets import sentiment_of_text

# Variables that contain the user credentials to access Twitter API 
access_token = "999118734320009216-jaE4Rmc6fU11sMmBKb566YTFAJoMPV5"
access_token_secret = "6ZxqJdK2RU6iridMX1MzSqr3uNpQsC9fv1E6otpZquLiF"
consumer_key = "Iv6RTiO7Quw3ivH0GWPWqbiD4"
consumer_secret = "theWmGwcKFG76OtTerxwhrxfX5nSDqGDWB2almLlp2ndRpxACm"

def twitter_parallel(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, num_steps):
    
    # PROCESS 0
    def source(out_stream):
        return twitter_to_stream(
            consumer_key, consumer_secret,
            access_token, access_token_secret,
            trackwords, out_stream, num_steps)
    def compute_func_0(in_streams, out_streams):
        map_element(lambda x: x, in_stream=in_streams[0],
                    out_stream=out_streams[0])
    proc_0 = shared_memory_process(
        compute_func=compute_func_0,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[('in', source)],
        name='proc_0')

    # PROCESS 1
    def compute_func_1(in_streams, out_streams):
        def get_sentiment(tweet):
            tweet_text = get_text(tweet)
            sentiment_of_tweet = sentiment_of_text(tweet_text)     
            return (tweet_text, sentiment_of_tweet)
        map_element(
            func=get_sentiment,
            in_stream=in_streams[0],
            out_stream=out_streams[0])
    proc_1 = shared_memory_process(
        compute_func=compute_func_1,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='proc_1')

    # PROCESS 2
    def compute_func_2(in_streams, out_streams):
        map_element(
            func=followers_and_retweets_of_tweet,
            in_stream=in_streams[0],
            out_stream=out_streams[0])
    proc_2 = shared_memory_process(
        compute_func=compute_func_2,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='proc_2')

    # PROCESS 3
    def compute_func_3(in_streams, out_streams):
        t = Stream()
        zip_stream(in_streams, out_stream=t)
        stream_to_file(in_stream=t, filename='result.dat')
    proc_3 = shared_memory_process(
        compute_func=compute_func_3,
        in_stream_names=['in_1', 'in_2'],
        out_stream_names=[],
        connect_sources=[],
        name='proc_3')

    mp = Multiprocess(
        processes=[proc_0, proc_1, proc_2, proc_3],
        connections=[(proc_0, 'out', proc_1, 'in'),
                     (proc_0, 'out', proc_2, 'in'),
                     (proc_1, 'out', proc_3, 'in_1'),
                     (proc_2, 'out', proc_3, 'in_2')])
    mp.run()

if __name__ == '__main__':
    twitter_parallel(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords=['Trump'], num_steps=10)
    
