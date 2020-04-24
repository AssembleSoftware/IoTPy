from collections import namedtuple
import numpy as np

class _stop_(object):
    def __init__(self):
        pass

class _close(object):
    def __init__(self):
        pass

class _changed(object):
    def __init__(self):
        pass

class _unchanged(object):
    def __init__(self):
        pass

class _no_value(object):
    """
    _no_value is the message sent on a stream to indicate that no
    value is sent on the stream at that point. _no_value is used
    instead of None because you may want an agent to send a message
    with value None and for the agent receiving that message to
    take some specific action.

    """
    def __init__(self):
        pass

class _multivalue(object):
    """
    When _multivalue([x1, x2, x3,...]) is sent on a stream, the
    actual values sent are the messages x1, then x2, then x3,....
    as opposed to a single instance of the class _multivalue.
    See examples_element_wrapper for examples using _multivalue.

    """
    def __init__(self, lst):
        self.lst = lst
        return

def remove_novalue_and_open_multivalue(l):
    """ This function returns a list which is the
    same as the input parameter l except that
    (1) _no_value elements in l are deleted and
    (2) each _multivalue element in l is opened
        i.e., for an object _multivalue(list_x)
        each element of list_x appears in the
        returned list.

    Parameter
    ---------
    l : list
        A list containing arbitrary elements
        including, possibly _no_value and
        _multi_value

    Returns : list
    -------
        Same as l with every _no_value object
        deleted and every _multivalue object
        opened up.

    Example
    -------
       l = [0, 1, _no_value, 10, _multivalue([20, 30])]
       The function returns:
           [0, 1, 10, 20, 30]

    """
    if not isinstance(l, list):
        return l
    return_list = []
    for v in l:
        if (isinstance(v, list) or
            isinstance(v, np.ndarray) or
            isinstance(v, tuple)):
            return_list.append(v)
        else:
            if (v == _no_value or
                v == _unchanged):
                continue
            elif (v == _changed):
                return_list.append(1)
            elif isinstance(v, _multivalue):
                return_list.extend(v.lst)
            else:
                return_list.append(v)
    return return_list

def remove_None(lst):
    if not isinstance(lst, list):
        return lst
    return [v for v in lst if v is not None]
    

TimeAndValue = namedtuple('TimeAndValue', ['time', 'value'])
