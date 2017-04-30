import random
import math


def source(state):
    """ Returns a list of two random values

    Parameters
    ----------
    state : int
        The step

    Returns
    -------
    list
        List of two random values

    """
    i = state
    state += 1
    return [random.randint(0, 10) * 0 + i, i *
            math.sin(i / 100.0) + math.sin(i / 10.0)], state
