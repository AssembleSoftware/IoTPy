"""
This module consists of functions that split a single input stream
into multiple output streams.

Functions in the module:
   1. split_element
   2. split_element_f
   3. separate
   4. separate_f
   5. unzip
   6. unzip_f
   7. timed_unzip
   8. timed_unzip_f
   9. split_list
   10. split_list_f
   11. split_window
   12. split_window_f
   13. split_tuple

Split functions:
   1. split_element_f: a function returns a list with each element placed
      in a different stream.
   2. separate_f: separate_f is the inverse of mix (see merge.py). The
      elements of the input stream are pairs (i, v) and the value v is
      placed on the i-th output stream.
   3. unzip_f: unzip_f is the inverse of zip_stream (see
      merge.py). The elements of the input stream are lists and the
      i-th element of the list is placed on the i-th output stream.
   4. timed_unzip_f:
   5. split_list_f: function version of list split.

Agents:
   1. split_element: agent used by split_element_f
   2. separate: agent used by separate_f
   3. unzip: not used by any function in this module. It is
      retained only for backward compatibility.
   4. timed_unzip
   5. split_list
   6. split_window
   7. split_tuple (same as split_element with identity function for func) 
   
"""
from ..core.stream import Stream, _no_value
from ..core.agent import Agent, InList
# agent, stream,are in ../core
from .check_agent_parameter_types import *
# check_agent_parameter_types is in current directory

#-----------------------------------------------------------------------
# SPLIT: SINGLE INPUT STREAM, LIST OF OUTPUT STREAMS
#-----------------------------------------------------------------------
def split_element(
        func, in_stream, out_streams,
        state=None, call_streams=None, name=None,
        *args, **kwargs):
    """

    Parameters
    ----------
        func: function
           function from an input list and possibly state, args, kwargs
           to an output list. Length of output list must be length of
           out_streams.
        in_stream: Stream
           The single input stream of the agent
        out_streams: list of Stream
           The list of output streams of the agent
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_streams. A new value in any stream in this
           list causes a state transition of this agent.
        name: str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    func returns a list and the j-th element of the list is appended to a
    the j-th out_stream

    """
    check_split_agent_arguments(func, in_stream, out_streams, call_streams, name)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_out_streams = len(out_streams)
    num_in_streams = 1

    # The transition function for this agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
        in_list = in_lists[0]
        input_list = in_list.list[in_list.start:in_list.stop]
        # If the new input data is empty then return an empty list for
        # the single output stream, and leave the state and the starting
        # point for the single input stream unchanged.
        if input_list is None or len(input_list) == 0:
            return ([[]]*num_out_streams, state, [in_list.start])

        if state is None:
            output_snapshots = \
              [func(element, *args, **kwargs) for element in input_list]
        else:
            output_snapshots = [[]]*len(input_list)
            for i in range(len(input_list)):
                output_snapshots[i], state = \
                  func(input_list[i], state, *args, **kwargs)

        check_func_output_for_multiple_streams(
            func, name, num_out_streams, output_snapshots)

        add_to_output_streams = [list(snapshot) for snapshot in zip(*output_snapshots)]
        return (add_to_output_streams, state, [in_list.start+len(input_list)])
    # Finished transition

    # Create agent
    return Agent([in_stream], out_streams, transition, state, call_streams, name)


def split_element_f(function, in_stream, num_out_streams, state=None, *args,
                 **kwargs):
    """
    split_element_f returns out_streams, a list of num_out_streams
    streams.  The function, with the specified state, args and kwargs,
    is applied to the elements of the input stream. The return value
    of the function must be a list of length num_out_streams. The i-th
    value of the returned list is placed in the i-th output stream.

    Parameters
    ----------
        in_stream: Stream
           The stream that will be split
        num_out_streams: int
           The number of output streams.
        state: object
           function operates on a state, args, and kwargs
    Returns
    -------
        out_streams: List of Stream
           The output streams generated by split_element_f
    Uses
    -------
        * split_element

    """
    out_streams = [Stream() for _ in range(num_out_streams)]
    split_element(
        function, in_stream, out_streams, state, *args, **kwargs) 
    return out_streams

