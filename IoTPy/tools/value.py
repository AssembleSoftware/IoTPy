

class Value:
    """ Class that stores values

    Parameters
    ----------
    value : object, optional
        Value to store

    Attributes
    ----------
    value : object
        Value stored
    dest : list
        List of Parameter destinations

    """
    def __init__(self, value=None):
        self.value = value
        self.dest = []
