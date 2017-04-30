import sys
import os
# sys.path.append(os.path.abspath("../"))
#sys.path.append(os.path.abspath("/helper_functions"))

from ..agent import Agent, InList
from ..stream import Stream, StreamArray
from ..stream import _no_value, _multivalue, _close
from ..helper_functions.check_agent_parameter_types import *
import types
import inspect
import numpy as np


#-----------------------------------------------------------------------
# MAP: SINGLE INPUT STREAM, SINGLE OUTPUT STREAM
#-----------------------------------------------------------------------
def window_map_agent(func, in_stream, out_stream,
                     window_size, step_size,
                     state=None, call_streams=None, name=None,
                     args=[], kwargs={}):
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
        num_steps = 1+(list_length - window_size)/step_size
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

def window(function, in_stream, window_size, step_size, state=None, args=[], kwargs={}):
    out_stream = Stream(function.__name__+in_stream.name)
    window_map_agent(function, in_stream, out_stream, window_size, step_size,
                     state, args=args, kwargs=kwargs)
    return out_stream



#-----------------------------------------------------------------------
# MERGE: LIST OF INPUT STREAMS, SINGLE OUTPUT STREAM
#-----------------------------------------------------------------------
def window_merge_agent(func, in_streams, out_stream, 
                       window_size, step_size,
                       state=None, call_streams=None, name=None,
                       args=[], kwargs={}):
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


#-----------------------------------------------------------------------
# SPLIT: SINGLE INPUT STREAM, LIST OF OUTPUT STREAMS
#-----------------------------------------------------------------------
def window_split_agent(func, in_stream, out_streams,
                       window_size, step_size,
                       state=None, call_streams=None, name=None,
                       args=[], kwargs={}):
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



#-----------------------------------------------------------------------
# MANY: LIST OF INPUT STREAMS, LIST OF OUTPUT STREAMS
#-----------------------------------------------------------------------
def window_many_agent(func, in_streams, out_streams,
                 window_size, step_size,
                 state=None, call_streams=None, name=None,
                 args=[], kwargs={}):
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

