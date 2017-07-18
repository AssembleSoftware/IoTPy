import sys
import os
sys.path.append(os.path.abspath("../"))

from agent import Agent, InList
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from helper_functions.check_agent_parameter_types import *
from compute_engine import compute_engine
from helper_functions.recent_values import recent_values
import numpy as np


#-----------------------------------------------------------------------
# MAP: SINGLE INPUT STREAM, SINGLE OUTPUT STREAM
#-----------------------------------------------------------------------
def window_map_agent(func, in_stream, out_stream,
                     window_size, step_size,
                     state=None, call_streams=None, name=None,
                     *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from a single element of the input stream to a
           single element of the output stream
        in_stream: Stream
           The single input stream of this agent
        out_stream: Stream
           The single output streams of the agent
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
    check_map_agent_arguments(func, in_stream, out_stream, call_streams, name)
    check_window_and_step_sizes(name, window_size, step_size)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_in_streams = 1
    num_out_streams = 1

    # The transition function for the map agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
        # The map agent has a single input stream. So, the transition
        # operates on a single in_list.
        in_list = in_lists[0]
        # The map agent has a single output stream. So, the transition
        # outputs a single list.
        output_list = []
        list_length = in_list.stop - in_list.start
        if window_size > list_length:
            # No changes are made.
            return ([output_list], state, [in_list.start])

        # There is enough input data for at least one step.
        num_steps = int(1+(list_length - window_size)/step_size)
        output_list = [[]]*num_steps
        for i in range(num_steps):
            window = in_list.list[
                in_list.start+i*step_size : in_list.start+i*step_size+window_size]
            if state is None:
                output_list[i] = func(window, *args, **kwargs)
            else:
                output_list[i], state = func(window, state, *args, **kwargs)
        
        return ([output_list], state, [in_list.start+num_steps*step_size])
    # Finished transition

    # Create agent
    return Agent([in_stream], [out_stream], transition, state, call_streams, name)

def window_map(function, in_stream, window_size, step_size, state=None, *args, **kwargs):
    out_stream = Stream(function.__name__+in_stream.name)
    window_map_agent(function, in_stream, out_stream, window_size, step_size,
                     state, None, None, *args, **kwargs)
    return out_stream




#-----------------------------------------------------------------------
# MERGE: LIST OF INPUT STREAMS, SINGLE OUTPUT STREAM
#-----------------------------------------------------------------------
def window_merge_agent(func, in_streams, out_stream, 
                       window_size, step_size,
                       state=None, call_streams=None, name=None,
                       *args, **kwargs):
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
        num_steps = 1+(smallest_list_length - window_size)/step_size
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

def window_merge(function, in_streams, window_size, step_size, state=None, *args, **kwargs):
    out_stream = Stream(function.__name__+in_streams[0].name)
    window_merge_agent(function, in_streams, out_stream, window_size, step_size,
                       None, None, state, *args, **kwargs)
    return out_stream

#-----------------------------------------------------------------------
# SPLIT: SINGLE INPUT STREAM, LIST OF OUTPUT STREAMS
#-----------------------------------------------------------------------
def window_split_agent(func, in_stream, out_streams,
                       window_size, step_size,
                       state=None, call_streams=None, name=None,
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
        num_steps = 1+(list_length - window_size)/step_size
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
        output_list = [output_snapshot for output_snapshot in zip(*output_snapshots)]
        return (output_list, state, [in_list.start+num_steps*step_size])
    # Finished transition

    # Create agent
    return Agent([in_stream], out_streams, transition, state, call_streams, name)

def window_split(function, in_stream, window_size, step_size, state=None, *args, **kwargs):
    out_streams = []
    for i in range(num_out_streams):
        out_streams.append(Stream(func.__name__+in_stream.name+str(i)))
    window_split_agent(function, in_stream, out_streams, window_size, step_size,
                       None, None, state, *args, **kwargs)
    return out_stream

#-----------------------------------------------------------------------
# MANY: LIST OF INPUT STREAMS, LIST OF OUTPUT STREAMS
#-----------------------------------------------------------------------
def window_many_agent(func, in_streams, out_streams,
                 window_size, step_size,
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
    check_many_agent_arguments(func, in_streams, out_streams, call_streams, name)
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
    
        num_steps = 1+(smallest_list_length - window_size)/step_size
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
        output_lists = [output_snapshot for output_snapshot in zip(*output_snapshots)]
        return (output_lists, state, in_lists_start_values)
    # Finished transition

    # Create agent
    return Agent(in_streams, out_streams, transition, state, call_streams, name)

def window_many(func, in_streams, num_out_streams, state=None, args=[], kwargs={}):
    out_streams = []
    for i in range(num_out_streams):
        out_streams.append(Stream(func.__name__+ in_streams[0].name + str(i)))
    window_many_agent(func, in_streams, out_streams, state,
                     None, None, *args, **kwargs)
    return out_streams

#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#     WINDOW AGENT TESTS
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
def test_window_agents():

    q = Stream('q')
    qq = Stream('qq')
    r = Stream('r')
    s = Stream('s')
    t = Stream('t')
    u = Stream('u')
    v = Stream('v')
    w = Stream('w')
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
    a = Stream('a')
    b = Stream('b')
    c = Stream('c')
    yy = Stream('yy')
    zz = Stream('zz')
    
    #----------------------------------------------------------------
    # Test simple window map agent with the same window size and step size
    smap = window_map(function=sum, in_stream=r, window_size=4, step_size=4)
    window_map_agent(
        func=sum, in_stream=r, out_stream=s, window_size=4, step_size=4)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test window map agent with different window and step sizes
    window_map_agent(
        func=sum, in_stream=r, out_stream=t, window_size=3, step_size=2)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test window map agent with a NumPy function
    window_map_agent(
        func=np.mean, in_stream=r, out_stream=q,
        window_size=3, step_size=2, name='bb')
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test window map agent with arguments
    def map_with_args(window, addend):
        return np.mean(window) + addend
    window_map_agent(
        func=map_with_args, in_stream=r, out_stream=qq,
        window_size=3, step_size=2,
        addend=1)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test window map agent with user-defined function and no state
    window_map_agent(
        func=lambda v: sum(v)+1,
        in_stream=r, out_stream=u,
        window_size=4, step_size=4)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test window map agent with state
    def g(lst, state):
        return sum(lst)+state, sum(lst)+state
    window_map_agent(
        func=g, in_stream=r, out_stream=v,
        window_size=4, step_size=4, state=0)
    #----------------------------------------------------------------


    #----------------------------------------------------------------
    # Test window merge agent with no state
    def h(list_of_windows):
        return sum([sum(window) for window in list_of_windows])
    window_merge_agent(
        func=h, in_streams=[r,w], out_stream=x,
        window_size=3, step_size=3)
    #----------------------------------------------------------------


    #----------------------------------------------------------------
    # Test window merge agent with state
    def h_with_state(list_of_windows, state):
        return (sum([sum(window) for window in list_of_windows])+state,
                state+1)
    window_merge_agent(
        func=h_with_state, in_streams=[r,w], out_stream=a,
        window_size=3, step_size=3,
        state=0)
    #----------------------------------------------------------------


    #----------------------------------------------------------------
    # Test window split agent with no state
    def splt(window):
        return sum(window), max(window)

    window_split_agent(
        func=splt, in_stream=r, out_streams=[y,z],
        window_size=3, step_size=3)
    #----------------------------------------------------------------


    #----------------------------------------------------------------
    # Test window split agent with state
    def split_with_state(window, state):
        return (sum(window)+state, max(window)+state), state+1

    window_split_agent(
        func=split_with_state, in_stream=r, out_streams=[yy,zz],
        window_size=3, step_size=3, state=0)
    #----------------------------------------------------------------


    #----------------------------------------------------------------
    # Test window many-to-many with state and args
    def func_window_many_with_state_and_args(
            windows, state, cutoff):
        return (
            (max(max(windows[0]), max(windows[1]), cutoff, state),
            min(min(windows[0]), min(windows[1]), cutoff, state)),
            state+2)
    window_many_agent(
        func=func_window_many_with_state_and_args,
        in_streams=[r,w], out_streams=[b,c], state=0,
        window_size=3, step_size=3, cutoff=15)
            
    #----------------------------------------------------------------


    #----------------------------------------------------------------    
    r.extend(range(16))
    compute_engine.execute_single_step()
    assert recent_values(r) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    assert recent_values(s) == [0+1+2+3, 4+5+6+7, 8+9+10+11, 12+13+14+15]
    assert recent_values(smap) == recent_values(s)
    assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14]
    assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13]
    assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14]
    assert recent_values(u) == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1]
    assert recent_values(v) == [6, 28, 66, 120]
    assert recent_values(w) == []
    assert recent_values(x) == []
    assert recent_values(y) == [3, 12, 21, 30, 39]
    assert recent_values(yy) == [3, 13, 23, 33, 43]
    assert recent_values(z) == [2, 5, 8, 11, 14]
    assert recent_values(zz) == [2, 6, 10, 14, 18]
    assert recent_values(a) == []
    assert recent_values(b) == []
    assert recent_values(c) == []


    #----------------------------------------------------------------
    w.extend([10, 12, 14, 16, 18])
    compute_engine.execute_single_step()
    assert recent_values(r) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    assert recent_values(s) == [0+1+2+3, 4+5+6+7, 8+9+10+11, 12+13+14+15]
    assert recent_values(smap) == recent_values(s)
    assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14]
    assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13]
    assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14]
    assert recent_values(u) == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1]
    assert recent_values(v) == [6, 28, 66, 120]
    assert recent_values(w) == [10, 12, 14, 16, 18]
    assert recent_values(x) == [(0+1+2)+(10+12+14)]
    assert recent_values(y) == [3, 12, 21, 30, 39]
    assert recent_values(yy) == [3, 13, 23, 33, 43]
    assert recent_values(z) == [2, 5, 8, 11, 14]
    assert recent_values(zz) == [2, 6, 10, 14, 18]
    assert recent_values(a) == [39]
    assert recent_values(b) == [15]
    assert recent_values(c) == [0]
    

    #----------------------------------------------------------------    
    r.extend([10, -10, 21, -20])
    compute_engine.execute_single_step()
    assert recent_values(s) == [6, 22, 38, 54, 1]
    assert recent_values(smap) == recent_values(s)
    assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14,
                                 14+15+10, 10+(-10)+21]
    assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13, 13, 7]
    assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14, 14, 8]
    assert recent_values(u) == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1,
                                10 + (-10) + 21 + (-20) + 1]
    assert recent_values(v) == [6, 28, 66, 120, 121]
    assert recent_values(w) == [10, 12, 14, 16, 18]
    assert recent_values(x) == [(0+1+2)+(10+12+14)]
    assert recent_values(y) == [3, 12, 21, 30, 39, 15]
    assert recent_values(yy) == [3, 13, 23, 33, 43, 20]
    assert recent_values(z) == [2, 5, 8, 11, 14, 15]
    assert recent_values(zz) == [2, 6, 10, 14, 18, 20]
    assert recent_values(a) == [39]
    assert recent_values(b) == [15]
    assert recent_values(c) == [0]


    #----------------------------------------------------------------    
    w.append(20)
    compute_engine.execute_single_step()
    assert recent_values(s) == [6, 22, 38, 54, 1]
    assert recent_values(smap) == recent_values(s)
    assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14,
                                 14+15+10, 10+(-10)+21]
    assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13, 13, 7]
    assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14, 14, 8]
    assert recent_values(u) == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1,
                                10 + (-10) + 21 + (-20) + 1]
    assert recent_values(v) == [6, 28, 66, 120, 121]
    assert recent_values(w) == [10, 12, 14, 16, 18, 20]
    assert recent_values(x) == [(0+1+2)+(10+12+14), (3+4+5)+(16+18+20)]
    assert recent_values(y) == [3, 12, 21, 30, 39, 15]
    assert recent_values(yy) == [3, 13, 23, 33, 43, 20]
    assert recent_values(z) == [2, 5, 8, 11, 14, 15]
    assert recent_values(zz) == [2, 6, 10, 14, 18, 20]
    assert recent_values(a) == [39, 67]
    assert recent_values(b) == [15, 20]
    assert recent_values(c) == [0, 2]
    
    #----------------------------------------------------------------        
    r.extend([-1, 1, 0])
    compute_engine.execute_single_step()
    assert recent_values(s) == [6, 22, 38, 54, 1]
    assert recent_values(smap) == recent_values(s)
    assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14,
                                 14+15+10, 10+(-10)+21, 21-20-1, -1+1+0]
    assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13, 13, 7, 0, 0]
    assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14, 14, 8, 1, 1]
    assert recent_values(u) == [7, 23, 39, 55, 2]
    assert recent_values(v) == [6, 28, 66, 120, 121]
    assert recent_values(w) == [10, 12, 14, 16, 18, 20]
    assert recent_values(x) == [(0+1+2)+(10+12+14), (3+4+5)+(16+18+20)]
    assert recent_values(y) == [3, 12, 21, 30, 39, 15, 0]
    assert recent_values(yy) == [3, 13, 23, 33, 43, 20, 6]
    assert recent_values(z) == [2, 5, 8, 11, 14, 15, 21]
    assert recent_values(zz) == [2, 6, 10, 14, 18, 20, 27]
    assert recent_values(a) == [39, 67]
    assert recent_values(b) == [15, 20]
    assert recent_values(c) == [0, 2]

    #----------------------------------------------------------------
    #----------------------------------------------------------------
    # TEST WINDOW WITH STREAM ARRAY
    #----------------------------------------------------------------
    #----------------------------------------------------------------
    
    x = StreamArray('x')
    y = StreamArray('y')

    #----------------------------------------------------------------
    # Test window map agent with stream arrays and a NumPy function
    window_map_agent(
        func=np.mean, in_stream=x, out_stream=y,
        window_size=3, step_size=3, name='window map agent for arrays')
    #----------------------------------------------------------------

    x.extend(np.linspace(0.0, 11.0, 12))
    compute_engine.execute_single_step()
    assert np.array_equal(recent_values(x), np.linspace(0.0, 11.0, 12))
    assert np.array_equal(recent_values(y), np.array([1.0, 4.0, 7.0, 10.0]))

    
    x = StreamArray('x', dimension=2)
    y = StreamArray('y', dimension=2)
    z = StreamArray('z', dimension=2)
    a = StreamArray('a', dimension=2)
    b = StreamArray('b', dimension=2)
    c = StreamArray('c', dimension=2)
    d = StreamArray('d', dimension=2)
    p = StreamArray('p', dimension=2)
    q = StreamArray('q', dimension=2)
    r = StreamArray('r', dimension=2)
    s = StreamArray('s', dimension=2)
    
    

    #----------------------------------------------------------------
    # Test window map agent with stream arrays and a NumPy function
    def f(input_array):
        return np.mean(input_array, axis=0)
    window_map_agent(
        func=f, in_stream=x, out_stream=y,
        window_size=2, step_size=2, name='window map agent for arrays')
    #----------------------------------------------------------------

    
    #----------------------------------------------------------------
    # Test window map agent with state
    def g(lst, state):
        return sum(lst)+state, state+1
    window_map_agent(
        func=g, in_stream=x, out_stream=z,
        window_size=2, step_size=2, state=0)
    #----------------------------------------------------------------


    #----------------------------------------------------------------
    # Test window merge agent with state
    def h_array(list_of_windows, state):
        return (sum([sum(window) for window in list_of_windows])+state,
                state+1)
    window_merge_agent(
        func=h_array, in_streams=[x,a], out_stream=b,
        window_size=2, step_size=2,
        state=0)
    #----------------------------------------------------------------

        
    #----------------------------------------------------------------
    # Test window split agent with state
    def split_with_state(window, state):
        return [np.sum(window, axis=0)+state, np.max(window, axis=0)+state], \
          state+1.0

    window_split_agent(
        func=split_with_state, in_stream=x, out_streams=[c,d],
        window_size=2, step_size=2, state=0.0)
    #----------------------------------------------------------------

    
    #----------------------------------------------------------------
    # Test window many-to-many with state and args
    def func_window_many_with_state_and_args(
            windows, state, cutoff):
        max_value = np.maximum(
            np.max(windows[0], axis=0),
            np.max(windows[1], axis=0))
        max_value = np.maximum(max_value, cutoff)+state

        min_value = np.minimum(
            np.min(windows[0], axis=0),
            np.min(windows[1], axis=0))
        min_value = np.minimum(min_value, cutoff)+state
        
        return (max_value, min_value), state+1

    window_many_agent(
        func=func_window_many_with_state_and_args,
        in_streams= [x,a], out_streams=[r,s], state=0,
        window_size=2, step_size=2, cutoff=10)
    #----------------------------------------------------------------

    x.extend(np.array([[1., 5.], [7., 11.]]))
    a.extend(np.array([[0., 1.], [2., 3.]]))
    compute_engine.execute_single_step()
    np.array_equal(recent_values(y), np.array([(1.+7.)/2.0, (5.+11.)/2.]))
    np.array_equal(recent_values(z), np.array([6., 9.]))
    np.array_equal(recent_values(b), np.empty(shape=(0,2)))
    np.array_equal(
        recent_values(a), np.array(
            [((1. + 7.) + (0. + 2.)), ((5. + 11.) + (1. + 3.))]))
    np.array_equal(recent_values(c), np.array([[8., 16.]]))
    np.array_equal(recent_values(d), np.array([[7., 11.]]))
    np.array_equal(recent_values(r), np.array([[10., 11.]]))
    np.array_equal(recent_values(s), np.array([[0., 1.]]))


    a.extend(np.array([[0., 1.], [1., 0.]]))
    compute_engine.execute_single_step()
    np.array_equal(recent_values(y), np.array([(1.+7.)/2.0, (5.+11.)/2.]))
    np.array_equal(recent_values(z), np.array([6., 9.]))
    np.array_equal(recent_values(b), np.empty(shape=(0,2)))
    np.array_equal(
        recent_values(a), np.array(
            [((1. + 7.) + (0. + 2.)), ((5. + 11.) + (1. + 3.))]))
    np.array_equal(recent_values(c), np.array([[8., 16.]]))
    np.array_equal(recent_values(d), np.array([[7., 11.]]))
    np.array_equal(recent_values(r), np.array([[10., 11.]]))
    np.array_equal(recent_values(s), np.array([[0., 1.]]))
    

    x.extend(np.array([[14., 18.], [18., 30.], [30., 38.], [34., 42.]]))
    compute_engine.execute_single_step()
    np.array_equal(recent_values(y), np.array([[4., 8.], [16., 24.], [32., 40.]]))
    np.array_equal(recent_values(z), np.array([[8., 16.], [33., 49.], [66., 82.]]))
    np.array_equal(
        recent_values(a), np.array(
            [[10.0,20.0], [33.0, 49.0], [65.0, 81.0]]))
    np.array_equal(recent_values(c), np.array([[8., 16.], [33., 49.], [66., 82.]]))
    np.array_equal(recent_values(d), np.array([[7., 11.], [19., 31.],[36., 44.]]))
    np.array_equal(recent_values(r), np.array([[10., 11.], [19., 31.]]))
    np.array_equal(recent_values(s), np.array([[0., 1.], [1., 1.]]))

    return

if __name__ == '__main__':
    test_window_agents()
