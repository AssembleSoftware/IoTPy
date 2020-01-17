"""
This module has the agent type iot and iot_merge. These
agents are different from the other agent types in
IoTPy/IoTPy/agent_types because the functions wrapped by
iot and iot_merge use the Stream class. By contrast,
the functions wrapped by other agent types only use
standard data types, such as list and int. If you want
to wrap a function from a standard Python library then
you can't use iot or iot_merge because standard library
functions don't use the Stream class. If you want to
use iot or iot_merge then you must call a standard
library function, and extend an output stream with the
result of the call.

The iot agent has only two parameters: func and in_stream.
The iot_merge agent also has two parameters func and
in_streams where in_streams is a list of input streams.
Typically, func uses positional or keyword arguments
specified in *args or **kwargs, respectively.
These arguments may include streams and agents.

"""
import numpy as np
import sys
import os
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("/agent_types"))
from agent import Agent, InList
from stream import Stream, StreamArray
from helper_control import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from run import run


def iot(func, in_stream, *args, **kwargs):
    """
    iot is called whenever in_stream is extended. iot invokes
    func and passes it a slice into the input stream. The
    slice begins at an index previously specified by func.
    The arguments of func are the slice and *args, **kwargs.

    func must return an index into the slice. This index
    indicates that func will not read elements of the input
    stream earlier than the index. The index is the
    displacement from the start of the slice. For example,
    if func returns 2 then it will no longer read the input
    stream upto the first 2 elements of the slice.
    
    Parameters
    ----------
        func: function
           function on a single array or a single list and
           *args, **kwargs. Note that func does not operate
           on a single element of a list or an array. func
           operates on the entire list or array.
        in_stream: Stream
            The input stream of this function, i.e., the
            input stream of the agent executing this
            function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    # The transition function for the map agent.
    def transition(in_lists, state):
        # STEP 1. GET THE SLICES -- LISTS OR ARRAYS -- INTO STREAMS. 
        # A is a list or an array
        A = in_lists[0].list[in_lists[0].start : in_lists[0].stop]

        # STEP 2. CALL FUNC.
        # new_start is a nonnegative number. It specifies that this
        # agent will no longer read elements of in_stream before
        # index in_lists[0].start + new_start
        new_start = func(A, *args, **kwargs)
        assert isinstance(new_start, int), \
          'funct in iot() must return a nonnegative integer' \
          ' but it returned {0}'.format(new_start)
        assert new_start >= 0, \
          ' func in iot() must return nonnegative integer, but it '\
          ' returned {0} : '.format(new_start)

        # STEP 3. RETURN VALUES FOR STANDARD AGENT
        # Return (i) list of output stream: this is empty.
        # (ii) next state: this is unchanged.
        # (iii) list of new pointers into input streams.
        return ([], state, [new_start+in_lists[0].start])
    # Finished transition

    # Create agent
    # This agent has no output streams, and so out_streams is [].
    return Agent([in_stream], [], transition)

def iot_merge(func, in_streams, *args, **kwargs):
    """
    Similar to iot except that the primary argument of iot_merge
    is a list of lists or a list of arrays whereas the primary
    argument of iot is a single list or a single array.

    iot_merge is called when any of its input streams is extended.
    func operates on a primary argument (in addition to *args and
    **kwargs) which is a list of lists, one list for each input
    stream. This list is a slice of the input stream from the
    point previously specified by func to the most recent value.

    func must carry out all the computation; all iot_merge does
    is invoke func and pass it a list of slices into the input
    streams.

    func must return a list of pointers with one pointer for each
    input stream. As in iot, a pointer is an index into an input
    list. This pointer indicates that func will not read elements
    of the stream earlier than the pointer. The next time that
    func is called, it will be passed a slice into its input stream
    starting from this pointer.
    
    
    Parameters
    ----------
        func: function
           function on a single element
        in_streams: List of Stream
           The input streams of this func (i.e., agent executing func.)
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    # The transition function for the map agent.
    def transition(in_lists, state):
        # 1. GET THE SLICES -- LISTS OR ARRAYS -- INTO STREAMS. 
        # A_list is a list of lists or a list of arrays.
        A_list = [in_list.list[in_list.start : in_list.stop]
                  for in_list in in_lists]

        # 2. CALL FUNC.
        # func must return a list of indices (new_starts) into
        # the input lists that indicate that it will no longer
        # read elements earlier than the pointers.
        new_starts = func(A_list, *args, **kwargs)
        assert isinstance(new_starts, list), \
          'func in iot_merge() must return list of new starting indices'\
          ' into the input lists but function returns {0}'.\
          format(new_starts)
        assert len(new_starts) == len(A_list), \
          'func in iot_merge() must return one starting index for each' \
          ' input list. The number of input lists is {0} ' \
          ' and the number of values returned is {1}'.\
          format(len(A_list), len(new_starts))
        for new_start in new_starts:
            assert isinstance(new_start, int) and (new_start >= 0), \
              ' func in iot_merge must return a nonnegative integer for each' \
              ' input list. One of the values returned is {0}'.\
              format(new_start)

        # 3. RETURN VALUES FOR STANDARD AGENT
        for i in range(len(new_starts)):
            new_starts[i] += in_lists[i].start
        # Return (i) list of output stream: this is empty.
        # (ii) next state: this is unchanged.
        # (iii) new pointers into input streams.
        return ([], state, new_starts)
    # Finished transition

    # Create agent
    # This agent has no output streams, and so out_streams is [].
    return Agent(in_streams, [], transition)



