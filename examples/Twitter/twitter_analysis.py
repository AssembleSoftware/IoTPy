import sys
import os
import re

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from twitter import twitter_to_stream

from multicore import single_process_single_source
from sink import sink_element

sys.path.append(os.path.abspath('../agent_types'))
sys.path.append(os.path.abspath('../multiprocessing'))

## # variables that contain the user credentials to access Twitter API 
## access_token = "Enter Your Access Token"
## access_token_secret = "Enter Your Access Token Secret"
## consumer_key = "Enter Your Consumer Key"
## consumer_secret = "Enter Your Consumer Secret"


# Variables that contain the user credentials to access Twitter API 
access_token = "999118734320009216-jaE4Rmc6fU11sMmBKb566YTFAJoMPV5"
access_token_secret = "6ZxqJdK2RU6iridMX1MzSqr3uNpQsC9fv1E6otpZquLiF"
consumer_key = "Iv6RTiO7Quw3ivH0GWPWqbiD4"
consumer_secret = "theWmGwcKFG76OtTerxwhrxfX5nSDqGDWB2almLlp2ndRpxACm"


def twitter_analysis(consumer_key, consumer_secret,
                     access_token, access_token_secret,
                     trackwords, compute_func, num_steps):
    """
    Get Tweets from Twitter and execute compute_func on each Tweet.

    Parameters
    ----------
       consumer_key, consumer_secret: str
           Credentials that you must establish on Twitter
       access_token, access_token_secret: str
           Credentials that you must establish on Twitter
       trackwords: list of str
           The list of words that you want to track on Twitter.
       compute_func: function with a single parameter - a stream.
           The function executed on each Tweet.
       num_steps: int
           The number of Tweets that are obtained.

    Notes
    -----
       This function has three steps:
       (1): Define a computational function, g(s), for input stream s.
       (2): Define a source function, f(s), for output stream s.
       (3): Create an agent using the wrapper
            single_process_single_source

   Usage
   -----
       To use twitter_analysis.py specify credentials, trackwords,
       and the compute function, and optionally the number of Tweets.
       An example of the compute function is in the simple test.

    """
    # Step 1:
    def g(s):
        """
        The computational function, g(s), is an agent consisting of a
        single sink element which executes compute_func(v) for each v 
        in its input stream s.

        """
        sink_element(func=compute_func, in_stream=s)

    # Step 2:
    def f(s):
        """
        The source function, f(s), is an agent that reads Twitter with
         the specified trackwords and credentials, and puts Tweets on its
         output stream s

        """
        return twitter_to_stream(
            consumer_key, consumer_secret,
            access_token, access_token_secret,
            trackwords, out_stream=s,
            num_steps=num_steps)

    # Step 3:
    # Create a single process with a single source specified by function f, 
    # and a computational function specified by function g
    single_process_single_source(source_func=f, compute_func=g)

def print_tweets(trackwords, num_steps):
    """
    Create an agent that prints tweets with the specified track words.
    Halt after printing num_steps tweets.

    You must specify the credentials --- consumer_key, consumer_secret,
    and access_token, access_token_secret --- outside this function.
    
    Parameters
    ----------
       trackwords: list of str
           The list of words that you want to track on Twitter.
       num_steps: int, optional
           The number of Tweets that are printed.
           If num_steps is not specified then this agent does not
           terminate execution.

    """
    
    def compute_func(tweet):
        if 'text' in tweet:
            print(tweet['text'])
            print

    twitter_analysis(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, compute_func, num_steps)

def print_sentiment_followers_retweets(trackwords, num_steps):
    """      
    Detailed test containing functions for retrieving and analyzing
    data for each tweet      
    """

    # thresholds that a tweet must meet in order to be
    # considered for sentiment analysis
    follower_limit = 5
    retweet_limit = 1

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

    def compute_func(tweet):
        """
        Computational function that operates on a stream, s,
        generated by the source
        
        Parameters:
            tweet (dict): data for individual tweet
        """
        
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

    twitter_analysis(consumer_key, consumer_secret,
                     access_token, access_token_secret,
                     trackwords=['Trump'],
                     compute_func=compute_func, num_steps=5)

if __name__ == '__main__':
    print "starting simple test"
    print_tweets(trackwords=['Trump'], num_steps=5)
    print 'simple test is finished'
    print '------------------------------------'
    print
    print
    print '------------------------------------'
    print 'starting test of sentiment analysis' 
    #clears file containing sentiment of each tweet
    open('twitter_sentiment.txt', 'w').close()
    print_sentiment_followers_retweets(
        trackwords=['Trump'], num_steps=5)
    print 'sentiment analysis test is finished'
    print '------------------------------------'
