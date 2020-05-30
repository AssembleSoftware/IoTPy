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
from ..core.agent import Agent, InList
from ..core.stream import StreamArray, Stream 
from ..core.helper_control import _no_value, _multivalue
# agent, stream, helper_control are in ../core
from ..helper_functions.recent_values import recent_values
#  recent_values is in ../helper_functions
from .check_agent_parameter_types import *
# check_agent_parameter_types is in current folder

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