def dynamic_window_agent(func, in_stream, out_stream, state,
                         min_window_size, max_window_size, step_size,
                         args={}, kwargs={}):
 
    # Note: The agent has a SINGLE input stream, input_stream.
    # The agent has a SINGLE output stream, output_stream.
    # state is a list where state[0] is the current_window_size
    # state[1] is steady_state, a boolean which
    # indicates whether the max window size has been reached.
    # state[2] is reset, a boolean which is set to
    # True when the window is to be reset to the min window size.
    # state[3:] is defined by the user.
 
    # min_window_size, max_window_size, step_size are constants.
 
    # INVARIANT:
    #  max_window_size >= current_window_size >= min_window_size
     
    # The system is in steady state if and only if
    # the current window size is equal to its max value.
 
    # When the function f resets the window size, by returning
    # reset=True, the current window size is reset to its min value
    # if the system is in steady state.
 
    # If f returns reset=True while not in steady state, then
    # when the system next enters steady state, the current window
    # size is reset to the minimum window size.
 
    # Note that if f returns reset=True while not in steady state,
    # then reset only has an effect AFTER the system next reaches steady
    # state.
 
    # This function produces a single output stream.
    num_outputs = 1
     
    def transition(in_lists, state):
        # Get parameters from the state.
        current_window_size = state[0]
        steady_state = state[1]
        reset = state[2]
         
        # In case current window size was set to below its min value:
        current_window_size = max(current_window_size, min_window_size)
 
        # output_list is the list of messages that will be
        # sent on the output stream in this transition.
        output_list = list()
 
        # in_lists is a list of elements of type in_list, with
        # one in_list for each input stream. In this case, the
        # agent has only one input stream, and hence in_lists
        # contains only one element. We call it: input_in_list.
        # input is the list of messages in the input
        # stream that are the input for this transition.
        # start, stop are pointers to the input stream
        # where input begins at start and ends at stop.
        input_in_list = in_lists[0]
        start = input_in_list.start
        stop = input_in_list.stop
        input_list = input_in_list.list[start:stop]
        input_length = stop - start
        # input_list and input_length remain unchanged hereafter.
 
        # The current window is:
        # input[start_increment:start_increment+current_window_size]
 
        # start_increment is initially 0 and remains 0 until the
        # current window size equals the max window size, and after
        # that point the start_increment is increased by the step size.
        # The start of the window remains unchanged while the window
        # size increases from its min value to its max value. After
        # the window size reaches its max value, the window size remains
        # unchanged, and the window moves.
        start_increment = 0
 
         
        ####################
        # THE MAJOR LOOP   #
        ####################
        # Iterate while the end of the current window, i.e.,
        # start_increment + current_window_size falls within
        # the input list.
        while start_increment + current_window_size <= input_length:
            # At each iteration, either start_increment or
            # current_window_size (possibly both) increase.
            # CASE 1:
            # If the system is not in steady state before and
            # after the iteration, then during the iteration:
            # (a) the start of the window doesn't change
            # (b) the window size increases by the step size.
            # CASE 2:
            # If the system is in steady state before and
            # after the iteration, then during the iteration:
            # (a) the start of the window increases by the step size
            # (b) the window size remains unchanged at its max value.
            # CASE 3:
            # If the system is in steady state before the iteration,
            # and function f resets the window, then after the iteration
            # (a) the start of the window increases and
            # (b) window size is set to its min value. So the system is no
            # longer in steady state.
            # (c) reset is set to False.
            # CASE 4:
            # If the system is not in steady state before the iteration,
            # and reaches steady state after the transition because the
            # window size is increased to its max value, and if
            # reset is False, then after the iteration:
            # (a) the start of the window may increase, and 
            # (b) window size is its max value. So the system is now
            # in steady state.
            # CASE 5:
            # If the system is not in steady state before the iteration,
            # and reaches steady state after the transition because the
            # window size is increased to its max value, and if
            # reset is True, then after the iteration, Case 3 applies, i.e.,
            # (a) the start of the window increases, and 
            # (b) window size is set to its min value, and
            # (c) reset is set to False.
            # The only cases in which the end of the window, i.e.,
            # start_increment + current_window_size,
            # does NOT increase, are cases 3 and 5, i.e., the cases in
            # which reset changes from True to False.
            # In these cases, the end of the window does not move, but its
            # start increases. In the next iteration, the
            # end of the window will move, and this ensures that the loop
            # terminates.
             
            # input_window is the next window in the input stream.
            input_window = \
              input_list[start_increment:start_increment+current_window_size]
 
            #############################################
            # COMPUTE INCREMENTS TO THE OUTPUT STREAM.  #
            #############################################
             
            # Note: function f MUST return state (where state[0]
            # is the current_window_size and state[1] indicates whether
            # the steady state, i.e., current window size equals max value,
            # has been reached, and state[2], the reset value).
            # Update the state to reflect the new value of current_window_size
            state[0] = current_window_size
            state[1] = steady_state
            state[2] = reset
             
            # Compute the new output and the new state.
            output_increment, state = func(input_window, state, *args, **kwargs)
             
            # Get the new window parameters from the new state.
            # state[0] and state[1] should not normally be changed
            # by f().
            #current_window_size = state[0]
            #steady_state = state[1]
            reset = state[2]
 
            #################################
            # PROCESS THE NEW OUTPUT.       #
            #################################
            # Deal with special objects that should not be placed
            # on the output stream. 
            output_increment = remove_novalue_and_open_multivalue(
                [output_increment])
            # Place the output increment on the output list.
            # The messages in the output list will eventually
            # be sent on the output stream
            output_list.extend(output_increment)
 
            ################################################
            # UPDATE WINDOW SIZE AND WINDOW STARTING POINT #
            ################################################
             
            # CASES 1 or CASE 4: NOT STEADY STATE
            # In this case, reset has no effect.
            # This is because the window size is still increasing
            # and hasn't yet reached max_window_size.
 
            # The current window size is increased, but
            # the start increment does not change because
            # the starting point of the window remains
            # unchanged until the current window size increases
            # to the max window size. After that point,
            # the starting point of the window moves forward
            # by step size.
            if not steady_state:
                # CASE 1 or CASE 4
                if current_window_size + step_size >= max_window_size:
                    # CASE 4 or CASE 5:
                    # Reaches steady state after this iteration.
                    steady_state = True
                    # Move the starting point of the window forwards.
                    # If current_window_size == max_window_size - step_size then
                    # the starting point of the window doesn't change.
                    # If current_window_size == max_window_size then
                    # the starting point of the window moves forward by step_size.
                    start_increment += current_window_size + step_size - max_window_size
                    current_window_size = max_window_size
                    # If reset is True then CASE 5 holds. The actions for
                    # CASE 5 appear later, see "if reset and steady_state:"
                    # If reset is False, then CASE 4 holds and no further action occurs
                    # in this iteration.
                    continue
                else:
                    # CASE 1:
                    # Have not reached steady state yet.
                    # Increase current window size and leave the starting point
                    # of the window unchanged.
                    current_window_size += step_size
 
 
            # CASE 3: IN STEADY STATE, AND RESET. or
            # CASE 5: REACHED STEADY STATE, AND RESET.
            # Since reset is True, the agent has determined that
            # the window size should be reset to its minimum value.
 
            if reset and steady_state:
                steady_state = False
                reset = False
                # Assume the previous window was slice A:B.  Then
                # B-A = current_window_size
                # The new window is A':B. The end, B, of the window doesn't
                # move, but its start, A, moves forward to A', where A'
                # is computed from new window size, B - A' = min_window_size.
                # We have: B = start_increment + current_window_size
                # Therefore:
                # A' = start_increment + current_window_size - min_window_size
                # A = start_increment
                # Hence A' - A = current_window_size - min_window_size.
                # Move the start of the window forward by this amount.
                start_increment += current_window_size - min_window_size
                current_window_size = min_window_size
 
            # CASE 2: IN STEADY STATE, AND NO RESET.
            if (not reset) and steady_state:
                # Assert: not reset and steady_state
                # Move the window forward by step_size without changing
                # its size which remains max_window_size
                start_increment += step_size
 
        ###############################
        #  END OF THE MAJOR LOOP      #
        ###############################
             
 
        # The start pointer for the input stream is moved forward
        # to the starting point of the current window
        start += start_increment
        start_increment = 0
 
        # Update state
        state[0] = current_window_size
        state[1] = steady_state
        state[2] = reset
 
 
        return ([output_list], state, [start])
 
    # Create agent
    Agent([in_stream], [out_stream], transition, state)


