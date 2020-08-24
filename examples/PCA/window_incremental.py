import numpy as np
import matplotlib.pyplot as plt
# sklearn imports
from sklearn.datasets import load_iris
from sklearn.decomposition import IncrementalPCA

import sys
from IoTPy.core.agent import Agent
from IoTPy.core.stream import Stream, StreamArray, _no_value, _multivalue, run
from IoTPy.agent_types.check_agent_parameter_types import check_agent_parameter_types
from IoTPy.agent_types.op import map_window
from IoTPy.agent_types.sink import sink_window
from IoTPy.agent_types.basics import fmap_w, sink_w
from IoTPy.helper_functions.recent_values import recent_values, incremental_buffer
from IoTPy.helper_functions.print_stream import print_stream

class incremental_PCA(object):
    def __init__(self, in_stream, out_stream, n_components, batch_size, n_recompute, plotter):
        '''
        Parameters
        ----------
        in_stream: Stream
           The single input stream
        out_stream: Stream
           The single output stream
        n_components: int (optional)
           Positive int, greater than 1, specifying number of components of
           the PCA. See IncrementalPCA
        batch_size: int (optional)
           The size of the batches used in IncrementalPCA
        n_recompute: int
        plotter: func
           The function used for plotting the results.

        '''
        self.in_stream = in_stream
        self.out_stream = out_stream
        self.n_components = n_components
        self.batch_size = batch_size
        self.n_recompute = n_recompute
        self.history = incremental_buffer(self.n_recompute*self.batch_size)
        self.ipca = IncrementalPCA(self.n_components, self.batch_size)
        self.plotter = plotter
        sink_window(self.f, self.in_stream,
               window_size=self.batch_size, step_size=self.batch_size)
    def f(self, window):
        self.ipca.partial_fit(window)
        self.history.extend(window)
        self.transformed_data = self.ipca.transform(self.history.value[:self.history.num_samples])
        self.out_stream.extend((self.transformed_data))
        self.plotter.plot(self.transformed_data)

class plot_incremental(object):
    def __init__(self, target, colors, labels):
        self.target = target
        self.colors = colors
        self.labels = labels
        self.n_types = len(colors)
    def plot(self, data):
        size = len(data)
        plt.figure(figsize=(8, 8))
        for color, i, target_name in zip(self.colors, [0, 1, 2], self.labels):
            plt.scatter(data[self.target[:size] == i, 0],
                        data[self.target[:size] == i, 1],
                        color=color, label=target_name)
        plt.title("Incremental PCA of iris dataset")
        plt.legend(loc="best", shadow=False, scatterpoints=1)
        plt.axis([-4, 4, -1.5, 1.5])
        plt.show()

## #This is the same algorithm implemented using an IoTPy function rather than an
#  #IoTPy class.
## def incremental_PCA(in_stream, out_stream, n_components, batch_size, n_recompute):
##     ipca = IncrementalPCA(n_components, batch_size)
##     @sink_w
##     def f(window, state, out_stream):
##         ipca.partial_fit(window)
##         state.extend(window)
##         transformed_data = ipca.transform(state.value[:state.num_samples])
##         out_stream.extend(transformed_data)
##         return state
##     f(in_stream, window_size=batch_size, step_size=batch_size,
##       state=incremental_buffer(n_recompute*batch_size),
##       out_stream=out_stream)

def test_incremental_PCA():
    # GET DATA
    iris = load_iris()
    raw_data = iris.data
    target = iris.target
    n_samples, n_features = raw_data.shape
    # RANDOMIZE DATA
    n_components = 2
    perm = np.random.permutation(n_samples)
    raw_data = raw_data[perm]
    target = target[perm]
    # SET UP PLOT
    plotter = plot_incremental(
        target=target,
        colors=['navy', 'turquoise', 'darkorange'],
        labels=iris.target_names)
    # RUN ALGORITHM
    in_stream = StreamArray(dimension=n_features, dtype=float)
    out_stream = StreamArray(dimension=n_components, dtype=float)
    incremental_PCA(in_stream, out_stream, n_components, batch_size=30, n_recompute=5,
                    plotter=plotter)
    in_stream.extend(raw_data)
    run()
    print (out_stream.recent[:out_stream.stop])

if __name__ == '__main__':
    test_incremental_PCA()


##     #for X_transformed, title in [(X_ipca, "Incremental PCA"), (X_pca, "PCA")]:
##     colors = ['navy', 'turquoise', 'darkorange']
##     plt.figure(figsize=(8, 8))
##     for color, i, target_name in zip(colors, [0, 1, 2], iris.target_names):
##         plt.scatter(reduced_data[target[:end] == i, 0], reduced_data[target[:end] == i, 1],
##                     color=color, lw=2, label=target_name)
        
##     plt.axis([-4, 4, -1.5, 1.5])
##     plt.show()


