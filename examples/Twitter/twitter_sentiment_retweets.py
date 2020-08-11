import re
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
from IoTPy.agent_types.sink import sink_element, stream_to_file
from IoTPy.agent_types.op import map_window, map_element
from IoTPy.agent_types.merge import zip_stream
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.concurrency.multicore import get_processes
from IoTPy.concurrency.multicore import get_processes_and_procs
from IoTPy.concurrency.multicore import extend_stream, terminate_stream
import ctypes

from examples.Twitter.twitter import twitter_to_stream, twitter_analysis, check_Twitter_credentials

from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Written by Tommy Hannan

## # variables that contain the user credentials to access Twitter API 
## access_token = "Enter Your Access Token"
## access_token_secret = "Enter Your Access Token Secret"
## consumer_key = "Enter Your Consumer Key"
## consumer_secret = "Enter Your Consumer Secret"


# Variables that contain the user credentials to access Twitter API
# Enter your values here
access_token = " "
access_token_secret = " "
consumer_key = " "
consumer_secret = " "

# HELPER FUNCTIONS FOR DEALING WITH TWEETS
def get_text(tweet):
    """
    Helper function that retrieves full text of tweet from dictionary

    Parameters
    ----------
        tweet: (dict)
           data for individual tweet

    Returns
    -------
        text (str)
           non-abbreviated text of tweet
    """

    text = str()

    # search tweet dictionary to see if extended tweet is available
    if 'extended_tweet' in str(tweet):
        if 'extended_tweet' in tweet.keys():
            text = tweet['extended_tweet']['full_text']
        else:
            if 'retweeted_status' in tweet.keys():
                if 'extended_tweet' in str(tweet['retweeted_status']):
                    if 'extended_tweet' in tweet['retweeted_status'].keys():
                        text = (tweet
                                    ['retweeted_status']
                                    ['extended_tweet']
                                    ['full_text'])
                    else:
                        if 'quoted_status' in (tweet
                                                   ['retweeted_status']
                                               ).keys():
                            if 'extended_tweet' in (tweet
                                                        ['retweeted_status']
                                                        ['quoted_status']
                                                    ).keys():
                                text = (tweet
                                            ['retweeted_status']
                                            ['quoted_status']
                                            ['extended_tweet']
                                            ['full_text'])   
    else:
        try:
            text = tweet['text']
        except:
            pass

    # clean text
    text = (text.replace('&amp', 'and')
               .replace('\n', ' ')
               .replace('RT ', ''))
    text = re.sub(r'http\S+', '', text)

    return text
        
def followers_and_retweets_of_tweet(tweet):
    """
    Function that retrieves number of followers of account 
    that posted tweet and the number of times that tweet was
    retweeted

    Parameters
    ----------

       tweet: dict
          data for individual tweet

    Returns
    -------
       followers: int
          numbers of followers
       retweets: int
          number of retweets
    """

    # search tweet dictionary for follower count
    followers = 0
    if 'user' in str(tweet):
        if 'followers_count' in str(tweet['user']):
            followers = tweet['user']['followers_count']

    # search tweet dictionary for retweet count
    retweets = 0
    if 'retweeted_status' in str(tweet):
        if 'retweet_count' in str(tweet['retweeted_status']):
            retweets = tweet['retweeted_status']['retweet_count']

    return followers, retweets         

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

    # create sentiment analyzer and computer value
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)['compound']

    return sentiment
    
def print_sentiment_followers_retweets(tweet):
    """      
    Detailed test containing functions for retrieving and analyzing
    data for each tweet      
    """
    # thresholds that a tweet must meet in order to be
    # considered for sentiment analysis
    follower_limit = 5
    retweet_limit = 1

    # get important data from helper functions
    text = get_text(tweet)        
    sentiment = sentiment_of_text(text)
    followers, retweets = followers_and_retweets_of_tweet(tweet)

    # save sentiment value to text file for graphing
    # and analysis.
    output = open('twitter_sentiment.txt', 'a')
    output.write(str(sentiment))
    output.write('\n')
    output.close          

    # ensures that analyzed tweets meet desired thresholds
    if followers >= follower_limit and retweets >= retweet_limit: 
        print('\nTweet: ' + text + '\n') 
        print('Sentiment: ' + str(sentiment)) 
        print('Followers: ' + str(followers) + 
              ', Retweets: ' + str(retweets) + '\n')

if __name__ == '__main__':
    twitter_analysis(consumer_key, consumer_secret,
                     access_token, access_token_secret,
                     trackwords=['Trump'],
                     tweet_analyzer=print_sentiment_followers_retweets,
                     num_tweets=10)
