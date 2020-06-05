"""
This module consists of functions that merge multiple input streams
into a single output stream.

Functions in the module:
   1. zip_map 
   2. zip_map_f
   3. zip_stream: same as zip_map with no function on merged stream.
   4. zip_stream_f
   5. merge_asynch: asynch merge which keeps track of which stream an
                    item came from
   6. merge_asynch_f
   5. mix: same as merge_asynch with no function on merged stream
   6. mix_f
   7. blend: applies func to elements as they arrive. Does not keep
             track of which input stream an item came from.
   8. blend_f
   9. merge_window
   10. merge_window_f
   11. merge_list: func operates on a list of lists (one list for each
                input stream, and returns a list.
   12. merge_list_f
   13. timed_zip
   14. timed_zip_f
   15. timed_mix
   16. timed_mix_f
   17. zip_map_list: same as merge_list

The output stream of a merge agent is declared before calling the 
agent whereas the merge functions return the output stream.

Agents:
   1. zip_map.
   This agent zips its input streams and then executes a function
   on the zipped stream to produce a single output stream.
   The merge function operates on a list (one element per input stream)
   to produce a single elemnt of the output stream.
   2. merge_asynch is the agent used by mix. It puts elements that
   appear in its input streams, in the order in which they appear, on
   its output stream.
   3. blend is the agent used by blend_f. It is merge_asynch 
   followed by a map.
   4. merge_window has the same structure as merge_element except that
   a window on each of the input streams is merged into a single
   element of the output stream (whereas in merge_element a single
   element --- not a window --- from each input stream is merged to
   form a single element of the output stream). The function in
   merge_window operates on a list of windows, i.e. a list of lists,
   with one window per input stream, to produce a single element of
   the output stream. The sizes of all windows are the same and all
   window step sizes are the same.
   5. merge_list is similar to merge_element except that the merge
   function is a function from a list of lists (one list per input
   stream) to a single list (for the output stream).
   6. timed_zip zips timed streams to produce a timed output stream.
   The elements of the output stream are pairs (t, lst) where lst is
   a list of elements, one from each input stream, where each element
   has timestamp t.
   
   
Merge functions:
   1. zip_stream is similar to zip in Python except that it operates on
      streams rather than lists. It is the function version of merge_element
   2. zip_map is map_stream(zip_stream()), i.e., first zip then map the
      result. This is the same as merge_element_f, and I use the
      name zip_map because it's more appropriate.
   3. mix is an asynchronous merge of the input streams. The elements of the
      output stream identify the input streams that generated the
      elements.
   4. blend_f is an asynch merge followed by a map. It is a functional
   version of blend.
   5. merge_window_f is the functional form of the merge_window agent.
   6. merge_list_f is the functional form of the merge_list agent.
   7. timed_zip_f is the functional form of timed_zip.
   

   
"""
from .check_agent_parameter_types import *
# check_agent_parameter_types is in the current folder
from ..core.stream import Stream, _no_value
from ..core.agent import Agent
# agent and stream are in ../core; _no_value is in helper_control but
# is imported inside stream

def zip_map(
        func, in_streams, out_stream,
        state=None, call_streams=None, name='zip_map',
        *args, **kwargs): 
    """
    Parameters
    ----------
        func: function
           function from a list (and possibly state,
           args and kwargs) to a single element of
           the output stream. The list has one element
           from each input stream.
        in_streams: list of Stream
           The list of input streams of the agent
        out_stream: Stream
           The single output stream of the agent
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

    """
    check_merge_agent_arguments(func, in_streams, out_stream, call_streams, name)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_in_streams = len(in_streams)

    # The transition function for this agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
        # input_snapshots is a list of snapshots.
        # Each snapshot is a list containing one element for each
        # input stream.
        input_snapshots = list(zip(*[v.list[v.start:v.stop] for v in in_lists]))
        # If the new input data is empty then return empty lists for
        # each output stream, and leave the state and the starting point
        # for each input stream unchanged.
        if not input_snapshots:
            return ([[]], state, [v.start for v in in_lists])

        # output_list[i] will be set to the result of func applied
        # to the list consisting of the i-th value in 
        # each of the input streams
        output_list = [ [] for lst in input_snapshots]

        for i, snapshot in enumerate(input_snapshots):
            assert isinstance(snapshot, list) or isinstance(snapshot, tuple)
            if state is None:
                output_list[i] = func(snapshot, *args, **kwargs)
            else:
                output_list[i], state = func(snapshot, state, *args, **kwargs)

            if output_list[i] is None: output_list[i] = []

        return ([output_list], state, [v.start+len(input_snapshots) for v in in_lists])
    # Finished transition

    # Create agent
    return Agent(in_streams, [out_stream], transition, state, call_streams, name)

