import numpy as np


def train(lst, state, train_func, num_features):
    """ This function trains a model using train_func

    Parameters
    ----------
    lst : list
        Data to train on
    state : object
        State for train
    train_func : function
        A function that trains a model.
        This function takes parameters x and y data, a model object, and a
        window_state tuple, and returns a trained model object.
        In the case of `data_train` as a `Stream`, this function has the
        signature (numpy.ndarray numpy.ndarray Object) -> (Object). The first
        parameter x will have dimensions i x `num_features`, where
        `min_window_size` <= i <= `max_window_size`. The second parameter y
        will have dimensions i x num_outputs, where num_outputs refers to the
        number of y outputs for an input. For example, num_outputs is 1 for 1
        scalar output. For unsupervised learning, num_outputs is 0.
        In the case of `data_train` as a `numpy` array, this function has the
        signature (numpy.ndarray numpy.ndarray Object) -> (Object). The first
        parameter x will have dimensions N x `num_features`, where N refers to
        the total number of training examples. The second parameter y will have
        dimensions N x num_outputs where num_outputs is defined as before.
        If `data_train` is none of the above, the function has the signature
        (Object None Object) -> (Object). The first parameter is `data_train`.
        The third parameter is a model defined by this function.
        The fourth parameter is a window_state tuple with the values
        (current_window_size, steady_state, reset, `step_size`,
        `max_window_size`),
        where current_window_size describes the number of points in the window,
        steady_state is a boolean that describes whether the window has reached
        `max_window_size`, and reset is a boolean that can be set to True to
        reset the window.
    num_features : int
        An int that describes the number of features in the data.
        
    """
    data = np.array(lst)
    x = data[:, 0:num_features]
    y = data[:, num_features:]

    # Initialize model
    if len(state) < 6:
        state.append(None)

    model = state[5]
    model = train_func(x, y, model, state)

    # Reset
    if state[1] and state[2]:
        model = None
    state[5] = model
    return (model, state)
