import numpy as np
from .kmeans import kmeans, findClosestCentroids, evaluate_error, init_plot


class Model:
    def __init__(self, k):
        self.centroids = None
        self.k = k
        self.sum_iterations = 0
        self.sum_error = 0
        self.i = 0


class KMeansStream:
    """Helper class for kmeans clustering.

    This class provides train and predict functions for using kmeans with
    `Stream_Learn`.

    Parameters
    ----------
    draw : boolean
        Describes whether the data is to be plotted (data must have 2 or less
        dimensions).
    output : boolean
        Describes whether debug info is to be printed. Info includes average
        error, average number of iterations, current number of iterations, and
        number of changed points over time.
    k : int
        Describes the number of clusters to train.
    incremental : boolean, optional
        Describes whether the kmeans algorithm is run incrementally or not (the
        default is True). If incremental, then previous clusters are used to
        initialize new clusters. Otherwise, clusters are reinitialized randomly
        for each window.
    figsize : tuple, optional
        A tuple containing the width and height of the plot for the map (the
        default is (15, 8)).

    Attributes
    ----------
    train : function
        The train function with signature as required by `Stream_Learn`.
    predict : function
        The predict function with signature as required by 'Stream_Learn'.
    avg_iterations : float
        The average number of iterations per window of data trained.
    avg_error : float
        The average error per window of data trained.

    """
    def __init__(self, draw, output, k, incremental=True, figsize=(1000, 500)):
        self.draw = draw
        self.output = output
        self.k = k
        self.incremental = incremental
        self.avg_iterations = 0
        self.avg_error = 0
        self._init_func()
        self.centroids = None
        self.source = None

        if draw:
            self.source = init_plot(figsize)

    def _init_func(self):

        def train_function(x, y, model, window_state):
            if not model:

                model = Model(self.k)
            if model.centroids is not None and self.incremental:
                [centroids, index, i] = kmeans(x, model.k, model.centroids,
                                               draw=self.draw,
                                               output=self.output,
                                               source=self.source)
            else:
                [centroids, index, i] = kmeans(x, model.k, draw=self.draw,
                                               output=self.output,
                                               source=self.source)
            model.centroids = centroids
            self.centroids = centroids
            error = evaluate_error(x, centroids, index)

            if self.output:
                print "Error: ", error

            model.sum_iterations += i
            model.sum_error += error
            model.i += 1
            return model

        def predict_function(x, y, model):
            self.avg_iterations = float(model.sum_iterations) / float(model.i)
            self.avg_error = float(model.sum_error) / float(model.i)
            if self.output:
                print "Average number of iterations: ", self.avg_iterations
                print "Average error: ", self.avg_error, "\n"
            return findClosestCentroids(np.array(x).reshape(1, len(x)),
                                        model.centroids)

        self.train = train_function
        self.predict = predict_function

    def reset(self):
        """Resets the KMeans functions and average values.

        Resets: train, predict, avg_iterations, avg_error

        """
        self._init_func()
        if self.draw:
            init_plot()

        self.avg_iterations = 0
        self.avg_error = 0