def zip_map_f(func, in_streams, state=None, *args, **kwargs):
    """
    zip_map returns out_stream, a stream obtained by applying function,
    with the specified state, args and kwargs, to the elements
    obtained by zipping the input streams.

    Parameters
    ----------
        in_streams: list of Stream
           The list of input streams that are zipped
        state: object
           function operates on a state, args, and kwargs
    Returns
    -------
        out_stream: Stream
           The output stream generated by zip_map
    Uses
    -------
        * merge_element

    """
    out_stream = Stream('output of zip')
    zip_map(func, in_streams, out_stream, state, *args, **kwargs)
    return out_stream


def zip_stream(in_streams, out_stream):
    """
    zip_stream returns out_stream, a stream obtained by zipping the
    input streams. zip_stream is similar to zip.

    Parameters
    ----------
        in_streams: list of Stream
           The list of input streams that are zipped
        state: object
           function operates on a state, args, and kwargs
    Returns
    -------
        out_stream: Stream
           The output stream generated by zip_stream
    Uses
    -------
        * merge_element

    """
    return zip_map(lambda v: v, in_streams, out_stream)

def zip_stream_f(in_streams):
    out_stream = Stream('output of zip_stream')
    zip_stream(in_streams, out_stream)
    return out_stream

def zip_streams(in_streams, out_stream):
    """
    Merely because zip_streams and zip_stream
    (plural and singular) are convenient for use.

    """
    return zip_stream(in_streams, out_stream)

def zip_map_sink(
        func, in_streams,
        state=None, call_streams=None, name='zip_map_sink',
        *args, **kwargs): 
    """
    Same as zip_map except that the encapsulated function returns
    nothing or None for zip_map_sink whereas the encapsulated
    function returns an element of the output stream for zip_map.

    Parameters
    ----------
        func: function
           function from a list (and possibly state,
           args and kwargs) to a single element of
           the output stream. The list has one element
           from each input stream.
        in_streams: list of Stream
           The list of input streams of the agent
        out_stream: Stream
           The single output stream of the agent
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

    """
    check_num_args_in_func(state, name, func, args, kwargs)
    num_in_streams = len(in_streams)

    # The transition function for this agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
        # input_snapshots is a list of snapshots.
        # Each snapshot is a list containing one element for each
        # input stream.
        input_snapshots = list(zip(*[v.list[v.start:v.stop] for v in in_lists]))
        # If the new input data is empty then return empty lists for
        # each output stream, and leave the state and the starting point
        # for each input stream unchanged.
        if not input_snapshots:
            return ([], state, [v.start for v in in_lists])

        for i, snapshot in enumerate(input_snapshots):
            assert isinstance(snapshot, list) or isinstance(snapshot, tuple)
            if state is None:
                func(snapshot, *args, **kwargs)
            else:
                state = func(snapshot, state, *args, **kwargs)

        return ([], state, [v.start+len(input_snapshots) for v in in_lists])
    # Finished transition

    # Create agent
    return Agent(in_streams, [], transition, state, call_streams, name)



