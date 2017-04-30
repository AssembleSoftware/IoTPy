from IoTPy.modules import Geomap
from IoTPy.modules.ML.KMeans import kmeans
from IoTPy.code.stream import _no_value

import requests
import json


def plot(x, y, model, state):
    """ Plots Meetup RSVPs and centroids

    Parameters
    ----------
    x : numpy.ndarray
        The location data to plot
    y : numpy.ndarray
        No data
    model : object
        Kmeans model
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
    state.plot(x, kmeans.findClosestCentroids(x, model.centroids), s=70)
    return state


def source(state):
    """ Returns the next Meetup RSVP

    This function gets the next Meetup RSVP from the Meetup stream and returns
    the location data.

    Parameters
    ----------
    state : object
        The Meetup stream

    Returns
    -------
    list
        A list containing the location data and the state

    """
    if state == 0:
        r = requests.get('http://stream.meetup.com/2/rsvps', stream=True)
        state = r.iter_lines()
    line = next(state)
    if line:
        data = json.loads(line)
        lat, lon = data['group']['group_lat'], data['group']['group_lon']
        if data['group']['group_country'] == 'us':
            return (lat, lon), state
    return _no_value, state
