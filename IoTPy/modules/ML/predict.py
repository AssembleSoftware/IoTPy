import numpy as np
from IoTPy.code.stream import _no_value


def predict(lst, state, predict_func, num_features):
    """ This function predicts values using predict_func

    Parameters
    ----------
    lst : list
       Data to predict
    state : object
       State for model
    predict_func : function
        A function that takes as input 2 tuples corresponding to 1 row of data
        and a model and returns the prediction output.
        This function has the signature (tuple tuple Object) -> (Object).
        The first tuple x has `num_features` values and the second tuple y
        has num_outputs values, where num_outputs refers to the number of y
        outputs for an input. In the case of unsupervised learning, y is empty.
    num_features : int
        An int that describes the number of features in the data.

    """

    # Update model
    index, value = lst
    if index == 1:
        state = value
    else:
        # Predict if model is valid
        if state != 0:
            if not isinstance(value, tuple):
                return predict_func(value, None, state)
            x = value[0:num_features]
            y = value[num_features:]
            model = state
            return predict_func(x, y, model), state
    return _no_value, state