#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#     WINDOW AGENT TESTS
#----------------------------r--------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
def test_window_agents():
    # Test simple window map agent with the same window size and step size
    r = Stream('r')
    s = Stream('s')
    smap = window(function=sum, in_stream=r, window_size=4, step_size=4)
    a = window_map_agent(
        func=sum, in_stream=r, out_stream=s, window_size=4, step_size=4,
        name='a')
    r.extend(range(16))
    assert s.stop == 4
    assert s.recent[:4] == [0+1+2+3, 4+5+6+7, 8+9+10+11, 12+13+14+15]
    
    r.extend([10, -10, 21, -20])
    assert s.stop == 5
    assert s.recent[:5] == [6, 22, 38, 54, 1]
    assert smap.recent[:smap.stop] == s.recent[:s.stop]    

    # Test window map agent with different window and step sizes
    t = Stream('t')
    b = window_map_agent(
        func=sum, in_stream=r, out_stream=t, window_size=3, step_size=2, name='b')
    assert t.stop == (20 - 3 + 1)/2
    assert t.recent[:t.stop] == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14,
                                 14+15+10, 10+(-10)+21]
    r.extend([-1, 1, 0])
    assert t.stop == 11
    assert t.recent[:t.stop] == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14,
                                 14+15+10, 10+(-10)+21, 21-20-1, -1+1+0]

    # Test window map agent with a NumPy function
    tt = Stream('tt')
    bb = window_map_agent(
        func=np.mean, in_stream=r, out_stream=tt,
        window_size=3, step_size=2, name='bb')
    assert tt.stop == 11
    assert tt.recent[:tt.stop] == [1, 3, 5, 7, 9, 11, 13, 13, 7, 0, 0]
    r.extend(range(1,4,1))
    assert tt.stop == 12
    assert tt.recent[:tt.stop] == [1, 3, 5, 7, 9, 11, 13, 13, 7, 0, 0, 1]

    # Test window map agent with user-defined function and no state
    def f(lst):
        return sum(lst)+1
    u = Stream('u')
    rr = Stream('rr')
    c = window_map_agent(
        func=f, in_stream=rr, out_stream=u, window_size=4, step_size=4, name='c')
    assert u.stop == 0
    rr.extend(range(16))
    assert u.stop==4
    assert u.recent[:4] == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1]
    rr.extend(range(16, 21, 1))
    assert u.stop==5
    assert u.recent[:5] == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1,
                            16+17+18+19+1]

    # Test window map agent with user-defined function and state
    def g(lst, state):
        return sum(lst)+state, sum(lst)+state
    v = Stream('v')
    v_in = Stream('v_in')
    d = window_map_agent(
        func=g, in_stream=v_in, out_stream=v, window_size=4, step_size=4,
        state=0, name='d')
    assert v.stop == 0
    v_in.extend(range(18))
    assert v.stop==4
    assert v.recent[:4] == [0+1+2+3, 0+1+2+3+4+5+6+7, 0+1+2+3+4+5+6+7+8+9+10+11,
                            0+1+2+3+4+5+6+7+8+9+10+11+12+13+14+15]
    v_in.extend(range(18, 22, 1))

    #------------------------------
    # Test window merge agent
    #------------------------------
    def h(list_of_windows):
        return sum([sum(window) for window in list_of_windows])
    w = Stream('w')
    x = Stream('x')
    w_prime = Stream('w_prime')
    e = window_merge_agent(
        func=h, in_streams=[r,w], out_stream=x, window_size=3, step_size=3,
        name='e')
    assert x.stop == 0
    w_prime.extend(range(16))
    assert x.stop == 0
    w.extend(range(100, 140, 4))
    assert x.stop == 3
    assert x.recent[:x.stop] == [315, 360, 405]

    def hh(list_of_windows):
        return sum([max(window) for window in list_of_windows])
    y = Stream('y')
    ee = window_merge_agent(
        func=hh, in_streams=[r,w], out_stream=y, window_size=3, step_size=3,
        name='ee')
    assert y.stop == 3
    assert y.recent[:y.stop] == [110, 125, 140]
    w.extend(range(140, 150, 4))
    assert y.stop == 4
    assert y.recent[:y.stop] == [110, 125, 140, 155]

    #------------------------------
    # test window split agent
    #------------------------------
    def splt(window):
        return sum(window), max(window)

    w = Stream('w')
    y = Stream('y')
    in_split = Stream('in_split')

    ff = window_split_agent(
        func=splt, in_stream=in_split, out_streams=[w,y], window_size=3, step_size=3,
        name='ff')
    assert w.stop == 0
    assert y.stop == 0
    in_split.extend(range(16))
    assert w.stop == 5
    assert y.stop == 5
    assert w.recent[:w.stop] == [3, 12, 21, 30, 39]
    assert y.recent[:y.stop] == [2, 5, 8, 11, 14]
    in_split.extend(range(16, 20, 1))
    assert w.recent[:w.stop] == [3, 12, 21, 30, 39, 48]
    assert y.recent[:y.stop] == [2, 5, 8, 11, 14, 17]

    def splt_np(window):
        return sum(window), np.mean(window)
    ww = Stream('ww')
    yy = Stream('yy')
    r_split_numpy = Stream('r split numpy')
    gg = window_split_agent(
        func=splt_np, in_stream=r_split_numpy, out_streams=[ww,yy], window_size=3, step_size=3,
        name='gg')
    assert ww.stop == 0
    assert yy.stop == 0
    r_split_numpy.extend(range(16))
    assert ww.stop == 5
    assert yy.stop == 5
    assert ww.recent[:ww.stop] == [3, 12, 21, 30, 39]
    assert yy.recent[:yy.stop] == [1, 4, 7, 10, 13]
    r_split_numpy.extend(range(16, 24, 1))
    assert ww.recent[:ww.stop] == [3, 12, 21, 30, 39, 48, 57, 66]
    assert yy.recent[:yy.stop] == [1, 4, 7, 10, 13, 16, 19, 22]

    def max_min_window(window):
        return max(window), min(window)
    
    zz = Stream('zz')
    aa = Stream('aa')
    r_max_min_window = Stream('max min window')
    hh = window_split_agent(
        func=max_min_window, in_stream=r_max_min_window, out_streams=[zz,aa],
        window_size=2, step_size=3,name='hh')
    assert zz.stop == 0
    assert aa.stop == 0
    r_max_min_window.extend(range(16))
    assert zz.stop == 5
    assert aa.stop == 5
    assert zz.recent[:zz.stop] == [1, 4, 7, 10, 13]
    assert aa.recent[:aa.stop] == [0, 3, 6, 9, 12]
    r_max_min_window.extend(range(16, 20, 1))
    assert zz.recent[:zz.stop] == [1, 4, 7, 10, 13, 16, 19]
    assert aa.recent[:aa.stop] == [0, 3, 6, 9, 12, 15, 18]

    bb = Stream('bb')
    cc = Stream('cc')
    in_bb_cc = Stream('in bb cc')
    ii = window_split_agent(
        func=max_min_window, in_stream=in_bb_cc, out_streams=[bb,cc], window_size=5, step_size=3,
        name='ii')
    assert bb.recent[:bb.stop] == []
    assert cc.recent[:cc.stop] == []
    in_bb_cc.extend(range(16))
    assert bb.stop == 4
    assert cc.stop == 4
    assert bb.recent[:bb.stop] == [4, 7, 10, 13]
    assert cc.recent[:cc.stop] == [0, 3, 6, 9]
    in_bb_cc.extend(range(16, 20, 1))
    assert bb.stop == 6
    assert cc.stop == 6
    assert bb.recent[:bb.stop] == [4, 7, 10, 13, 16, 19]
    assert cc.recent[:cc.stop] == [0, 3, 6, 9, 12, 15]
    

    # check window_many_agent
    def max_min_of_sum_of_windows(list_of_two_windows):
        window_0, window_1 = list_of_two_windows
        sum_0 = sum(window_0)
        sum_1 = sum(window_1)
        return max(sum_0, sum_1), min(sum_0, sum_1)

    def max_min_of_sum_of_windows_args(
            list_of_two_windows, multiplicand, addend):
        window_0, window_1 = list_of_two_windows
        sum_0 = sum(window_0)
        sum_1 = sum(window_1)
        return max(sum_0, sum_1)*multiplicand, min(sum_0, sum_1)+addend

    dd = Stream('dd')
    ee = Stream('ee')
    many_dd_ee_0 = Stream('input 0 for output dd ee')
    many_dd_ee_1 = Stream('input 1 for output dd ee')

    ddd = Stream('ddd')
    eee = Stream('eee')
    many_ddd_eee_0 = Stream('input 0 for output ddd eee')
    many_ddd_eee_1 = Stream('input 1 for output ddd eee')
    
    qqq = window_many_agent(
        func=max_min_of_sum_of_windows, in_streams=[many_dd_ee_0, many_dd_ee_1],
        out_streams=[dd, ee], window_size=7, step_size=5,
        name='qqq')

    qqq_args = window_many_agent(
        func=max_min_of_sum_of_windows_args, in_streams=[many_dd_ee_0, many_dd_ee_1],
        out_streams=[ddd, eee], window_size=7, step_size=5,
        name='qqq_args', args=[2], kwargs={'addend':10})
    
    assert dd.recent[:dd.stop] == []
    assert ee.recent[:ee.stop] == []
    assert ddd.recent[:ddd.stop] == []
    assert eee.recent[:eee.stop] == []

    many_dd_ee_0.extend(range(16))
    assert dd.recent[:dd.stop] == []
    assert ee.recent[:ee.stop] == []
    assert ddd.recent[:ddd.stop] == []
    assert eee.recent[:eee.stop] == []

    many_dd_ee_1.extend(range(100, 220, 10))
    assert dd.recent[:dd.stop] == [910, 1260]
    assert ee.recent[:ee.stop] == [21, 56]
    assert ddd.recent[:ddd.stop] == [1820, 2520]
    assert eee.recent[:eee.stop] == [31, 66]

    many_dd_ee_0.extend(range(16, 32, 1))
    assert dd.recent[:dd.stop] == [910, 1260]
    assert ee.recent[:ee.stop] == [21, 56]
    assert ddd.recent[:ddd.stop] == [1820, 2520]
    assert eee.recent[:eee.stop] == [31, 66]


    many_dd_ee_1.extend(range(220, 300, 10))
    assert dd.recent[:dd.stop] == [910, 1260, 1610]
    assert ee.recent[:ee.stop] == [21, 56, 91]
    assert ddd.recent[:ddd.stop] == [1820, 2520, 3220]
    assert eee.recent[:eee.stop] == [31, 66, 101]

    # Try a different window size
    many_in_2 = Stream('many in 2')
    many_in_3 = Stream('many in 3')
    many_out_2 = Stream('many out 2')
    many_out_3 = Stream('many out 3')
    rrr = window_many_agent(
        func=max_min_of_sum_of_windows, in_streams=[many_in_2, many_in_3],
        out_streams=[many_out_2, many_out_3], window_size=2, step_size=5,
        name='rrr')
    assert many_out_2.stop == 0
    assert many_out_3.stop == 0
    many_in_2.extend(range(4))
    many_in_3.extend(range(10, 100, 10))
    assert many_out_2.stop == 1
    assert many_out_3.stop == 1
    assert many_out_2.recent[:many_out_2.stop] == [30]
    assert many_out_3.recent[:many_out_3.stop] == [1]
    many_in_3.extend(range(100,200,10))
    assert many_out_2.stop == 1
    assert many_out_3.stop == 1
    assert many_out_2.recent[:many_out_2.stop] == [30]
    assert many_out_3.recent[:many_out_3.stop] == [1]
    many_in_2.extend(range(4, 10, 1))
    assert many_out_2.stop == 2
    assert many_out_3.stop == 2
    assert many_out_2.recent[:many_out_2.stop] == [30, 130]
    assert many_out_3.recent[:many_out_3.stop] == [1, 11]


    #-------------------------------------------------------------
    # TEST args and kwargs
    #-------------------------------------------------------------
    # Test simple window map agent with args
    def f_args(window, multiplicand):
        return sum(window)*multiplicand
    rr = Stream('rr')
    ss = Stream('ss')
    sss = Stream('sss')
    aa = window_map_agent(
        func=sum, in_stream=rr, out_stream=ss, window_size=4, step_size=4,
        name='aa')
    aaa = window_map_agent(
        func=f_args, in_stream=rr, out_stream=sss, window_size=4, step_size=4,
        name='aaa', args=[10])

    rr.extend(range(16))
    assert ss.recent[:ss.stop] == [6, 22, 38, 54]
    assert sss.recent[:sss.stop] == [60, 220, 380, 540]

    rr.append(20)
    assert ss.recent[:ss.stop] == [6, 22, 38, 54]
    assert sss.recent[:sss.stop] == [60, 220, 380, 540]

    rr.extend([21, 22, 23, 24])
    assert ss.recent[:ss.stop] == [6, 22, 38, 54, 86]
    assert sss.recent[:sss.stop] == [60, 220, 380, 540, 860]


    # Test simple window map agent with kwargs
    rr_kwargs = Stream('rr_kwargs')
    sss_kwargs = Stream('sss_kwargs')
    aaa_kwargs = window_map_agent(
        func=f_args, in_stream=rr_kwargs, out_stream=sss_kwargs,
        window_size=4, step_size=4,
        name='aaa_kwargs', kwargs={'multiplicand':10})

    rr_kwargs.extend(range(16))
    assert sss_kwargs.recent[:sss_kwargs.stop] == [60, 220, 380, 540]

    rr_kwargs.append(20)
    assert sss_kwargs.recent[:sss_kwargs.stop] == [60, 220, 380, 540]

    rr_kwargs.extend([21, 22, 23, 24])
    assert sss_kwargs.recent[:sss_kwargs.stop] == [60, 220, 380, 540, 860]


    # Test simple window map agent with args and kwargs
    def f_args_kwargs(window, multiplicand, addend):
        return sum(window)*multiplicand + addend
    
    rr_args_kwargs = Stream('rr_args_kwargs')
    ss_args_kwargs = Stream('ss_args_kwargs')
    sss_args_kwargs = Stream('sss_args_kwargs')
    
    aa_args_kwargs = window_map_agent(
        func=sum, in_stream=rr_args_kwargs, out_stream=ss_args_kwargs,
        window_size=4, step_size=4,
        name='aa_args_kwargs')
    aaa = window_map_agent(
        func=f_args_kwargs, in_stream=rr_args_kwargs, out_stream=sss_args_kwargs,
        window_size=4, step_size=4,
        name='aaa_args_kwargs', args=[10], kwargs={'addend':5})

    assert ss_args_kwargs.recent[:ss_args_kwargs.stop] == []
    assert sss_args_kwargs.recent[:sss_args_kwargs.stop] == []
    
    rr_args_kwargs.extend(range(16))
    assert ss_args_kwargs.recent[:ss_args_kwargs.stop] == [6, 22, 38, 54]
    assert sss_args_kwargs.recent[:sss_args_kwargs.stop] == [65, 225, 385, 545]

    rr_args_kwargs.append(20)
    assert ss_args_kwargs.recent[:ss_args_kwargs.stop] == [6, 22, 38, 54]
    assert sss_args_kwargs.recent[:sss_args_kwargs.stop] == [65, 225, 385, 545]

    rr_args_kwargs.extend([21, 22, 23, 24])
    assert ss_args_kwargs.recent[:ss_args_kwargs.stop] == [6, 22, 38, 54, 86]
    assert sss_args_kwargs.recent[:sss_args_kwargs.stop] == [65, 225, 385, 545, 865]

    return

if __name__ == '__main__':
    test_window_agents()
