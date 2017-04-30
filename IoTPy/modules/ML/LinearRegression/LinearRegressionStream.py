import numpy as np
from .linear_regression import train_sgd, train, init_plot, plot, evaluate_error


class Model:
    def __init__(self, num_features, incremental=False):
        self.w = np.zeros((num_features + 1, 1))
        self.sum_error = 0
        self.i = 0
        # Use incremental matrix state if data has 1 feature
        if num_features == 1 and incremental:
            self._sum = 0
            self._sum = 0
            self.y_sum = 0
            self.x_sum = 0


class LinearRegressionStream:
    """Helper class for linear regression.

    This class provides train and predict functions for using linear regression
    with `Stream_Learn`.

    Parameters
    ----------
    draw : boolean
        Describes whether the data is to be plotted (data must have 1
        dimension).
    output : boolean
        Describes whether debug info is to be printed. Info includes average
        error and current error.
    incremental : boolean, optional
        Describes whether the linear regression algorithm is run incrementally
        or not (the default is True). If incremental, then the algorithm uses
        incremental calculations for matrix inversion and matrix multiplication
        if the data has 1 feature, or stochastic gradient descent if the data
        has more than 1 feature. Otherwise, the algorithm uses linear algebra.
    alpha : float, optional
        Learning rate for stochastic gradient descent (the default is 0.01).
        Ignored if incremental is False or if incremental is True and data has
        1 feature.
    figsize : tuple, optional
        A tuple containing the width and height of the plot for the map (the
        default is (15, 8)).

    Attributes
    ----------
    train : function
        The train function with signature as required by `Stream_Learn`.
    predict : function
        The predict function with signature as required by `Stream_Learn`.
    w : tuple
        The learned weight vector.
    avg_error : float
        The average error per window of data trained.

    """
    def __init__(self, draw, output, incremental=True, alpha=0.01,
                 figsize=(1000, 500)):
        self.draw = draw
        self.output = output
        self.avg_error = 0
        self.incremental = incremental
        self._init_func()
        self.w = 0
        self.alpha = alpha

        if draw:
            self.source = init_plot(figsize)

    def _init_func(self):

        if self.incremental:
            def train_function(x, y, model, window_state):

                step_size = window_state[3]
                current_window_size = window_state[0]
                max_window_size = window_state[4]

                # Initialize model if not initialized
                if not model:

                    model = Model(x.shape[1], self.incremental)

                    # Set incremental matrix state if data has 1 feature
                    if x.shape[1] == 1:
                        model.x_sum = np.sum(x)
                        model.y_sum = np.sum(y)
                        model.xy_sum = np.sum(x * y)
                        model.xx_sum = np.sum(x ** 2)

                # Model is already initialized

                # If data has 1 feature, add last step_size points from
                # sums
                elif x.shape[1] == 1:
                    for i in range(-step_size, 0):
                        x_value = x[i].tolist()[0]
                        y_value = y[i].tolist()[0]
                        model.x_sum += x_value
                        model.y_sum += y_value
                        model.xy_sum += x_value * y_value
                        model.xx_sum += x_value ** 2

                # If data has 1 feature, compute w with incremental matrix
                if x.shape[1] == 1:

                    n = x.shape[0]
                    model.w[1] = (model.xy_sum - model.x_sum * model.y_sum /
                                  float(n)) / (model.xx_sum - model.x_sum *
                                               model.x_sum / float(n))
                    model.w[0] = (model.y_sum/float(n) - model.w[1] *
                                  model.x_sum/float(n))

                    self.w = model.w

                    if self.draw:
                        plot(x, y, model.w, self.source, step_size, max_window_size)

                    # If the window has not reached steady state and the next
                    # window will be at steady state, remove points to
                    # correctly update the sums
                    if (max_window_size - current_window_size < step_size and
                            not window_state[1]):
                        for i in range(0, step_size - (max_window_size -
                                                       current_window_size)):
                            x_value = x[i].tolist()[0]
                            y_value = y[i].tolist()[0]
                            model.x_sum -= x_value
                            model.y_sum -= y_value
                            model.xy_sum -= x_value * y_value
                            model.xx_sum -= x_value ** 2

                    # If the window has reached steady state, remove the first
                    # step size points from sums
                    if window_state[1]:

                        for i in range(0, step_size):
                            x_value = x[i].tolist()[0]
                            y_value = y[i].tolist()[0]
                            model.x_sum -= x_value
                            model.y_sum -= y_value
                            model.xy_sum -= x_value * y_value
                            model.xx_sum -= x_value ** 2

                # The data has more than 1 feature, train using SGD
                else:
                    model.w = train_sgd(x, y, self.alpha, model.w)
                    if self.draw:
                        plot(x, y, model.w, self.source, step_size, max_window_size)
                    self.w = model.w
                error = evaluate_error(x, y, model.w)
                if self.output:
                    print "Error: ", error

                model.sum_error += error
                model.i += 1
                return model

        # Non-incremental training
        else:
            def train_function(x, y, model, window_state):
                if not model:

                    model = Model(x.shape[1])

                step_size = window_state[3]
                max_window_size = window_state[4]

                model.w = train(x, y)
                if self.draw:
                    plot(x, y, model.w, self.source, step_size, max_window_size)
                self.w = model.w
                error = evaluate_error(x, y, model.w)
                if self.output:
                    print "Error: ", error

                model.sum_error += error
                model.i += 1
                return model

        def predict_function(x, y, model):
            self.avg_error = float(model.sum_error) / float(model.i)
            if self.output:
                print "Average error: ", self.avg_error, "\n"

            X_array = np.array(x).reshape(1, len(x))
            y_array = np.array(y).reshape(1, len(y))
            return evaluate_error(X_array, y_array, model.w) ** 0.5

        self.train = train_function
        self.predict = predict_function

    def reset(self):
        """Resets the KMeans functions and average values.

        Resets: train, predict, avg_error

        """
        self._init_func()
        if self.draw:
            self.source = init_plot()
        self.avg_error = 0