#-----------------------------------------------------------------------
# SEPARATE: SINGLE INPUT STREAMS, LIST OF OUTPUT STREAM
#-----------------------------------------------------------------------
def separate(in_stream, out_streams, name=None):
    """
    separate is the inverse of mix (see merge.py). Each
    element of the input stream is a pair (j, v). 
    The value v is placed on the j-th output stream.

    Parameters
    ----------
        in_stream: Stream
           The single input stream of the agent
        out_streams: list of Stream
           The list of output streams of the agent
        name: str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.
 
    """
    def f(x):
        j, v = x
        j = int(j)
        lst = [_no_value] * len(out_streams)
        lst[j] = v
        return lst
     
    return split_element(
        func=f, in_stream=in_stream, out_streams=out_streams, name=name)

unmix = separate

def separate_f(in_stream, num_out_streams):
    """
    separate_f returns out_streams, a list of num_out_streams
    streams. separate_f is the inverse of mix (see merge.py). The
    elements of the input stream are pairs (i, v) and the value v is
    placed on the i-th output stream. 

    Parameters
    ----------
        in_stream: Stream
           The stream that will be split
        num_out_streams: int
           The number of output streams.

    Returns
    -------
        out_streams: List of Stream
           The output streams generated by split_element_f
    Uses
    -------
        * separate

    """
    out_streams = [Stream() for _ in range(num_out_streams)]
    separate(in_stream, out_streams)
    return out_streams

unmix_f = separate_f
 
#-----------------------------------------------------------------------
# UNZIP: SINGLE INPUT STREAMS, LIST OF OUTPUT STREAM
#-----------------------------------------------------------------------
def unzip(in_stream, out_streams, name=None):
    """
    Parameters
    ----------
        in_stream: Stream
           The single input stream of the agent
        out_streams: list of Stream
           The list of output streams of the agent
        name: str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.
    Uses
    ----
        split_element

    Each element of in_stream is a list; the j-th element in this list
    is placed in the j-th output stream. 
 
    """
    def f(lst):
        if len(lst) < len(out_streams):
            lst.extend([None] * (len(out_streams) - len(lst)))
        elif len(lst) > len(out_streams):
            lst = lst[0:len(out_streams)]
        return lst
     
    return split_element(f, in_stream, out_streams)

def unzip_f(in_stream, num_out_streams):
    """
    unzip_f returns out_streams, a list of num_out_streams
    streams. unzip_f is the inverse of zip_stream (see
    merge.py). The elements of the input stream are lists of length
    num_out_streams and the i-th element of the list is placed on the
    i-th output stream. 

    Parameters
    ----------
        in_stream: Stream
           The stream that will be split
        num_out_streams: int
           The number of output streams.

    Returns
    -------
        out_streams: List of Stream
           The output streams generated by split_element_f
    Uses
    -------
        * unzip

    """
    out_streams = [Stream() for _ in range(num_out_streams)]
    unzip(in_stream, out_streams)
    return out_streams

def timed_unzip(in_stream, out_streams):
    """
    timed_unzip unzips the elements of in_stream into each stream
    in out_streams. timed_unzip is the inverse of timed_zip (see
    merge.py). The elements of the input stream are pairs (t, v) where
    v is a list of length num_out_streams. The i-th element of the
    list, with the timestamp t is placed on the i-th output stream if
    and only if v is not None.

    Parameters
    ----------
        in_stream: Stream
           The stream that will be split
        out_streams: list of Stream
           The list of output streams.

    Returns
    -------
        agent
    Uses
    -------
        * split_element

    """
    num_out_streams = len(out_streams)
    def f_time_unzip(timed_element):
        timestamp, messages = timed_element
        if len(messages) > num_out_streams:
            messages = messages[:num_out_streams]
        elif len(messages) < num_out_streams:
            messages.extend([None]*(num_out_streams - len(messages)))
        output_list = [
            _no_value if message is None else (timestamp, message) for
            message in messages]
        return output_list
    return split_element(f_time_unzip, in_stream, out_streams)


