

class Parameter:
    """ Stores parameter info for assemble

    Parameters
    ----------
    name : str
        Name of the part
    param : str
        Name of the field
    index : int
        Index of the field.

    Attributes
    ----------
    name : str
        Name of the part
    param : str
        Name of the field
    index : int, optional
        Index of the field (the default is None)

    """
    def __init__(self, name, param, index=None):
        self.name = name
        self.param = param
        self.index = index

    def to_list(self):
        """ Returns the parameter info as a list

        Returns
        -------
        lst
            List containing name and param, and index if valid

        """
        lst = [self.name, self.param]
        if self.index is not None:
            lst.append(self.index)
        return lst

    def __str__(self):
        s = "Parameter: {0}:{1}".format(self.name, self.param)
        if self.index is not None:
            s += ":" + str(self.index)
        return s


def get_external(external):
    """ Constructs a Parameter object from a list

    Parameters
    ----------
    external : list
        List containing name, param, and index (optional)

    Returns
    -------
    Parameter

    """
    return Parameter(*external)


def get_internal(internal):
    """ Constructs Parameter objects from internal list

    This function constructs a source and a destination from a list.

    Parameters
    ----------
    internal : list
        List containing source name, source param name, source index (optional),
        destination name, destination param name, destination index (optional)

    Returns
    -------
    Parameter, Parameter
        Source and destination Parameter objects

    """
    source_index = None
    des_index = None

    # No indices
    if len(internal) == 4:
        source, source_param, des, des_param = internal
    elif len(internal) == 5:

        # Source index
        if isinstance(internal[2], int):
            source, source_param, source_index, des, des_param = internal

        # Destination index
        else:
            source, source_param, des, des_param, des_index = internal
    else:
        source, source_param, source_index, des, des_param, des_index = internal

    return Parameter(source, source_param, source_index), Parameter(
        des, des_param, des_index)


def make_internal(source, des):
    """ Creates list from source and destination Parameter objects

    Parameters
    ----------
    source : Parameter
        Parameter object for source
    des : Parameter
        Parameter object for destination
 
    Returns
    -------
    list
        List for connection, parameter for get_internal

    See Also
    --------
    get_internal

    """
    internal = source.to_list() + des.to_list()
    return internal
