"""
This module contains:
(1) code for the k-means algorithm, see
https://en.wikipedia.org/wiki/K-means_clustering
and
(2) applications of the algorithm to sliding windows of
a stream.

The module contains the following functions:
 * random_points: returns random points in a space.
 * random_items_in_data: returns a sample, without
   replacement, of the data.
 * normally_distributed_points: returns points in space
   where the points are normally distributed with a
   specified center and standard deviation.
 * closest_sentinel: given a collection of points and
   another collection of points, called sentinels,
   then the function returns the closest sentinel to
   each point.
 * mean_squared_distance_to_sentinels: returns the
   average of the square of the distance of each point
   to its associated sentinel.
 * compute_centroids: given a collection of clusters of
   points this function returns the centroids of the
   clusters.
 * kmeans: the k-means algorithm.
 * kmeans_sliding_windows: the k-means algorithm applied
   to sliding windows in a stream.

"""
import numpy as np
import random

import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, StreamArray, run
from IoTPy.agent_types.op import map_window
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.helper_functions.print_stream import print_stream


def random_points(num_points, num_dimensions, low, high):
    """
    Returns num_points random points in a space with
    num_dimensions. Each coordinate of each point lies
    in [low, high).

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
    Picks random rows of data.

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
    # random.sample(range(0, len(data)), num_items) is
    # a list of num_items random numbers in the range
    # [0, len(data)) where the list has no duplicates.
    index = random.sample(range(0, len(data)), num_items)
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
    # np.dot(point - sentinel, point - sentinel) is the
    # square of the distance between point and sentinel.
    # We don't need to compute the actual distance using
    # np.linalg.norm, and it's faster not to.
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
        points, num_clusters, initial_centroids=None, output_flag=False,
        source=None):
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
        initialize the algorithm. Get random centroids by calling
        random_items_in_data(..)
    output_flag : boolean, optional
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
        if num_iters != 0 and output_flag:
            print (np.count_nonzero(cluster_ids - previous_cluster_ids),\
                " data points changed centroids")
        previous_cluster_ids, previous_centroids = cluster_ids, centroids
        X = points
        # Compute location of the centroid of each cluster given the
        # clusters.
        centroids = compute_centroids(points, cluster_ids, num_clusters)
        num_iters += 1

    if output_flag:
        print ("Num iters: ", num_iters)
    return [centroids, cluster_ids]

class KMeansForSlidingWindows(object):
    def __init__(
            self, num_clusters,
            initial_centroids=None, output_flag=False):
        self.num_clusters = num_clusters
        self.centroids = initial_centroids
        self.cluster_ids = np.array([0]*num_clusters)
        self.output_flag = output_flag
    def func(self, points):
        self.centroids, self.cluster_ids = kmeans(
            points, self.num_clusters,
            self.centroids, self.output_flag)
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
    
def normally_distributed_points(center, stdev, num_points):
    """
    Return num_points points with a normal distribution and
    the specified center and specified standard deviation.
    The number of dimensions of the space is obtained from
    the number of dimensions of center.

    Parameters
    ----------
    center : numpy.ndarray
        A one-dimensional array. Its shape is (num_dimensions,)
        where num_dimensions is the number of dimensions of the
        space. For example, a center could be [0.0, 0.0, 0.0]
        in a 3-D space.
    stdev : float
        The standard deviation of the distribution.
    num_points : int
        The number of points to make.

    Returns
    -------
    X : numpy.ndarray
        A numpy array with dimensions (num_points, num_dimensions).
        Each row of the array represents a point with the j-th
        coordinate being the j-th element of the row.
        The points are selected randomly from a normal distribution
        with the specified center and standard deviation.

    """
    # num_dimensions is the number of dimensions of this space
    num_dimensions = center.shape[0]
    return np.random.normal(center, stdev, (num_points, num_dimensions))

def mean_squared_distance_to_sentinels(points, sentinels, indexes):
    """Returns the average square of distance from each point in
    points to its associated sentinel. The sentinel associated
    with points[p] is sentinels[indexes[p]] for p in 0,..,num_points
    where num_points is the number of rows of p. The length of
    indexes is also num_points.

    Parameters
    ----------
    points : numpy.ndarray
        Each row of the array represents a point in d-space
        where d is the number of columns of the array.
        The number of rows of points is num_points.
    sentinels : numpy.ndarray
        A numpy array with d columns.
        Each row represents a sentinel.
        The number of rows is the number of sentinels which
        is an arbitrary positive value.
    indexes : numpy.ndarray
        A numpy array with 1 column. The number of rows is
        num_points.
        sentinel[indexes[p]] is the sentinel associated with
        point p.

    Returns
    -------
    float
        Sum of squares of points to their corresponding
        sentinels.

    Notes
    -----
    The mean squared error is calculated as the average squared distance of
    each point from the closest centroid.

    """
    sum_of_squares = 0.0
    num_points = len(points)
    for i in range(0, num_points):
        sentinel = sentinels[indexes[i]]
        point = points[i]
        sum_of_squares += np.dot(point-sentinel, point-sentinel)
    return sum_of_squares / num_points

def random_points_around_random_centroids(n, num_centroids, stdev, low, high):
    """
    Create num_centroids random centroids.
    For each centroid generate n random points, normally distributed,
    where the center is the centroid and with the specified standard deviation,
    stdev.

    Parameters
    ----------
    n : int
        The number of points around each centroid.
    num_centroids : int
        The number of centroids.
    stdev : int
        Describes the stdev for the distribution.
    low : int
        The lower bound (inclusive) for a centroid.
    high : int
        The upper bound (exclusive) for a centroid.

    Returns
    -------
    X : numpy.ndarray
        A numpy array with dimensions (`n` * `num_centroids`) * 2.

    """
    centroids = random_points(num_points=num_centroids, num_dimensions=2,
                              low=low, high=high)

    for i in range(0, len(centroids)):
        if i == 0:
            X = normally_distributed_points(center=centroids[i], stdev=stdev, num_points=n)
        else:
            X = np.vstack((X, normally_distributed_points(center=centroids[i], stdev=stdev, num_points=n)))

    print ('X is ', X)
    return X

#------------------------------------------------------------------------
#     TESTS
#------------------------------------------------------------------------
def test_random_points():
    num_points = 4
    num_dimensions = 3
    low, high = 2.0, 10.0
    points = random_points(
        num_points, num_dimensions, low, high)
    print ('---------------------------------------')
    print (' ')
    print ('testing random points')
    print ('num_points is ', num_points)
    print ('num_dimensions is ', num_dimensions)
    print ('low, high are ', low, high)
    print ('points is an array with num_dimensions columns')
    print ('  and num_points rows. Its entries are random ')
    print ('  points in the range [low, high)  \n')
    print ('points is:')
    print (points)

def test_random_items_in_data():
    data = np.array([
        [+1.0, +1.0],
        [+1.02, +1.02],
        [+1.01, +1.01],
        [+0.99, +0.99],
        [+0.98, +0.98],
        [+1.0, -1.0],
        [+1.01, -0.99],
        [+0.99, -1.01],
        [-1.0, +1.0],
        [-1.01, +0.99],
        [-0.99, +1.01],
        [-1.0, -1.0],
        [-1.01, -1.01],
        [-0.99, -0.99]
        ])
    num_items=5
    points = random_items_in_data(data, num_items)
    print ('---------------------------------------')
    print (' ')
    print ('testing random items in data')
    print ('data is ')
    print (data)
    print ('num_items is ', num_items)
    print ('points is an array with num_items rows')
    print (' Each point is picked randomly from data.')
    print (' ')
    print ('points is ')
    print (points)

def test_compute_centroids():
    points = np.array([
        [+1.0, +1.0],
        [+1.02, +1.02],
        [+1.01, +1.01],
        [+0.99, +0.99],
        [+0.98, +0.98],
        [+1.0, -1.0],
        [+1.01, -0.99],
        [+0.99, -1.01],
        [-1.0, +1.0],
        [-1.01, +0.99],
        [-0.99, +1.01],
        [-1.0, -1.0],
        [-1.01, -1.01],
        [-0.99, -0.99]
        ])
    cluster_ids = np.array([0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3])
    num_clusters = 4
    centroids = compute_centroids(points, cluster_ids, num_clusters)
    print ('---------------------------------------')
    print (' ')
    print ('testing compute centroids')
    print ('points is ')
    print (points)
    print ('cluster_ids is ', cluster_ids)
    print ('num_clusters is ', num_clusters)
    print ('centroids is ')
    print (centroids)
    
def test_kmeans():
    points = np.array([
        [+1.0, +1.0],
        [+1.02, +1.02],
        [+1.01, +1.01],
        [+0.99, +0.99],
        [+0.98, +0.98],
        [+1.0, -1.0],
        [+1.01, -0.99],
        [+0.99, -1.01],
        [-1.0, +1.0],
        [-1.01, +0.99],
        [-0.99, +1.01],
        [-1.0, -1.0],
        [-1.01, -1.01],
        [-0.99, -0.99]
        ])
    centroids, cluster_ids = kmeans(
        points, num_clusters=4)
    print ('---------------------------------------')
    print (' ')
    print ('testing kmeans')
    print ('input points is ')
    print (points)
    print ('output:')
    print ('centroids: ')
    print (centroids)
    print (' ')
    print ('cluster_ids: ')
    print (cluster_ids )
    print (' ')

def test_kmeans_sliding_windows():
    print ('-----------------------------------------')
    print (' ')
    print ('testing kmeans sliding windows')
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
    run()
    print (' ')
    print ('num_dimensions = ', num_dimensions)
    print ('window_size = ', window_size)
    print ('step_size = ', step_size)
    print ('num_clusters = ', num_clusters)
    print ('points: ')
    print (points)
    print ('output_stream: ')
    print (recent_values(out_stream))

def test_generate_normally_distributed_points():
    center = np.array([0.0, 0.0, 0.0])
    stdev = 1.0
    num_points=5
    print ('-----------------------------------------')
    print (' ')
    print ('testing normally distributed points')
    print ('center is ', center)
    print ('stdev is ', stdev)
    print ('num_points is ', num_points)
    points = normally_distributed_points(
        center, stdev, num_points)
    print ('points is')
    print (points)

def test_random_points_around_random_centroids():
    print ('testing random_points_around_random_centroids')
    n = 4
    num_centroids = 3
    stdev = 1.0
    low = -1.0
    high = 1.0
    random_points_around_random_centroids(n, num_centroids, stdev, low, high)
    

if __name__ == '__main__':
    test_random_points()
    test_random_items_in_data()
    test_compute_centroids()
    test_random_points_around_random_centroids()
    test_kmeans()
    test_kmeans_sliding_windows()
    test_generate_normally_distributed_points()
    
    