def timed_unzip_f(in_stream, num_out_streams):
    out_streams = [Stream() for _ in range(num_out_streams)]
    timed_unzip(in_stream, out_streams)
    return out_streams

#-----------------------------------------------------------------------
# LIST SPLIT: SINGLE INPUT STREAM, LIST OF OUTPUT STREAMS
#-----------------------------------------------------------------------
def split_list(func, in_stream, out_streams, state=None,
               call_streams=None, name='split_list',
               *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from an input list to a list of lists (one
              list per output stream).
        in_stream: Stream
           The single input stream of the agent
        out_streams: list of Stream
           The list of output streams of the agent
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_streams. A new value in any stream in this
           list causes a state transition of this agent.
        name: Str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    # Check the types of the input lists for the transition.
    check_split_agent_arguments(func, in_stream, out_streams,
                                call_streams, name)
    # Check the number of arguments in func, the transition function.
    check_num_args_in_func(state, name, func, args, kwargs)
    num_out_streams = len(out_streams)
    num_in_streams = 1

    # The transition function for this agent.
    def transition(in_lists, state):
        # Check the types of the input lists for the transition.
        check_in_lists_type(name, in_lists, num_in_streams)
        # This agent has only one input stream. Get its only in_list.
        in_list = in_lists[0]
        # input_list is the slice of the input stream that this agent
        # is working on.
        # in_list is an object of type InList, and it consists of an
        # arbitrarily long list (in_list.list), and pointers to where
        # this agent is starting to read the list (in_list.start), and
        # where the list ends (in_list.stop). 
        input_list = in_list.list[in_list.start:in_list.stop]

        # Check for the null transition.
        # If the new input data is empty then return an empty list for
        # the single output stream, and leave the state and the starting
        # point for the single input stream unchanged.
        if len(input_list) == 0:
            # output_list is [] for each output stream.
            # So, output_lists = [[]]*num_out_streams
            # return (output_lists, state,
            #         [in_list.start+len(input_list)]
            return ([[]]*num_out_streams, state, [in_list.start])

        # Compute the output generated by this transition.
        if state is None:
            output_lists = func(input_list, *args, **kwargs)
        else:
            output_lists, state = func(input_list, state, *args, **kwargs)

        assert len(output_lists) == num_out_streams, \
          'Error in list-split transition function of agent {0}.'\
          ' The number, {1}, of output lists does not equal the number, {2},'\
          ' of output streams.'.format(name, len(output_lists), num_out_streams)

        # Return: (1) output_lists, the list of outputs, one per
        #         output stream.
        #         (2) the new state and
        #         (3) the new starting pointer into this stream for
        #             this agent. Since this agent has read the entire
        #             input_list, move its starting pointer forward by
        #             the length of the input list.
        return (output_lists, state, [in_list.start+len(input_list)])
    # Finished transition

    # Create agent with the following parameters:
    # 1. list of input streams. split has a single input stream.
    # 2. list of output streams.
    # 3. transition function
    # 4. new state
    # 5. list of calling streams
    # 6. Agent name
    return Agent([in_stream], out_streams, transition, state, call_streams, name)
    
def split_list_f(func, in_stream, num_out_streams, state=None, *args, **kwargs):
    out_streams = []
    for i in range(num_out_streams):
        out_streams.append(Stream(func.__name__+in_stream.name+str(i)))
    split_list(func, in_stream, out_streams, state,
                     None, None, *args, **kwargs)
    return out_streams


def split_window(
        func, in_stream, out_streams, window_size, step_size,
        state=None, call_streams=None, name='split_window',
        *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from a window to a list containing a single
           element for each output stream.
        in_stream: Stream
           The single input stream of the agent
        out_streams: list of Stream
           The list of output streams of the agent
        window_size: int
           Positive integer. The size of the moving window
        step_size: int
           Positive integer. The step size of the moving window
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_streams. A new value in any stream in this
           list causes a state transition of this agent.
        name: Str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    check_split_agent_arguments(func, in_stream, out_streams, call_streams, name)
    check_window_and_step_sizes(name, window_size, step_size)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_in_streams = 1
    num_out_streams = len(out_streams)

    # The transition function for this agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)

        # The split agent has a single input stream. So, the transition
        # operates on a single in_list.
        in_list = in_lists[0]
        # The split agent has a list of output streams. So, the transition
        # outputs a list for each output stream.
        output_lists = [ [] for _ in range(num_out_streams)]
        list_length = in_list.stop - in_list.start
        if window_size > list_length:
            return (output_lists, state, [in_list.start])
                
        # Assert: Each input stream has enough elements for a window operation.
        # num_steps is the number of window operations that can be
        # carried out with the given numbers of unprocessed elements
        # in the input streams.
        num_steps = 1+(list_length - window_size)//step_size
        output_snapshots = [[]]*num_steps
        for i in range(num_steps):
            window = in_list.list[
                in_list.start+i*step_size : in_list.start+i*step_size+window_size]
            if state is None:
                output_snapshots[i] = func(window, *args, **kwargs)
            else:
                output_snapshots[i], state = func(window, state, *args, **kwargs)
                
        check_func_output_for_multiple_streams(
            func, name, num_out_streams, output_snapshots)
        # output_snapshots is a list of num_steps snapshots. Each snapshot is a
        # list of num_outwith one output for each output stream.
        # output_list is a list of num_out_streams lists. Each member of output_list
        # is a list
        output_list = [(output_snapshot) for output_snapshot in zip(*output_snapshots)]
        return (output_list, state, [in_list.start+num_steps*step_size])
    # Finished transition

    # Create agent
    return Agent([in_stream], out_streams, transition, state, call_streams, name)

def split_window_f(func, in_stream, num_out_streams,
                   window_size, step_size, state=None, *args, **kwargs):
    out_streams = []
    for i in range(num_out_streams):
        out_streams.append(Stream(func.__name__+in_stream.name+str(i)))
    split_window(func, in_stream, out_streams, window_size, step_size,
                 state=state, *args, **kwargs)
    return out_streams

def split_tuple(in_stream, out_streams):
    split_element(lambda x: x, in_stream, out_streams)



def split_signal(
        func, in_stream, out_streams, state=None, name=None,
        *args, **kwargs):
    """
    This agent executes func when it reads a new value on
    in_stream. The function func operates on kwargs and possibly
    a state. Note that func does not operate on elements of in_stream.
    This is because in_stream serves merely as a signaling mechanism
    that informs this agent that it needs to execute a step, i.e.,
    call func.

    Parameters
    ----------
        func: function
           function that operates on kwargs and possibly the state.
        in_stream: Stream or StreamArray
           The single input stream of this agent
        out_streams: list of Stream or StreamArray
           The list of output streams of the agent
        state: object
           The state of the agent
        name: Str
           Name of the agent created by this function.
        *args, **kwargs:
           Positional and keyword parameters, if any, for func.
    Returns
    -------
        Agent.
         The agent created by this function.
    Uses
    ----
       * Agent
       * check_map_agent_arguments

    """
    # The transition function for this agent.
    def transition(in_lists, state):
        num_in_streams = 1
        check_in_lists_type(name, in_lists, num_in_streams)
        in_list = in_lists[0]
        input_list = in_list.list[in_list.start:in_list.stop]
        # If the new input data is empty then return an empty list for
        # the single output stream, and leave the state and the starting
        # point for the single input stream unchanged.
        if input_list is None or len(input_list) == 0:
            return ([[]], state, [in_list.start])
        # In the following output is (typically) a list of _no_value
        # when the variables listed in kwargs do not change, and is a
        # list of any value other than _no_value (e.g. 1)  if any
        # variable in kwargs does change.
        # The length of the list, output, must be the same as the length
        # of the list, out_streams.
        else:
            if state is None:
                output = func(*args, **kwargs)
            else:
                output, state = func(state, *args, **kwargs)
        assert len(output) == len(out_streams)
        output_list = [[v] for v in output]

        return (output_list, state, [in_list.start+len(input_list)])
    # Finished transition

    call_streams = None
    # Create agent
    return Agent([in_stream], out_streams, transition, state, call_streams, name)