####################################################
# OPERATIONS ON ASYCHRONOUS INPUT STREAMS
####################################################
def merge_asynch(
        func, in_streams, out_stream, state=None,
        call_streams=None, name='merge_asynch',
        *args, **kwargs): 
    """
    Parameters
    ----------
        func: function
           function from a pair (i, v) where i is the
           index into a stream in the list in_streams,
           and v is an element in that stream. The
           function returns an element of the output
           stream.
        in_streams: list of Stream
           The list of input streams of the agent
        out_stream: Stream
           The single output stream of the agent
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

    """
    def transition(in_lists, state):
        for v in in_lists:
            # loop through each in_stream with one in_list
            # per in_stream
            if v.stop > v.start:
                # In the following, input_list is the list of new 
                # values on an in_stream
                input_list = v.list[v.start:v.stop]
        output_list = []
        
        # If the input data is empty, i.e., if v.stop == v.start for all
        # v in in_lists, then return empty lists for  each output stream, 
        # and leave the state and the starting point for each input
        # stream unchanged.
        if all(v.stop <= v.start for v in in_lists):
            return ([output_list], state, [v.start for v in in_lists])

        # Assert at least one input stream has unprocessed data.
        for stream_number, v in enumerate(in_lists):
            # v is an in_list
            # if v.stop <= v.start then skip this input stream
            # because no new messages have arrived on this stream.
            if v.stop > v.start:
                # In the following,input_list is the list of new values
                # on the input stream with index stream_number
                input_list = v.list[v.start:v.stop]

                # Append each unread element in this input stream,
                # and its stream_number, to output_list
                if state is None:
                    for element in input_list:
                        output_list.append(
                            func((stream_number, element), *args, **kwargs))
                else:
                    for element in input_list:
                        output_element, state = func(
                            (stream_number, element), state, *args, **kwargs)
                        output_list.append(output_element)

        return ([output_list], state, [v.stop for v in in_lists])

    # Create agent
    return Agent(in_streams, [out_stream], transition, state, call_streams, name)

def merge_asynch_f(
        func, in_streams, state=None, *args, **kwargs):
    out_stream = Stream('output of merge_asynch_f')
    merge_asynch(func, in_streams, out_stream, state, *args, **kwargs)
    return out_stream

def mix(in_streams, out_stream):
    return merge_asynch(lambda v: v, in_streams, out_stream, name='mix')

def mix_f(in_streams):
    out_stream = Stream('mix')
    mix(in_streams, out_stream)
    return out_stream

def timed_mix(in_streams, out_stream):
    def f(index_and_time_value_pair, state):
        index, time_value_pair = index_and_time_value_pair
        timestamp, element_value = time_value_pair
        if timestamp <= state:
            return _no_value, state
        else:
            next_state = timestamp
            return (timestamp, (index, element_value)), next_state

    merge_asynch(f, in_streams, out_stream, state=-1)

def timed_mix_f(in_streams):
    out_stream = Stream('timed mix')
    timed_mix(in_streams, out_stream)
    return out_stream

def blend(func, in_streams, out_stream, state=None,
          call_streams=None, name='blend', *args, **kwargs):
    """
     Parameters
    ----------
        func: function
           function from an input list and args and kwargs to
           an output list
        in_streams: list of Stream
           The list of input streams of the agent
        out_stream: Stream
           The single output stream of the agent
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

    """
    def transition(in_lists, state):
        output_list = []
        
        # If the input data is empty, i.e., if v.stop == v.start for all
        # v in in_lists, then return empty lists for  each output stream, 
        # and leave the state and the starting point for each input
        # stream unchanged.
        if all(v.stop <= v.start for v in in_lists):
            return ([output_list], state, [v.start for v in in_lists])

        # Assert at least one input stream has unprocessed data.
        for stream_number, v in enumerate(in_lists):
            # v is an in_list
            # if v.stop <= v.start then skip this input stream
            # because no new messages have arrived on this stream.
            if v.stop > v.start:
                # In the following,input_list is the list of new values
                # on the input stream with index stream_number
                input_list = v.list[v.start:v.stop]

                # Add each unread element in this input stream, with the
                # stream_number, to output_list.
                if state == None:
                    for element in input_list:
                        output_list.append(func(element, *args, **kwargs))
                else:
                    for element in input_list:
                        next_output, state = func(element, state, *args, **kwargs)
                        output_list.append(next_output)

        return ([output_list], state, [v.stop for v in in_lists])

    # Create agent
    return Agent(in_streams, [out_stream], transition, state, call_streams, name)


