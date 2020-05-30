from ..core.stream import Stream, StreamArray, _no_value, _multivalue
from ..core.agent import Agent, InList
# agent, stream are in ../core
# _no_value and _multivalue are in helper_control, but it is imported
# into stream, so we can import above
from ..helper_functions.recent_values import recent_values
# recent_values is in ../helper_functions

from .check_agent_parameter_types import *

"""
Functions in this module:
1. multi_element
2. multi_element_f
3. multi_list
4. multi_list_f
5. multi_window
6. multi_window_f

"""


def multi_element(func, in_streams, out_streams, state=None,
                       call_streams=None, name=None,
                       *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from an input list and args and kwargs to
           an output list
        in_streams: list of Stream
           The input streams of the agent
        out_streams: list of Stream
           The output streams of the agent
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_stream. A new value in any stream in this
           list causes a state transition of this agent.
        name: str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    check_multi_agent_arguments(func, in_streams, out_streams, call_streams, name)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_out_streams = len(out_streams)
    num_in_streams = len(in_streams)

    # The transition function for this agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
    
        # input_snapshots is a list of snapshots of the collection of input
        # streams.
        # Each snapshot in input_snapshots is a list with one value for each
        # input stream.
        # The j-th snapshot in input_snapshots is the snapshot at the j-th
        # time slice in this list of the input streams.
        input_snapshots = list(zip(*[v.list[v.start:v.stop] for v in in_lists]))
        # If the new input data is empty then return empty lists for
        # each output stream, and leave the state and the starting point
        # for each input stream unchanged.
        if not input_snapshots:
            return ([[]]*num_out_streams, state, [v.start for v in in_lists])

        # output_snapshots is a list of snapshots of the output streams.
        # The j-th value of output_snapshots is the output for
        # input_snapshots[j].
        if state is None:
            output_snapshots = \
              [func(input_snapshot, *args, **kwargs)
               for input_snapshot in input_snapshots]
        else:
            output_snapshots = [[]]*len(input_snapshots)
            for i in range(len(input_snapshots)):
                output_snapshots[i], state = \
                  func(input_snapshots[i], state, *args, **kwargs)

        check_func_output_for_multiple_streams(func, name, num_out_streams,
                                               output_snapshots)
                
        # output_snapshots[i] is a list whose each elements is a snapshot of the output
        # streams: each snapshot is a list with one element for each output stream.
        # zip them up to get  add_to_output_streamss where add_to_output_streams[j] is
        # a list containing the sequence of values to be added to output stream j.
        add_to_output_streams = [list(snapshot) for snapshot in list(zip(*output_snapshots))]

        return (add_to_output_streams, state,
                [v.start+len(input_snapshots) for v in in_lists])
    # Finished transition

    # Create agent
    return Agent(
        in_streams, out_streams, transition, state, call_streams,
        name)

def multi_element_f(func, in_streams, num_out_streams,
                state=None, *args, **kwargs):
    out_streams = [Stream() for _ in range(num_out_streams)]
    call_streams = None
    name=None
    multi_element(func, in_streams, out_streams, state,
                       call_streams, name, *args, **kwargs)
    return out_streams

def multi_list(func, in_streams, out_streams, state=None,
                    call_streams=None, name=None,
                    *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from an input list to an output list
        in_streams: list of Stream
           The input streams of the agent
        out_streams: list of Stream
           The output streams of the agent
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_stream. A new value in any stream in this
           list causes a state transition of this agent.
        name: Str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    # Check the types of the input lists for the transition.
    check_multi_agent_arguments(func, in_streams, out_streams, call_streams, name)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_out_streams = len(out_streams)
    num_in_streams = len(in_streams)

    # The transition function for this agent.
    def transition(in_lists, state):
        # Check the types of the input lists for the transition.
        check_in_lists_type(name, in_lists, num_in_streams)
        # smallest_list_length is the smallest of all the inputs for
        # this agent.
        smallest_list_length = \
          min(in_list.stop - in_list.start for in_list in in_lists)
        # Check for the null transition.
        if smallest_list_length == 0:
            # output_list is [] for each output stream.
            # So, output_lists = [[]]*num_out_streams
            # return (output_lists, state,
            #         [in_list.start+smallest_list_length
            #                           for in_list in in_lists])
            return ([[]]*num_out_streams, state,
                    [in_list.start for in_list in in_lists])

        # input_lists is the list of lists that this agent operates on
        # in this transition.
        input_lists = [in_list.list[in_list.start:in_list.start+smallest_list_length]
                       for in_list in in_lists]
        # Compute the output generated by this transition.
        if state is None:
            output_lists = func(input_lists, *args, **kwargs)
        else:
            ouput_lists, state = func(input_lists, state, *args, **kwargs)

        # Return: (1) output_lists, the list of outputs, one per
        #         output stream.
        #         (2) the new state and
        #         (3) the new starting pointer into this stream for
        #             this agent. Since this agent has read
        #             smallest_list_length number of elements, move
        #             its starting pointer forward by
        #             smallest_list_length. 
        return (output_lists, state,
                [in_list.start+smallest_list_length for in_list in in_lists])
    # Finished transition

    # Create agent with the following parameters:
    # 1. list of input streams. 
    # 2. list of output streams.
    # 3. transition function
    # 4. new state
    # 5. list of calling streams
    # 6. Agent name
    return Agent(in_streams, out_streams, transition, state, call_streams, name)

def multi_list_f(func, in_streams, num_out_streams, state=None, *args, **kwargs):
    out_streams = []
    for i in range(num_out_streams):
        out_streams.append(Stream(func.__name__+str(i)))
    multi_list(func, in_streams, out_streams, state,
                     None, None, *args, **kwargs)
    return out_streams


def multi_window(
        func, in_streams, out_streams, window_size, step_size,
        state=None, call_streams=None, name=None,
        *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from a list of windows with one window for each input stream
           to an output list containing a single element for each output stream.
        in_streams: list of Stream
           The list of input streams of the agent
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
    check_multi_agent_arguments(func, in_streams, out_streams, call_streams, name)
    check_window_and_step_sizes(name, window_size, step_size)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_in_streams = len(in_streams)
    num_out_streams = len(out_streams)

    # The transition function for this agent.
    def transition(in_lists, state=None):
        check_in_lists_type(name, in_lists, num_in_streams)
        output_lists = [ [] for _ in range(num_out_streams)]
        smallest_list_length = min(in_list.stop - in_list.start for in_list in in_lists)
        if window_size > smallest_list_length:
            # No changes
            return (output_lists, state, [in_list.start for in_list in in_lists])
    
        num_steps = 1+(smallest_list_length - window_size)//step_size
        output_snapshots = [[]]*num_steps
    
        for i in range(num_steps):
            windows = [in_list.list[
                in_list.start + i*step_size : in_list.start+ i*step_size + window_size]
                for in_list in in_lists]
            if state is None:
                output_snapshots[i] = func(windows, *args, **kwargs)
            else:
                output_snapshots[i], state = func(windows, state, *args, **kwargs)
        # Finished iteration: for i in range(num_steps)

        check_func_output_for_multiple_streams(
            func, name, num_out_streams,output_snapshots)

        in_lists_start_values = [
            in_list.start + num_steps*step_size for in_list in in_lists]
        # output_snapshots is a list of num_steps snapshots. Each snapshot is a
        # list of num_outwith one output for each output stream.
        # output_list is a list of num_out_streams lists. Each member of output_list
        # is a list
        #output_lists = [(output_snapshot) for output_snapshot in list(zip(*output_snapshots))]
        output_lists = [output_snapshot for output_snapshot in list(zip(*output_snapshots))]
        return (output_lists, state, in_lists_start_values)
    # Finished transition

    # Create agent
    return Agent(in_streams, out_streams, transition, state, call_streams, name)

def multi_window_f(
        func, in_streams, num_out_streams,
        window_size, step_size, state=None,
        *args, **kwargs):
    out_streams = []
    for i in range(num_out_streams):
        out_streams.append(Stream(func.__name__+ in_streams[0].name + str(i)))
    multi_window(func, in_streams, out_streams, window_size, step_size,
                state, call_streams=None, name=None, *args, **kwargs)
    return out_streams

