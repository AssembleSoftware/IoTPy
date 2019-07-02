"""
This module contains code for the k-means algorithm, see
https://en.wikipedia.org/wiki/K-means_clustering
and applications of the algorithm to sliding windows of
a stream.

The module contains the following functions:
 * random_points: returns random points in a space.
 * random_items_in_data: returns a sample, without
   replacemnt, of the data.
 * closest_sentinel: given a collection of points and
   another collection of points, called sentinels,
   then the function returns the closest sentinel to
   each point.
 * compute_centroids: given a collection of clusters of
   points this function returns the centroids of the
   clusters.
 * kmeans: the k-means algorithm.
 * kmeans_sliding_windows: the k-means algorithm applied
   to sliding windows in a stream.

"""
import numpy as np
from bokeh.models import ColumnDataSource, LinearColorMapper
from bokeh.plotting import curdoc, figure
from bokeh.client import push_session
from bokeh.palettes import Magma
import random

import sys
import os

sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# stream is in ../../IoTPy/core
from stream import Stream, StreamArray
# op is in ../../IoTPy/agent_types
from op import map_window


def random_points(num_points, num_dimensions, low, high):
    """
    Returns num_points random points in a space with
    num_dimensions. In the plots in this module,
    num_dimensions is 2, and so the points are in
    the x-y plane. Each coordinate lies in [low, high).

    Parameters
    ----------
    num_points : int, positive
        The number of points to return.
    num_dimensions: int, positive
        The number of dimensions of the space.
    low : int or float
        The lower bound (inclusive) for each coordinate
        of each point.
    high : int or float
        The upper bound (exclusive) for each coordinate
        of each point.

    Returns
    -------
    random points : numpy.ndarray
        Numpy array with num_points rows and num_dimension
        columns. Each row represents a point in the space.

    """
    # np.random.rand(n, m) returns an array with n rows and
    # m columns where the entries are random numbers in (0, 1).
    return (
        np.random.rand(num_points, num_dimensions) * (high - low)
        + low)


def random_items_in_data(data, num_items):
    """
    Returns num_items from data without replacement.

    Parameters
    ----------
    data : numpy.ndarray
    num_items : int, pos
        The number of items to return.
        num_items must not exceed the number of rows
        in data.

    Returns
    -------
    random_items: numpy.ndarray
        An array with num_items rows. The number of
        columns of random_items is the same as the
        number of columns in data.

    """
    # random.sample(xrange(0, len(data)), num_items) is
    # a list of num_items random numbers in the range
    # [0, len(data)) where the list has no duplicates.
    index = random.sample(xrange(0, len(data)), num_items)
    random_items = data[index, :]
    return random_items


def closest_sentinel(points, sentinels):
    """
    Returns a numpy array containing the index of the closest
    sentinel for each point in points.

    Parameters
    ----------
    points : numpy.ndarray
        A numpy array.
        Each row represents a point in space. The number of
        columns is the dimension of the space.
    sentinels : numpy.ndarray
        A numpy array with arbitrary many rows and the same
        number of columns as points.
        Each row represents a sentinel, i.e. a special
        location in the space.

    Returns
    -------
    sentinel_ids : numpy.ndarray
        A numpy array with dimensions (n, 1), i.e. a vector,
        where n is the number of points, i.e. rows in the
        points array.
        sentinel_ids[i] is the index of the sentinel closest to
        the i-th point.

    """
    # np.dot(point - sentinel, point - sentinel) is the square of the distance
    # between point and sentinel.
    sentinel_ids = np.array(
        [np.argmin([np.dot(point - sentinel, point - sentinel)
                    for sentinel in sentinels])
        for point in points])
    return sentinel_ids