#---------------------------------------------------------------------------
#     TESTS
#---------------------------------------------------------------------------

def test_iot():
    x = StreamArray(dtype=int)
    y = StreamArray(dtype=int)
    z = StreamArray(dtype=int)
    u = StreamArray(dtype=int)
    v = StreamArray(dtype=int)
    
    def f(A, y, z):
        """
        Function wrapped by an iot agent. The first parameter
        'A' is an array obtained from the input stream of the
        agent. The other parameters, y and z, are positional
        arguments (*args) of the function.

        The function returns a pointer into the input stream.
        In this example, each call to the function processes
        the entire input array 'A' and so the function returns
        len(A).

        """
        y.extend(2*A)
        z.extend(3*A)
        # Return a pointer into the input array.
        return len(A)

    def g(A, u, v):
        """
        Parameters are similar to f.

        """
        u.extend(A+A)
        v.extend(A**2)
        return len(A)

    # Create agents that wrap functions f and g.
    iot(f, x, y, z)
    iot(g, x, u, v)

    # Extend stream x with an array
    x.extend(np.arange(5, dtype=int))
    run()
    assert np.array_equal(recent_values(y), 2*np.arange(5, dtype=int))
    assert np.array_equal(recent_values(z), 3*np.arange(5, dtype=int))
    assert np.array_equal(recent_values(u), 2*np.arange(5, dtype=int))
    assert np.array_equal(recent_values(v), np.arange(5, dtype=int)**2)

    # Extend stream x with another array
    x.extend(np.arange(5, 10, dtype=int))
    run()
    assert np.array_equal(recent_values(y), 2*np.arange(10, dtype=int))
    assert np.array_equal(recent_values(z), 3*np.arange(10, dtype=int))
    assert np.array_equal(recent_values(u), 2*np.arange(10, dtype=int))
    assert np.array_equal(recent_values(v), np.arange(10, dtype=int)**2)

def test_iot_merge():
    x = StreamArray(dtype=float)
    y = StreamArray(dtype=float)
    z = StreamArray(dimension=2, dtype=float)
    
    def f(A_list, z):
        """
        f is the function wrapped by an iot_merge agent.
        A_list is a list of arrays. A_list[j] is the input array obtained
        from the j-th input stream of the agent that wraps f.
        z is the positional argument of f. z is an output stream that is
        extended by f.

        The agent completes reading n_rows elements of each array in
        A_list where n_rows is the number of elements in the smallest
        array. So, the function returns n_rows.

        """
        n_rows = min([len(A) for A in A_list])
        n_cols = len(A_list)
        out = np.column_stack((A_list[0][:n_rows], A_list[1][:n_rows]))
        z.extend(out)
        return [n_rows for A in A_list]

    # Create the agent by wrapping function f.
    # A_list has two arrays from streams x and y.
    # z is a keyword argument for f.
    iot_merge(f, [x, y], z=z)
    # Extend stream x with [0, 1, 2, 3, 4]
    x.extend(np.arange(5, dtype=float))
    run()
    assert np.array_equal(recent_values(x), np.array(np.arange(5, dtype=float)))
    assert np.array_equal(recent_values(x), np.array([0., 1., 2., 3., 4.]))
    assert np.array_equal(recent_values(y), np.zeros(shape=(0,), dtype=float))
    assert np.array_equal(recent_values(z), np.zeros(shape=(0, 2), dtype=float))
    y.extend(np.arange(100, 107, dtype=float))
    run()
    assert np.array_equal(recent_values(x), np.array([0., 1., 2., 3., 4.]))
    assert np.array_equal(recent_values(y), np.array([100., 101., 102., 103., 104., 105., 106.]))
    assert np.array_equal(
        recent_values(z), np.array(
            [[  0., 100.], [  1., 101.], [  2., 102.], [  3., 103.], [  4., 104.]]))

    
class sliding_window_test(object):
    def __init__(self, func, in_stream, out_stream, window_size, step_size):
        self.func = func
        self.in_stream = in_stream
        self.out_stream = out_stream
        self.window_size = window_size
        self.step_size = step_size
        iot(func=self.extend, in_stream=self.in_stream)
    def extend(self, A):
        if len(A) < self.window_size:
            return 0
        else:
            num_steps = int(1+(len(A) - self.window_size)//self.step_size)
            self.output = np.zeros(num_steps)
            for i in range(num_steps):
                window = A[i*self.step_size : i*self.step_size+self.window_size]
                self.output[i] = self.func(window)
            self.out_stream.extend(self.output)
            return num_steps*self.step_size
def test_iot_class():
    x = StreamArray(dtype=int)
    y = StreamArray(dtype=float)
    sw = sliding_window_test(
        func=np.sum, in_stream=x, out_stream=y, window_size=5, step_size=2)
    x.extend(np.arange(10, dtype=int))
    run()
    assert np.array_equal(recent_values(y), np.array([10., 20., 30.]))
    x.extend(np.arange(10, 20, dtype=int))
    run()
    assert np.array_equal(recent_values(y), np.array([10., 20., 30.,
                                                      40., 50., 60.,
                                                      70., 80.]))

if __name__ == '__main__':
    test_iot()
    test_iot_merge()
    test_iot_class()
    
    
    
