import numpy as np
import math
from bokeh.models import ColumnDataSource
from bokeh.plotting import curdoc, figure
from bokeh.client import push_session

TIME_SLEEP = 0.000000001


def train_sgd(X, y, alpha, w=None):
    """Trains a linear regression model using stochastic gradient descent.

    Parameters
    ----------
    X : numpy.ndarray
        Numpy array of data
    y : numpy.ndarray
        Numpy array of outputs. Dimensions are n * 1, where n is the number of rows
        in `X`.
    alpha : float
        Describes the learning rate.
    w : numpy.ndarray, optional
        The initial w vector (the default is zero).

    Returns
    -------
    w : numpy.ndarray
        Trained vector with dimensions (m + 1) * 1, where m is the number of
        columns in `X`.

    """

    X_b = np.hstack((np.ones((X.shape[0], 1)), X))

    previous_error = -1
    error = -1

    stop = False
    num_iters = 0

    if w is None:
        w = np.zeros((x.shape[1] + 1, 1))

    while not stop:
        for i in range(0, len(X)):
            w = w - alpha / len(X) * (np.dot(np.transpose(w),
                                      X_b[i].reshape(X_b.shape[1], 1)) -
                                      y[i]) * X_b[i].reshape(X_b.shape[1], 1)

            error = evaluate_error(X, y, w)
            if previous_error == -1:
                previous_error = error
            elif (math.fabs(error - previous_error) < 0.01 * previous_error and
                  num_iters > 10000):
                stop = True
                break

            previous_error = error
            num_iters += 1

    return w


def train(X, y):
    """Trains a linear regression model using linear algebra.

    Parameters
    ----------
    X : numpy.ndarray
        Numpy array of data
    y : numpy.ndarray
        Numpy array of outputs. Dimensions are n * 1, where n is the number of rows
        in `X`.

    Returns
    -------
    w : numpy.ndarray
        Trained vector with dimensions (m + 1) * 1, where m is the number of
        columns in `X`.

    """

    # Add bias term
    X_b = np.hstack((np.ones((X.shape[0], 1)), X))

    # Compute pseudo-inverse
    X_inverse = (np.linalg.inv(np.transpose(X_b).dot(X_b)).dot(
                 np.transpose(X_b)))

    # Compute w
    w = X_inverse.dot(y)

    return w


# Plot data
def plot(X, y, w, source, step_size, max_window_size):
    """Plot X data, the actual y output, and the prediction line.

    Parameters
    ----------
    X : numpy.ndarray
        Numpy array of data with 1 column.
    y : numpy.ndarray
        Numpy array of outputs. Dimensions are n * 1, where n is the number of
        rows in `X`.
    w : numpy.ndarray
        Numpy array with dimensions 2 * 1.
    source : list
        List of ColumnDataSource
    step_size : int
        The step size
    max_window_size : int
        The max window size

    """

    X_b = np.hstack((np.ones((X.shape[0], 1)), X))


    y_predict = X_b.dot(w)

    source, predict = source

    for i in range(-step_size, 0):
        x_value = X[i].tolist()[0]
        y_value = y[i].tolist()[0]

        new_data = dict(
            x=[x_value],
            y=[y_value],
        )

        source.stream(new_data, max_window_size)

    predict.data = dict(x=X.flatten().tolist(), y=y_predict.flatten().tolist())


def init_plot(figsize=(1000, 500)):
    """Initializes the plot.

    Parameters
    ----------
    figsize : tuple, optional
        A tuple containing the width and height of the plot (the default is
        (1000, 800)).

    """

    source = ColumnDataSource(dict(
        x=[], y=[]
    ))

    predict = ColumnDataSource(dict(
        x=[], y=[]
    ))

    p = figure(plot_width=figsize[0], plot_height=figsize[1], tools="xpan,xwheel_zoom,xbox_zoom,reset", x_axis_type=None, y_axis_location="right")
    p.x_range.follow = "end"
    p.x_range.follow_interval = 100
    p.x_range.range_padding = 0

    p.circle(x='x', y='y', alpha=0.2, line_width=3, color='navy', source=source)
    p.line(x='x', y='y', alpha=0.2, line_width=3, color='navy', source=predict)

    session = push_session(curdoc())

    curdoc().add_root(p)

    session.show()

    return source, predict

def evaluate_error(X, y, w):
    """Returns the mean squared error.

    X : numpy.ndarray
        Numpy array of data.
    y : numpy.ndarray
        Numpy array of outputs. Dimensions are n * 1, where n is the number of
        rows in `X`.
    w : numpy.ndarray
        Numpy array with dimensions (m + 1) * 1, where m is the number of
        columns in `X`.

    Returns
    -------
    float
        The mean squared error

    """

    X_b = np.hstack((np.ones((X.shape[0], 1)), X))
    y_predict = X_b.dot(w)
    dist = (y - y_predict) ** 2

    return float(np.sum(dist)) / X.shape[0]


def predict(X, w):
    """Returns the prediction for one data point.

    Parameters
    ----------
    X : numpy.ndarray
        Numpy array of data
    w : numpy.ndarray
        Numpy array with dimensions (m + 1) * 1, where m is the number of
        columns in `X`.

    Returns
    -------
    float
        The mean squared error

    """
    X_b = np.hstack((np.ones((X.shape[0], 1)), X))
    return X_b.dot(w)