def compute_centroids(points, cluster_ids, num_clusters):
    """
    Finds the centroids for the data given the index of the closest centroid
    for each data point.

    Parameters
    ----------
    points : numpy.ndarray
        Each row of the points array represents a point in
        space. The number of columns in the points array
        is the dimension of the space.
    cluster_ids: numpy.ndarray
       Each point in points is assigned to a cluster.
       cluster_ids is a numpy array with dimensions (n, 1),
       i.e., a vector of length n, where n is the number of
       points (i.e. rows in the array points).
       cluster_ids[i] identifies the cluster to which the i-th
       point has been assigned.
    num_clusters : int
        The maximum number of clusters.
        The cluster ids are in the interval [0, .., num_clusters)

    Returns
    -------
    centroids : numpy.ndarray
        A numpy array with num_clusters rows and the same number
        of columns as points. The j-th row of centroids has the
        coordinates of the j-th centroid of a new cluster.

    Notes
    -----
    The centroids are computed by taking the mean of each group of points
    assigned to the same cluster. Therefore, centroids[i] is the mean of
    all points where cluster_ids[j] == i.

    """
    num_rows, num_columns = points.shape
    centroids = np.zeros((num_clusters, num_columns))

    for i in range(0, num_clusters):
        # idx is an array of indexes into points that all belong to
        # the i-th cluster.
        idx = np.where(cluster_ids == i)[0]
        if len(idx) != 0:
            points_in_cluster = points[idx, :]
            # For an array A, np.mean(A, 0) returns an array
            # with the same number of columns as A, and where
            # the j-th element of np.mean(A, 0) is the mean
            # of the j-th column of A
            centroids[i, :] = np.mean(points_in_cluster, 0)
    return centroids


def kmeans(
        points, num_clusters, initial_centroids=None, output=False):
    """
    Runs kmeans until clusters stop moving.

    Parameters
    ----------
    points : numpy.ndarray
        Each row of the points array represents a point in
        space. The number of columns in the points array
        is the dimension of the space.
    num_clusters : int
        The maximum number of clusters.
        The cluster ids are in the interval [0, .., num_clusters)
    initial_centroids : numpy.ndarray, optional
        A numpy array with initial centroids to run the kmeans algorithm.
        The number of rows in the array is num_clusters, and the
        number of columns is dimension of the space, i.e the same
        number of columns as in points.
        If initial_centroids is None then compute random centroids to
        initialize the algorithm.
    draw : boolean, optional
        Describes whether the data is to be plotted (data must have 2 or less
        dimensions). The default is False.
    output : boolean, optional
        Describes whether debug info is to be printed (the default is False).
        Info includes current number of iterations and number of changed points
        over time.

    Returns
    -------
    centroids : numpy.ndarray
        Numpy array with learned centroids. The array has the same dimensions
        as initial_centroids. The number of rows is num_clusters and the
        number of columns is the dimension of the space.
    cluster_ids: numpy.ndarray
       Each point in points is assigned to a cluster.
       cluster_ids is a numpy array with dimensions (n, 1),
       i.e., a vector of length n, where n is the number of
       points (i.e. rows in the array points).
       cluster_ids[i] identifies the cluster to which the i-th
       point has been assigned.

    Local Variables
    ---------------
    previous_cluster_ids: numpy.ndarray
        The value of cluster_ids on the previous iteration.

    """

    num_iters = 0
    # Use initial centroids if provided
    if initial_centroids is not None:
        centroids = initial_centroids
    # Set initial centroids to random points in the data.
    else:
        centroids = random_items_in_data(
            data=points, num_items=num_clusters)

    cluster_ids = np.zeros((len(points), 1))
    previous_centroids = centroids
    previous_cluster_ids = cluster_ids

    while True:
        cluster_ids = closest_sentinel(points, sentinels=centroids)
        # If no points have been reassigned to different clusters,
        # then the centroids have not moved, and so the algorithm
        # has reached a fixed point. Terminate the algorithm.
        if np.array_equal(cluster_ids, previous_cluster_ids):
            break

        # Print number of points reassigned
        if num_iters != 0 and output:
            print np.count_nonzero(cluster_ids - previous_cluster_ids),\
                " data points changed centroids"
        previous_cluster_ids, previous_centroids = cluster_ids, centroids
        ## if draw:
        ##     plotKMeans(X, centroids, previous, index, source)

        # Compute location of the centroid of each cluster given the
        # clusters.
        centroids = compute_centroids(points, cluster_ids, num_clusters)
        print 'centroids'
        print centroids
        print
        print 'points'
        print points
        print
        print 'cluster_ids'
        print cluster_ids
        print
        print '------------------------'
        num_iters += 1

    if output:
        print "Num iters: ", num_iters
    return [centroids, cluster_ids]

class KMeansForSlidingWindows(object):
    def __init__(
            self, num_clusters,
            initial_centroids=None, output=False):
        self.num_clusters = num_clusters
        self.centroids = initial_centroids
        self.cluster_ids = np.array([0]*num_clusters)
        self.output = output
    def func(self, points):
        print
        print 'Calling func'
        print
        self.centroids, self.cluster_ids = kmeans(
            points, self.num_clusters,
            self.centroids, self.output)
        return self.cluster_ids
        
