import numpy as np


def plot(lst, state, plot_func, num_features):
    """ This function plots data using the plot_func

    Parameters
    ----------
    lst : list
        Data to plot
    state : object
        State used for predict and plot
    plot_func : function
        A function that processes the data for usage such as visualization.
        This function takes parameters x and y data, a model object, a state
        object, and returns an updated state object.
        This function has the signature
        (np.ndarray np.ndarray Object Object tuple) -> (Object).
        The first numpy array x has dimensions i x `num_features`, where
        `min_window_size` <= i <= `max_window_size`. The second numpy array y
        has dimensions i x num_outputs, where num_outputs refers to the number
        of y outputs for an input. The third parameter is the model object
        defined by `train_func`. The fourth parameter is a state object defined
        by this function.
    num_features : int
        An int that describes the number of features in the data.

    """

    index, value = lst

    # Initialize state
    if state == 0:
        state = [None, None]

    # Update model
    if index == 1:
        state[0] = value
    else:
        # Plot if model is valid
        if state[0] is not None:
            data = np.array(value)
            x = data[:, 0:num_features]
            y = data[:, num_features:]

            model = state[0]
            state_plot = state[1]
            state_plot = plot_func(x, y, model, state_plot)
            state[1] = state_plot
    return state
