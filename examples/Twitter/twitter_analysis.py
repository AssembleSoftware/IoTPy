import sys
import os
from twitter import twitter_to_stream
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../multiprocessing"))
from Multicore import single_process_single_source
from sink import sink_element

import string
import time
import json
import re

# nltk: Natural Language Toolkit
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
# Sentiment analysis
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def twitter_analysis(consumer_key, consumer_secret,
            access_token, access_token_secret,
            trackwords, compute_func, num_steps=0):
    def g(s):
        def h(tweet):
            compute_func(tweet)
        sink_element(func=h, in_stream=s)

    def f(s):
        return twitter_to_stream(
            consumer_key, consumer_secret,
            access_token, access_token_secret,
            trackwords, out_stream=s,
            num_steps=num_steps)

    # Create a single process with a single source
    # specified by function f, and a computational function
    # specified by function g.
    single_process_single_source(
        source_func=f, compute_func=g)

def test():
    def untokenize(words):
        """
        From MIT license:
        https://github.com/commonsense/metanl/blob/master/metanl/token_utils.py
        Untokenizing a text undoes the tokenizing operation, restoring
        punctuation and spaces to the places that people expect them to be.
        Ideally, `untokenize(tokenize(text))` should be identical to `text`,
        except for line breaks.
        """
        text = ' '.join(words)
        step1 = text.replace("`` ", '"').replace(" ''", '"').replace('. . .', '...')
        step2 = step1.replace(" ( ", " (").replace(" ) ", ") ")
        step3 = re.sub(r' ([.,:;?!%]+)([ \'"`])', r"\1\2", step2)
        step4 = re.sub(r' ([.,:;?!%]+)$', r"\1", step3)
        step5 = step4.replace(" '", "'").replace(" n't", "n't").replace(
            "can not", "cannot")
        step6 = step5.replace(" ` ", " '")
        return step6.strip()
    
    # Variables that contain the user credentials to access Twitter API 
    access_token = "999118734320009216-jaE4Rmc6fU11sMmBKb566YTFAJoMPV5"
    access_token_secret = "6ZxqJdK2RU6iridMX1MzSqr3uNpQsC9fv1E6otpZquLiF"
    consumer_key = "Iv6RTiO7Quw3ivH0GWPWqbiD4"
    consumer_secret = "theWmGwcKFG76OtTerxwhrxfX5nSDqGDWB2almLlp2ndRpxACm"
    # trackwords is the list of words that you want to track on Twitter.
    trackwords=['Trump']

    # The computational function that operates on a stream s generated
    # by the source.
    def compute_func(tweet):
        stop_words = ('english', 'RT')
        if 'extended_tweet' in tweet:
            text = tweet['extended_tweet']['full_text']
        elif 'text' in tweet:
            text = tweet['text']
        else:
            text = str()
        if 'user' in tweet:
            tweet_user = tweet['user']
            if 'followers_count' in tweet_user:
                followers_count = tweet_user['followers_count']
        if 'retweet_count' in tweet:
            retweet_count = tweet['retweet_count']

        print 'text is ', text
        # convert tweet text to tokens
        tokens = word_tokenize(text)
        print 'tokens', tokens
        print 'followers_count', followers_count
        print 'retweet_count', retweet_count

        # tweet must be long enough, popular enough, and not a retweet
        if (len(tokens) > 2 and followers_count> 5):
        ## if (len(tokens) > 2 and 'RT' not in tweet and
        ##     followers_count> 5 and retweet_count > 1):
            print('Tweet:', text)
            print('followers_count:', followers_count) 
            print('retweet_count:', retweet_count)

            sentences = sent_tokenize(text)
            cleaned_tweet = str()
            for sentence in sentences:
                words = word_tokenize(sentence)
                # clean sentence
                for tok in words:
                    if ('http' in tok or
                        'https' in tok or
                        '//' in tok or
                        tok[0] not in string.ascii_letters
                        or tok in stop_words):
                        words.remove(tok)
                # convert filtered tokens back to text
                cleaned_sentence = untokenize(words) + '. '
                print 'cleaned_sentence', cleaned_sentence
                cleaned_tweet += cleaned_sentence

            print 'cleaned_tweet', cleaned_tweet
            # analyze sentiment of filtered tweet
            ## analyzer = SentimentIntensityAnalyzer()
            ## sent = analyzer.polarity_scores(cleaned_tweet)

            ## print('Sentiment:', sent['compound'])
            print('\n')

    twitter_analysis(
        consumer_key, consumer_secret,
        access_token, access_token_secret,
        trackwords, compute_func, num_steps=10)

if __name__ == '__main__':
    test()