def kmeans_sliding_windows(
        in_stream, out_stream, window_size, step_size, num_clusters):
    # The initial state is set to 0.
    # (Note that setting state to None implies no state, and so that
    # won't work.)
    kmeans_object = KMeansForSlidingWindows(num_clusters)
    map_window(
        kmeans_object.func, in_stream, out_stream,
        window_size, step_size)
    
def initializeDataCenter(centroid, scale, n):
    """
    Initialize n points with a normal distribution and scale around a
    centroid.

    Parameters
    ----------
    centroid : numpy.ndarray
        Numpy array with dimensions 1 * 2.
    scale : int
        Describes the scale for the distribution.
    n : int
        Describes the number of points to make.

    Returns
    -------
    X : numpy.ndarray
        A numpy array with dimensions `n` * 2.

    """
    X = np.random.normal(centroid, scale=scale, size=(n, 2))
    return X


def initializeData(n, k, scale, low, high):
    """
    Initialize n points around k random centroids each with a normal
    distribution and scale.

    Parameters
    ----------
    n : int
        Describes the number of points to make around each centroid.
    k : int
        Describes the number of centroids.
    scale : int
        Describes the scale for the distribution.
    low : int
        The lower bound (inclusive) for a centroid.
    high : int
        The upper bound (exclusive) for a centroid.

    Returns
    -------
    X : numpy.ndarray
        A numpy array with dimensions (`n` * `k`) * 2.

    """
    centroids = random_points_on_xy_plane(k, low, high)

    for i in range(0, len(centroids)):
        if i == 0:
            X = initializeDataCenter(centroids[i], scale, n)
        else:
            X = np.vstack((X, initializeDataCenter(centroids[i], scale, n)))

    return X


def _plotData(X, index, source):
    source.data = dict(x=X[:, 0], y=X[:, 1], index=index)


def plotKMeans(X, centroids, previous, index, source):
    """Plots the data and centroids.

    This function plots the data with the current centroids and shows the
    movement of the centroids.

    Parameters
    ----------
    X : numpy.ndarray
        A numpy array with 2 columns.
    centroids : numpy.ndarray
        A numpy array with 2 columns.
    previous : numpy.ndarray
        A numpy array with 2 columns and the same number of rows as
        `centroids`.
    index : numpy.ndarray
        A numpy array with 1 column.
    source : list
        List of ColumnDataSource

    """

    source, source_centroids, segments = source
    _plotData(X, index, source)
    source_centroids.data = dict(x=centroids[:, 0], y=centroids[:, 1],)
    segments.data = dict(x0=previous[:,0], y0=previous[:,1], x1=centroids[:,0], y1=centroids[:,1])


def init_plot(figsize=(1000, 500)):
    """Initializes the plot.

    Parameters
    ----------
    figsize : tuple, optional
        A tuple containing the width and height of the plot (the default is
        (1000, 800)).

    """

    source = ColumnDataSource(dict(
        x=[], y=[], index=[]
    ))

    centroids = ColumnDataSource(dict(
        x=[], y=[]
    ))

    segments = ColumnDataSource(dict(
        x0=[], y0=[], x1=[], y1=[]
    ))

    p = figure(plot_width=figsize[0], plot_height=figsize[1], tools="xpan,xwheel_zoom,xbox_zoom,reset", x_axis_type=None, y_axis_location="right")
    # p.x_range.follow = "end"
    # p.x_range.follow_interval = 100
    # p.x_range.range_padding = 0

    mapper = LinearColorMapper(palette=Magma[256])

    p.circle(x='x', y='y', alpha=0.2, line_width=3, color={"field": "index", "transform": mapper}, source=source)
    p.circle(x='x', y='y', alpha=0.2, size=20, color='black', source=centroids)
    p.segment(x0='x0', y0='y0', x1='x1', y1='y1', line_width=3, color='blue', source=segments)

    session = push_session(curdoc())

    curdoc().add_root(p)

    session.show()

    return source, centroids, segments


def evaluate_error(points, centroids, index):
    """Returns the mean squared error.

    Parameters
    ----------
    X : numpy.ndarray
        A numpy array with 2 columns.
    centroids : numpy.ndarray
        A numpy array with 2 columns.
    index : numpy.ndarray
        A numpy array with 1 column.

    Returns
    -------
    float
        The mean squared error.

    Notes
    -----
    The mean squared error is calculated as the average squared distance of
    each point from the closest centroid.

    """
    s = 0
    for i in range(0, len(X)):
        centroid_index = index[i]
        s += np.dot(X[i] - centroids[centroid_index], X[i] -
                    centroids[centroid_index])

    return float(s) / X.shape[0]