def blend_f(func, in_streams, state=None, *args, **kwargs):
    out_stream = Stream('output of blend')
    blend(func, in_streams, out_stream, state, *args, **kwargs)
    return out_stream

def weave(in_streams, out_stream):
    func=lambda v: v
    blend(func, in_streams, out_stream)

def weave_f(in_streams):
    out_stream = Stream('output of weave')
    weave(in_streams, out_stream)
    return out_stream
    

#-----------------------------------------------------------------------
# MERGE_WINDOW: LIST OF INPUT STREAMS, SINGLE OUTPUT STREAM
#-----------------------------------------------------------------------
def merge_window(
        func, in_streams, out_stream, window_size, step_size,
        state=None, initial_value=None, call_streams=None,
        name='merge_window', *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from a list of windows with one window per input stream
           to a single element of the output stream.
        in_streams: list of Stream
           The list of input streams of the agent
        out_stream: Stream
           The single output streams of the agent
        window_size: int
           Positive integer. The size of the moving window
        step_size: int
           Positive integer. The step size of the moving window
        state: object
           The state of the agent
        initial_value: None or object
           If initial_value is None then the output stream starts
           after its first window is full. Otherwise, the output
           stream starts with window_size elements of initial_value.
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
    check_merge_agent_arguments(func, in_streams, out_stream, call_streams, name)
    check_window_and_step_sizes(name, window_size, step_size)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_in_streams = len(in_streams)
    num_out_streams = 1

    if initial_value is not None:
        out_stream.extend([initial_value for _ in range(window_size)])

    # The transition function for this agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
        # The merge agent has a single output stream. So, the transition
        # outputs a single list.
        output_list = []
        # The merge agent has a list of input streams. So, the transition
        # operates on in_lists which is a list of elements, each of type InList.
        smallest_list_length = \
          min(in_list.stop - in_list.start for in_list in in_lists)

        if window_size > smallest_list_length:
            # No changes are made.
            return ([output_list], state,
                    [in_list.start for in_list in in_lists])

        # There is enough input for at least one step.
        num_steps = 1+(smallest_list_length - window_size)//step_size
        output_list = [[]]*num_steps

        for i in range(num_steps):
            # windows is a list with a window for each input stream.
            windows = [in_list.list[
                in_list.start+i*step_size : in_list.start+i*step_size+window_size]
                for in_list in in_lists]
            if state is None:
                output_list[i] = func(windows, *args, **kwargs)
            else:
                output_list[i], state = func(windows, state, *args, **kwargs)
        # Finished iteration: for i in range(num_steps)

        return ([output_list], state,
                [in_list.start+num_steps*step_size for in_list in in_lists])
    # Finished transition

    # Create agent
    return Agent(in_streams, [out_stream], transition, state, call_streams, name)

def merge_window_f(func, in_streams, window_size, step_size, state=None, *args, **kwargs):
    out_stream = Stream(func.__name__+in_streams[0].name)
    merge_window(func, in_streams, out_stream, window_size, step_size,
                       state, *args, **kwargs)
    return out_stream

def merge_multiple_windows(
        func, in_streams, out_stream, window_sizes, step_sizes,
        state=None, call_streams=None, name='merge_multiple_windows',
        *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from a list of windows with one window per input stream
           to a single element of the output stream. The windows in the list
           of windows may be of different sizes.
        in_streams: list of Stream
           The list of input streams of the agent
        out_stream: Stream
           The single output streams of the agent
        window_sizes: list of int
           Positive integers. The sizes of the moving windows with one
           window for each in_stream.
        step_sizes: list of int
           Positive integers. The step sizes of the moving windows with
           one step size for each in_stream.
        state: object
           The state of the agent
        name: Str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    num_in_streams = len(in_streams)
    num_out_streams = 1

    # The transition function for this agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
        # The merge agent has a single output stream. So, the transition
        # outputs a single list.
        output_list = []
        num_steps_list = [0] * num_in_streams
        for index in range(num_in_streams):
            list_length = in_lists[index].stop - in_lists[index].start
            if window_sizes[index] > list_length:
                # No changes are made because not enough new data in
                # in_stream
                return ([output_list], state,
                        [in_list.start for in_list in in_lists])
            # There is enough new data in this in_stream for
            # at least one step.
            # num_steps_list[index] is the number of steps that can be
            # taken based only on the stream: in_streams[index].
            num_steps_list[index] = (1 +
                                (list_length - window_sizes[index])//
                                step_sizes[index])
        # num_steps is a positive integer. It is the number of steps
        # that can be taken based on all the input streams.
        num_steps = min(num_steps_list)

        # Compute the element of the output stream for each step
        # for a total of num_steps.
        output_list = [[]]*num_steps
        for i in range(num_steps):
            # windows is a list with a window for each input stream.
            windows = [in_lists[index].list[
                in_lists[index].start+i*step_sizes[index] :
                in_lists[index].start+i*step_sizes[index] + window_sizes[index]]
                for index in range(num_in_streams)]
            if state is None:
                output_list[i] = func(windows, *args, **kwargs)
            else:
                output_list[i], state = func(windows, state, *args, **kwargs)
        # Finished iteration: for i in range(num_steps)

        return ([output_list], state,
                [in_lists[index].start+num_steps*step_sizes[index]
                 for index in range(num_in_streams)])
    # Finished transition

    # Create agent
    return Agent(in_streams, [out_stream], transition, state, call_streams, name)


#-----------------------------------------------------------------------
# MERGE_LIST: LIST OF INPUT STREAMS, SINGLE OUTPUT STREAM
#-----------------------------------------------------------------------
def merge_list(func, in_streams, out_stream, state=None,
                        call_streams=None, name=None,
                        *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from a list of lists (one list per input stream) to an output list
        in_streams: list of Stream
           The list of input streams of the agent
        out_stream: Stream
           The single output stream of the agent
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
    # Check the arguments and output error messages if argument types
    # and numbers are incorrect.
    check_merge_agent_arguments(func, in_streams, out_stream, call_streams, name)
    check_num_args_in_func(state, name, func, args, kwargs)

    num_in_streams = len(in_streams)

    # The transition function for this agent.
    def transition(in_lists, state):
        # Check the types of the input lists for the transition.
        check_in_lists_type(name, in_lists, num_in_streams)
        # smallest_list_length is the smallest of all the inputs for
        # this agent.
        smallest_list_length = \
          min(in_list.stop - in_list.start for in_list in in_lists)
        # Check for null transition.
        if smallest_list_length == 0:
            # output_list is []
            # return ([output_list], state,
            #         [in_list.start+smallest_list_length
            #                           for in_list in in_lists])
            return ([[]], state,
                    [in_list.start for in_list in in_lists])
        # input_lists is the list of lists that this agent operates on
        # in this transition.
        input_lists = [in_list.list[
            in_list.start:in_list.start+smallest_list_length]
            for in_list in in_lists]

        # Compute the output generated by this transition.
        if state is None:
            output_list = func(input_lists, *args, **kwargs)
        else:
            ouput_list, state = func(input_lists, state, *args, **kwargs)

        # Return: (1) the list of outputs, one per output stream. The
        #         merge_agent has a single output list.
        #         (2) the new state and
        #         (3) the new starting pointer into this stream for
        #             this agent. Since this agent has read the entire
        #             input_list, move its starting pointer forward by
        #             the length of the input list.
        return ([output_list],
                state,
                [in_list.start+smallest_list_length for in_list in in_lists])
    # Finished transition

    # Create agent with the following parameters:
    # 1. list of input streams. merge has a list, instreams, of input
    # streams. 
    # 2. list of output streams. merge has a single output stream.
    # 3. transition function
    # 4. new state
    # 5. list of calling streams
    # 6. Agent name
    return Agent(in_streams, [out_stream], transition, state, call_streams, name)

zip_map_list = merge_list

def merge_list_f(func, in_streams, state=None, *args, **kwargs):
    out_stream = Stream('merge_list_f:' + func.__name__)
    merge_list(func, in_streams, out_stream, state, None, None, *args, **kwargs)
    return out_stream

zip_map_list_f = merge_list_f


def timed_zip(in_streams, out_stream, call_streams=None, name=None):
    """
    Parameters
    ----------
        in_streams: list of Stream
           The list of input streams of the agent
        out_stream: Stream
           The single output stream of the agent
        call_streams: list of Stream
           The list of call_streams. A new value in any stream in this
           list causes a state transition of this agent.
        name: Str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.
    Notes
    -----
        Each stream in in_streams must be a stream of tuples or lists
        or NumPy arrays where element[0] is a time and where time is
        a total order. Each stream in in_stream must be strictly
        monotonically increasing in time.
        
        out_stream merges the in_streams in order of time. An element
        of out_stream is a list where element[0] is a time T and
        element[1] is a list consisting of all elements of in in_streams
        that have time T.

    Examples
    --------

    """
    # Check types of arguments
    check_list_of_streams_type(list_of_streams=in_streams,
                          agent_name=name, parameter_name='in_streams')
    check_stream_type(name, 'out_stream', out_stream)
    check_list_of_streams_type(list_of_streams=call_streams,
                          agent_name=name, parameter_name='call_streams')

    num_in_streams = len(in_streams)
    indices = range(num_in_streams)

    # The transition function for this agent.
    def transition(in_lists, state):
        # Check the types of in_lists
        check_in_lists_type(name, in_lists, num_in_streams)

        # input_lists is the list of lists that this agent can operate on
        # in this transition.
        input_lists = [in_list.list[in_list.start:in_list.stop]
                       for in_list in in_lists]
        # pointers is a list where pointers[i] is a pointer into the i-th
        # input lists
        pointers = [0 for i in indices]
        # stops is a list where pointers[i] must not exceed stops[i].
        stops = [len(input_lists[i]) for i in indices]
        # output_list is the single output list for this agent. 
        output_list = []

        while all(pointers[i] < stops[i] for i in indices):
            # slice is a list with one element per input stream.
            # slice[i] is the value pointed to by pointers[i].
            slice = [input_lists[i][pointers[i]] for i in indices]
            # slice[i][0] is the time field for slice[i].
            # earliest_time is the earliest time pointed to by pointers.
            earliest_time = min(slice[i][0] for i in indices)
            # slice[i][1:] is the list of fields other than the time
            # field for slice[i].
            # next_output_value is a list with one element for
            # each input stream.
            # next_output_value[i] is the empty list if the time
            # for slice[i] is later than earliest time. If the time
            # for slice[i] is the earliest time, hen next_output_value[i]
            # is the list of all the non-time fields.
            next_output_value = [slice[i][1] if slice[i][0] == earliest_time
                           else None  for i in indices]
            # increment pointers for this indexes where the time was the
            # earliest time.
            pointers = [pointers[i]+1 if slice[i][0] == earliest_time
                        else pointers[i]  for i in indices]

            # Make next_output a list consisting of a time: the earliest time
            # followed by a sequence of lists, one for each input stream.
            # Each list in this sequence consists of the non-time fields.
            next_output = [earliest_time]
            next_output.append(next_output_value)

            # output_list has an element for each time in the input list.
            output_list.append(next_output)

        # Return: (1) output_lists, the list of outputs, one per
        #         output stream. This agent has a single output stream
        #         and so output_lists = [output_list]
        #         (2) the new state; the state is irrelevant for this
        #             agent because all it does is merge streams.
        #         (3) the new starting pointer into this stream for
        #             this agent. Since this agent has read
        #             pointers[i] number of elements in the i-th input
        #             stream, move the starting pointer for the i-th input
        #             stream forward by pointers[i].
        return [output_list], state, [in_lists[i].start+pointers[i] for i in indices]
    # Finished transition

    # Create agent
    state = None
    # Create agent with the following parameters:
    # 1. list of input streams. 
    # 2. list of output streams. This agent has a single output stream and so
    #         out_streams is [out_stream].
    # 3. transition function
    # 4. new state (irrelevant for this agent), so state is None
    # 5. list of calling streams
    # 6. Agent name
    return Agent(in_streams, [out_stream], transition, state, call_streams, name)

def timed_zip_f(list_of_streams):
    out_stream = Stream('output of timed zip')
    timed_zip(list_of_streams, out_stream)
    return out_stream


