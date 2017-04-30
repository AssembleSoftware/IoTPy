from IoTPy import config
from IoTPy.modules import Geomap

import json

import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler

import numpy as np

import nltk

import nltk.classify.util
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import movie_reviews
from nltk.stem.porter import *

import time

access_token = config.get("twitter", "access_token")
access_token_secret = config.get("twitter", "access_token_secret")
consumer_key = config.get("twitter", "consumer_key")
consumer_secret = config.get("twitter", "consumer_secret")


class StdOutListener(StreamListener):

    def __init__(self, stream):
        StreamListener.__init__(self)
        self.stream = stream

    def on_data(self, data):
        try:
            data_json = json.loads(data)
            text = data_json['text']
            if data_json['place']['bounding_box'] and 'retweeted_status' not in data_json.keys():
                if data_json['place']['country'] == 'United States':
                    location = np.array(
                        data_json['place']['bounding_box']['coordinates'])
                    location = location.flatten().reshape(4, 2)
                    mean_loc = tuple(np.mean(location, 0).tolist())
                    self.stream.extend(
                        [(text, float(mean_loc[1]), float(mean_loc[0]))])
        except BaseException:
            pass
        return True

    def on_error(self, status):
        print status


def plot(x, y, model, state):
    """ Plots the twitter data

    Parameters
    ----------
    x : numpy.ndarray
        The array of tweets
    y : numpy.ndarray
        The array of locations
    model : object
        The model for sentiment analysis
    state : object
        The plot state

    Returns
    -------
    Geomap.Geomap
        The current map

    """
    if state is None:
        state = Geomap.Geomap(
            lat=40,
            lng=-100,
            map_type="roadmap",
            zoom=3)

    locations = np.zeros((len(y), 2))
    for i in range(0, len(y)):
        locations[i][0] = float(y[i][0])
        locations[i][1] = float(y[i][1])

    index = np.zeros((len(y), 1))
    for i in range(0, len(x)):
        tweet = x[i][0]
        sentiment = model.classify(word_feats(tweet.split()))
        index[i] = int(sentiment == 'pos')

    state.plot(locations, index, text=x, s=100)

    return state


def train_function(x, y, model, window_state):
    """ Trains a model for sentiment analysis

    Parameters
    ----------
    x : numpy.ndarray
        The array of tweets
    y : numpy.ndarray
        The array of locations
    model : object
        The model for sentiment analysis
    window_state : list
        The current window state. See train.py

    Returns
    -------
    object
        The model for sentiment analysis

    """
    if not model:
        negids = movie_reviews.fileids('neg')
        posids = movie_reviews.fileids('pos')

        negfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'neg')
                    for f in negids]
        posfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'pos')
                    for f in posids]

        negcutoff = len(negfeats) * 3 / 4
        poscutoff = len(posfeats) * 3 / 4

        trainfeats = negfeats[:negcutoff] + posfeats[:poscutoff]
        testfeats = negfeats[negcutoff:] + posfeats[poscutoff:]
        print 'train on %d instances, test on %d instances' % (len(trainfeats), len(testfeats))

        classifier = NaiveBayesClassifier.train(trainfeats)
        print 'accuracy:', nltk.classify.util.accuracy(classifier, testfeats)

        return classifier

    return model


def predict_function(tweet, y, classifier):
    """ This function predicts the sentiment for a tweet

    Parameters
    ----------
    tweet : numpy.ndarray
        The array of tweets.
    y : numpy.ndarray
        The location of the tweet
    classifier : object
        The model for sentiment analysis

    """

    tweet = tweet[0]
    print "--------------------------------------------------------------------------------"
    print "Tweet: ", tweet
    sentiment = classifier.classify(word_feats(tweet.split()))
    if sentiment == 'pos':
        sentiment_r = "Positive"
    elif sentiment == 'neg':
        sentiment_r = "Negative"
    print "Sentiment: ", sentiment_r


def word_feats(words):
    return dict([(word, True) for word in words])


def source(stream):
    """ This function creates a stream of tweets

    Parameters
    ----------
    stream : Stream
        Stream to add tweets

    """
    l = StdOutListener(stream)
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = tweepy.Stream(auth, l)
    while True:
        try:
            stream.filter(track=['trump', 'clinton'])
        except:
            continue