#------------------------------------------------------------------------
#     TESTS
#------------------------------------------------------------------------
def test_random_points():
    num_points = 4
    num_dimensions = 2
    low, high = 0.0, 1.0
    points = random_points(
        num_points, num_dimensions, low, high)
    print '---------------------------------------'
    print
    print 'testing random points'
    print 'num_points is ', num_points
    print 'num_dimensions is ', num_dimensions
    print 'low, high are ', low, high
    print 'points is:'
    print points

def test_random_items_in_data():
    data = np.array([
        [+1.0, +1.0],
        [+1.2, +1.2],
        [+1.1, +1.1],
        [+0.9, +0.9],
        [+0.8, +0.8],
        [+1.0, -1.0],
        [+1.1, -0.9],
        [+0.9, -1.1],
        [-1.0, +1.0],
        [-1.1, +0.9],
        [-0.9, +1.1],
        [-1.0, -1.0],
        [-1.1, -1.1],
        [-0.9, -0.9]
        ])
    num_items=5
    points = random_items_in_data(data, num_items)
    print '---------------------------------------'
    print
    print 'testing random items in data'
    print 'data is '
    print data
    print 'num_items is ', num_items
    print 'points is '
    print points

def test_compute_centroids():
    points = np.array([
        [+1.0, +1.0],
        [+1.2, +1.2],
        [+1.1, +1.1],
        [+0.9, +0.9],
        [+0.8, +0.8],
        [+1.0, -1.0],
        [+1.1, -0.9],
        [+0.9, -1.1],
        [-1.0, +1.0],
        [-1.1, +0.9],
        [-0.9, +1.1],
        [-1.0, -1.0],
        [-1.1, -1.1],
        [-0.9, -0.9]
        ])
    cluster_ids = np.array([0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3])
    num_clusters = 4
    centroids = compute_centroids(points, cluster_ids, num_clusters)
    print '---------------------------------------'
    print
    print 'testing compute centroids'
    print 'points is '
    print points
    print 'cluster_ids is ', cluster_ids
    print 'num_clusters is ', num_clusters
    print 'centroids is '
    print centroids
    
def test_centroids_simple():
    points = np.array([
        [+1.0, +1.0],
        [+1.2, +1.2],
        [+1.1, +1.1],
        [+0.9, +0.9],
        [+0.8, +0.8],
        [+1.0, -1.0],
        [+1.1, -0.9],
        [+0.9, -1.1],
        [-1.0, +1.0],
        [-1.1, +0.9],
        [-0.9, +1.1],
        [-1.0, -1.0],
        [-1.1, -1.1],
        [-0.9, -0.9]
        ])
    centroids, cluster_ids = kmeans(
        points, num_clusters=4)
    print '---------------------------------------'
    print
    print 'testing centroids_simple'
    print 'centroids: '
    print centroids
    print
    print 'cluster_ids: '
    print cluster_ids
    print
    print 'num_iters: '
    print num_iters
    print

def test_kmeans_sliding_windows():
    num_dimensions=2
    window_size = 12
    step_size = 2
    num_clusters = 4
    in_stream = StreamArray(
        name='in', dimension=num_dimensions)
    out_stream = StreamArray(
        name='out', dimension=window_size, dtype=int)

    kmeans_sliding_windows(
        in_stream, out_stream, window_size, step_size,
        num_clusters)

    points = np.array([
        [+1.0, +1.0],
        [+1.1, +1.1],
        [+0.9, +0.9],
        [+1.0, -1.0],
        [+1.1, -0.9],
        [+0.9, -1.1],
        [-1.0, +1.0],
        [-1.1, +0.9],
        [-0.9, +1.1],
        [-1.0, -1.0],
        [-1.1, -1.1],
        [-0.9, -0.9],
        # NEXT STEP
        [+1.0, +1.0],
        [+1.1, +1.1],
        # NEXT STEP
        [+0.9, +0.9],
        [+1.0, -1.0],
        # NEXT STEP
        [-1.2, -1.2],
        [-0.8, -0.8]
        ])
    in_stream.extend(points)
    Stream.scheduler.step()

    

if __name__ == '__main__':
    ## test_random_points()
    ## test_random_items_in_data()
    ## test_compute_centroids()
    ## test_centroids_simple()
    test_kmeans_sliding_windows()
    
    
