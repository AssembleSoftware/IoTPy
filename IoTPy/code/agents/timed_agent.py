""" This module has timed_zip and timed_window which are described
in the manual documentation.

"""
import sys
import os
scriptpath = "../"
sys.path.append(os.path.abspath(scriptpath))

from agent import Agent, InList
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from compute_engine import compute_engine
from helper_functions.check_agent_parameter_types import *
from helper_functions.recent_values import recent_values

import time

####################################################
#                     TIMED ZIP
####################################################

def timed_zip_agent(in_streams, out_stream,
                    name=None, call_streams=None,
                    no_value_symbol=None):
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

        # input_lists is the list of lists that this agent operates on
        # in this transition.
        input_lists = [in_list.list[in_list.start:in_list.stop]
                       for in_list in in_lists]

        # pointers is a list where pointers[i] is a pointer into the i-th
        # list in input_lists
        pointers = [0 for i in indices]
        
        # stops is a list where pointers[i] must not exceed stops[i].
        stops = [len(input_lists[i]) for i in indices]
        
        # output_list is the single output list for this agent. 
        output_list = []

        while all(pointers[i] < stops[i] for i in indices):
            # slice is a list with one element per input stream.
            # slice[i] is the value pointed to by pointers[i] in the
            # i-th input list.
            slice = [input_lists[i][pointers[i]] for i in indices]

            # slice[i][0] is the time field for slice[i].
            # earliest_time is the earliest time pointed to by the
            # pointers of all the input streams.
            try:
                earliest_time = min(slice[i][0] for i in indices)
            except:
                raise ValueError('slice should be a list')
            # slice[i][1:] is the list of fields other than the time field
            # for slice[i].
            # next_output_value is a list with one element for
            # each input stream.
            # next_output_value[i] is None if the time
            # for slice[i] is later than earliest time. If the time
            # for slice[i] is the earliest time, then next_output_value[i]
            # is the list of all the non-time fields.
            next_output_value = []
            next_pointers = []
            for i in indices:
                assert earliest_time <= slice[i][0]
                if slice[i][0] > earliest_time:
                    next_output_value.append(no_value_symbol)
                    next_pointers.append(pointers[i])
                else:
                    assert earliest_time == slice[i][0]
                    next_output_value.append(slice[i][1])
                    next_pointers.append(pointers[i]+1)
            pointers = next_pointers

            # Make next_output a list consisting of a time: the earliest time
            # followed by a sequence of lists, one for each input stream.
            # Each list in this sequence consists of the non-time fields.
            next_output = [earliest_time]
            if earliest_time <= state[0]:
                print 'earliest time', earliest_time
                print 'state', state
                print 'state[0]', state[0]
                raise ValueError('earliest_time')
            state = (earliest_time, pointers)
            #next_output.append(next_output_value)
            next_output.extend(next_output_value)
            #assert len(next_output) == 2

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
    state = (-1, [])
    # Create agent with the following parameters:
    # 1. list of input streams. 
    # 2. list of output streams. This agent has a single output stream and so
    #         out_streams is [out_stream].
    # 3. transition function
    # 4. new state (irrelevant for this agent), so state is None
    # 5. list of calling streams
    # 6. Agent name
    return Agent(in_streams, [out_stream], transition, state, call_streams, name)

def timed_zip(list_of_streams):
    out_stream = Stream('output of timed zip')
    timed_zip_agent(list_of_streams, out_stream)
    return out_stream



###############################################################
#                    TIMED_WINDOW
###############################################################
def timed_window_agent(
        func, in_stream, out_stream,
        window_duration, step_time, window_start_time=0,
        state=None, call_streams=None, name=None,
        args=[], kwargs={}):

    # All windows with start times earlier than window_start_time
    # have already been processed.
    # state is the state of the underlying agent.
    # Augment the state with the start time of the
    # window.
    state = (window_start_time, state)

    def transition(in_lists, state):
        # The map agent has a single input stream. So, the transition
        # operates on a single in_list.
        in_list = in_lists[0]
        # The map agent has a single output stream. So, the transition
        # outputs a single list.
        output_list = []
        # input_list is the list extracted from in_list
        input_list = in_list.list[in_list.start:in_list.stop]
        # If there is no new input then return.
        if len(input_list) == 0:
            return ([output_list], state, [in_list.start])
        
        # Extract window start and the underlying state from the combined state.
        window_start_time, temp_state = state
        state = temp_state
        window_end_time = window_start_time + window_duration
        # last_element = input_list[-1]
        last_element_time = input_list[-1][0]
        # index is a pointer to input_list which starts at 0.
        timestamp_list = [timestamp_and_value[0] for timestamp_and_value in input_list]
        window_start_index = 0
        
        # Main loop    
        while window_end_time <= last_element_time:
            # Compute window_start_index which is the earliest index to an element
            # whose timestamp is greater than or equal to window_start_time
            while (window_start_index < len(input_list) and
                   timestamp_list[window_start_index] < window_start_time):
                window_start_index += 1

            if window_start_index >= len(input_list):
                # No element has timestamp greater than or equal to window_start_time.
                break

            # Determine the window, starting at window_start_index within the input_list.
            window_end_index = window_start_index
            next_window = []
            while (window_end_index < len(input_list) and
                   window_end_time > timestamp_list[window_end_index]):
                window_end_index += 1
            next_window.extend(input_list[window_start_index:window_end_index])

            # Compute output_increment which is the output for
            # next_window.
            if state is None:
                output_increment = func(next_window)
            else:
                output_increment, state = func(next_window, state)

            # Append the output for this window to the output list.
            # The timestamp for this output is window_end_time.
            output_list.append([window_end_time, output_increment])
            # Move the window forward by one step.
            window_start_time += step_time
            window_end_time = window_start_time + window_duration
        # End main loop

        # RETURN OUTPUT LIST, NEW STATE, and NEW STARTING INDEX
        # Compute window_start_index which is the earliest index to an element
        # whose timestamp is greater than or equal to window_start_time
        while (window_start_index < len(timestamp_list) and
               timestamp_list[window_start_index] < window_start_time):
            window_start_index += 1
        state = (window_start_time, state)
        # Return the list of output messages, the new state, and the
        # new start value of the input stream.
        return ([output_list], state, [window_start_index+in_list.start])
    
    # Create agent
    return Agent([in_stream], [out_stream], transition, state, call_streams, name)


def timed_window(
        function, in_stream, window_duration, step_time, state=None, args=[], kwargs={}):
    out_stream = Stream(function.__name__+in_stream.name)
    timed_window_skip_empties_agent(function, in_stream, out_stream, window_duration, step_time,
                    state=state, args=args, kwargs=kwargs)
    return out_stream



###############################################################
#                    TIMED_WINDOW_SKIP_EMPTIES
###############################################################
def timed_window_skip_empties_agent(
        func, in_stream, out_stream,
        window_duration, step_time, window_start_time=0,
        state=None, call_streams=None, name=None,
        args=[], kwargs={}):

    # All windows with start times earlier than window_start_time
    # have already been processed.
    # state is the state of the underlying agent.
    # Augment the state with the start time of the
    # window.
    state = (window_start_time, state)

    def transition(in_lists, state):
        # The map agent has a single input stream. So, the transition
        # operates on a single in_list.
        in_list = in_lists[0]
        # The map agent has a single output stream. So, the transition
        # outputs a single list.
        output_list = []
        # input_list is the list extracted from in_list
        input_list = in_list.list[in_list.start:in_list.stop]
        # If there is no new input then return.
        if len(input_list) == 0:
            return ([output_list], state, [in_list.start])
        
        # Extract window start and the underlying state from the combined state.
        window_start_time, temp_state = state
        state = temp_state
        window_end_time = window_start_time + window_duration
        # last_element = input_list[-1]
        last_element_time = input_list[-1][0]
        # index is a pointer to input_list which starts at 0.
        timestamp_list = [timestamp_and_value[0] for timestamp_and_value in input_list]
        window_start_index = 0
        
        # Main loop    
        while window_end_time <= last_element_time:
            # Compute window_start_index which is the earliest index to an element
            # whose timestamp is greater than or equal to window_start_time
            while (window_start_index < len(input_list) and
                   timestamp_list[window_start_index] < window_start_time):
                window_start_index += 1

            if window_start_index >= len(input_list):
                # No element has timestamp greater than or equal to window_start_time.
                break

            # The timestamp corresponding to window_start_index may be much larger than
            # window_start_time. So, instead of moving the window start time in many steps,
            # move the window start time forward to match the window start index.
            # Then update the window end time to match the new window start time.
            # num_steps is the number of steps that the window is moved forward
            # so that the window includes window_start_index.
            if window_end_time > timestamp_list[window_start_index]:
                num_steps = 0
            else:
                num_steps = \
                  1 + int(timestamp_list[window_start_index] - window_end_time)/ int(step_time)

            # Slide the start and end times forward by the number of steps.
            window_start_time += num_steps * step_time
            window_end_time = window_start_time + window_duration
 
            # If window end time exceeds the timestamp of the last element then
            # this time-window crosses the input list. So, we have to wait for
            # elements with higher timestamps before the end of the window can
            # be determined. In this case break from the main loop.
            if window_end_time > last_element_time:
                break

            # Compute window end index which is the first element whose timestamp
            # is greater than or equal to window_end_time.
            window_end_index = window_start_index
            while timestamp_list[window_end_index] < window_end_time:
                window_end_index += 1

            next_window = input_list[window_start_index : window_end_index]

            # Compute output_increment which is the output for
            # next_window.
            if state is None:
                output_increment = func(next_window)
            else:
                output_increment, state = func(next_window, state)

            # Append the output for this window to the output list.
            # The timestamp for this output is window_end_time.
            output_list.append([window_end_time, output_increment])
            # Move the window forward by one step.
            window_start_time += step_time
            window_end_time = window_start_time + window_duration
        # End main loop

        # RETURN OUTPUT LIST, NEW STATE, and NEW STARTING INDEX
        # Compute window_start_index which is the earliest index to an element
        # whose timestamp is greater than or equal to window_start_time
        while (window_start_index < len(timestamp_list) and
               timestamp_list[window_start_index] < window_start_time):
            window_start_index += 1
        state = (window_start_time, state)
        # Return the list of output messages, the new state, and the
        # new start value of the input stream.
        return ([output_list], state, [window_start_index+in_list.start])
    
    # Create agent
    return Agent([in_stream], [out_stream], transition, state, call_streams, name)


def timed_window_skip_empties(
        function, in_stream, window_duration, step_time, state=None, args=[], kwargs={}):
    out_stream = Stream(function.__name__+in_stream.name)
    timed_window_skip_empties_agent(function, in_stream, out_stream, window_duration, step_time,
                    state=state, args=args, kwargs=kwargs)
    return out_stream


###############################################################
#                          TESTS
###############################################################

def test_timed_zip_agents():
    p = Stream('p')
    #q = Stream('q')
    #r = Stream('r')
    #s = Stream('s')
    u = Stream('u')
    v = Stream('v')
    w = Stream('w')
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
    
    timed_zip_agent(in_streams=[x,y], out_stream=z, name='a_agent')
    q = timed_zip([x, y])

    def concat_operator(timed_list):
        result = ''
        for value in timed_list:
            result = result + value[1]
        return result

    r = timed_window_skip_empties(concat_operator, x, 5, 5)
    s = timed_window_skip_empties(concat_operator, x, 20, 10)

    x.extend([[1, 'a'], [3, 'b'], [10, 'd'], [15, 'e'], [17, 'f']])
    y.extend([[2, 'A'], [3, 'B'], [9, 'D'], [20, 'E']])
    compute_engine.execute_single_step()

    assert recent_values(z) == \
      [[1, 'a', None], [2, None, 'A'], [3, 'b', 'B'], [9, None, 'D'],
       [10, 'd', None], [15, 'e', None], [17, 'f', None]]
    assert recent_values(r) == [[5, 'ab'], [15, 'd']]
    assert recent_values(s) == []
    
    x.extend([[21, 'g'], [23, 'h'], [40, 'i'], [55, 'j'], [97, 'k']])
    y.extend([[21, 'F'], [23, 'G'], [29, 'H'], [55, 'I']])
    compute_engine.execute_single_step()
    assert recent_values(z) == \
      [[1, 'a', None], [2, None, 'A'], [3, 'b', 'B'], [9, None, 'D'],
       [10, 'd', None], [15, 'e', None], [17, 'f', None],
       [20, None, 'E'], [21, 'g', 'F'], [23, 'h', 'G'],
       [29, None, 'H'], [40, 'i', None], [55, 'j', 'I']]
    assert recent_values(r) == [[5, 'ab'], [15, 'd'], [20, 'ef'],
                                [25, 'gh'], [45, 'i'], [60, 'j']]
    assert recent_values(s) == [[20, 'abdef'], [30, 'defgh'], [40, 'gh'],
                                 [50, 'i'], [60, 'ij'], [70, 'j']]


    x.extend([[100, 'l'], [105, 'm']])
    y.extend([[100, 'J'], [104, 'K'], [105, 'L'], [107, 'M']])
    compute_engine.execute_single_step()
    assert recent_values(z) == \
      [[1, 'a', None], [2, None, 'A'], [3, 'b', 'B'], [9, None, 'D'],
       [10, 'd', None], [15, 'e', None], [17, 'f', None],
       [20, None, 'E'], [21, 'g', 'F'], [23, 'h', 'G'],
       [29, None, 'H'], [40, 'i', None], [55, 'j', 'I'],
       [97, 'k', None], [100, 'l', 'J'], [104, None, 'K'], [105, 'm', 'L']]
    assert recent_values(r) == [
        [5, 'ab'], [15, 'd'], [20, 'ef'], [25, 'gh'], [45, 'i'], [60, 'j'],
        [100, 'k'], [105, 'l'],
        ]
    assert recent_values(s) == [
        [20, 'abdef'], [30, 'defgh'], [40, 'gh'], [50, 'i'], [60, 'ij'],
        [70, 'j'], [100, 'k']
        ]

    x.extend([[106, 'n'], [110, 'o']])
    compute_engine.execute_single_step()
    assert recent_values(z) == \
      [[1, 'a', None], [2, None, 'A'], [3, 'b', 'B'], [9, None, 'D'],
       [10, 'd', None], [15, 'e', None], [17, 'f', None],
       [20, None, 'E'], [21, 'g', 'F'], [23, 'h', 'G'],
       [29, None, 'H'], [40, 'i', None], [55, 'j', 'I'],
       [97, 'k', None], [100, 'l', 'J'], [104, None, 'K'], [105, 'm', 'L'],
       [106, 'n', None], [107, None, 'M']]

    assert recent_values(r) == [
        [5, 'ab'], [15, 'd'], [20, 'ef'], [25, 'gh'], [45, 'i'], [60, 'j'],
        [100, 'k'], [105, 'l'], [110, 'mn']
        ]
    
    assert recent_values(s) == [
        [20, 'abdef'], [30, 'defgh'], [40, 'gh'], [50, 'i'], [60, 'ij'],
        [70, 'j'], [100, 'k'], [110, 'klmn']
        ]

#---------------------------------------------------------------------
def test_timed_window_skip_empties():
    x = Stream('x')
    y = Stream('y')
    timed_window_skip_empties_agent(
        func=lambda v: v, in_stream=x, out_stream=y,
        window_duration=2, step_time=2)
    x.extend([[1, 100], [3, 250], [5, 400], [5.5, 100], [7, 300], [11.0, 250]])
    compute_engine.execute_single_step()
    assert recent_values(y) == \
      [[2, [[1, 100]]], [4, [[3, 250]]], [6, [[5, 400], [5.5, 100]]],
      [8, [[7, 300]]]
      ]
    return

#---------------------------------------------------------------------
def test_timed_window():
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
 
    timed_window_agent(
        func=lambda v: v, in_stream=x, out_stream=y,
        window_duration=2, step_time=2, window_start_time=4)

    def sum_values_in_window(window):
        return_value = 0
        for timestamp_element in window:
            timestamp, element = timestamp_element
            return_value += element + timestamp
        return return_value

    timed_window_agent(
        func=sum_values_in_window, in_stream=x, out_stream=z,
        window_duration=2, step_time=2)

    x.extend([[1, 100], [3, 250], [5, 400], [5.5, 100], [12, 300], [15.0, 250]])
    compute_engine.execute_single_step()
    assert recent_values(y) == \
      [[6, [[5, 400], [5.5, 100]]], [8, []],
       [10, []], [12, []], [14, [[12, 300]]]
      ]
    assert recent_values(z) == \
      [[2, 101], [4, 253], [6, 510.5], [8, 0], [10, 0], [12, 0], [14, 312]]

#---------------------------------------------------------------------
def test_timed_window_start_time():
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')

    def starting_agent(start_time):
        pass
 
    timed_window_agent(
        func=lambda v: v, in_stream=x, out_stream=y,
        window_duration=2, step_time=2)


#---------------------------------------------------------------------
    x_array = StreamArray('x_array', dtype=int, dimension=2)
    y_list = Stream('list')
    z_array = StreamArray('z_array', dtype=int, dimension=2)

    timed_window_agent(
        func=sum_values_in_window, in_stream=x_array, out_stream=z_array,
        window_duration=2, step_time=2)

    timed_window_agent(
        func=lambda v: v, in_stream=x_array, out_stream=y_list,
        window_duration=2, step_time=2)
    
    x_array.extend(
        np.array(
            [[1, 100], [2, 200], [3, 250], [5, 400], [6, 100], [7, 200],
             [12, 300], [15, 250]]))
    compute_engine.execute_single_step()
    assert np.array_equal(
        recent_values(z_array),
        np.array([
            [2, 101], [4, 455], [6, 405], [8, 313], [10, 0], [12, 0], [14, 312]]
            ))
    expected_output = [
        [2, [np.array([  1, 100])]], [4, [np.array([  2, 200]), np.array([  3, 250])]],
        [6, [np.array([  5, 400])]], [8, [np.array([  6, 100]), np.array([  7, 200])]],
        [10, []], [12, []], [14, [np.array([ 12, 300])]]
        ]
    for i in range(len(recent_values(y_list))):
        assert recent_values(y_list)[i][0] == expected_output[i][0]
        for j in range(len(recent_values(y_list)[i][1])):
            assert np.array_equal(recent_values(y_list)[i][1][j], expected_output[i][1][j])
        
    return

#---------------------------------------------------------------------
def test_timed_zip_with_array():
    min_value = np.iinfo(np.int).min
    x = StreamArray('x', dtype=int, dimension=2)
    y = StreamArray('y', dtype=int, dimension=2)
    z = StreamArray('z', dtype=int, dimension=3)
    timed_zip_agent(in_streams=[x,y], out_stream=z,
                    no_value_symbol=0,
                    #no_value_symbol=min_value,
                    name='a_agent_array')
    x.extend(np.array([[1, 1], [3, 3], [5, 5]]))
    y.extend(np.array([[1, 10], [2, 20], [4, 40]]))
    compute_engine.execute_single_step()
    assert np.array_equal(
        recent_values(z),
        [[1, 1, 10], [2, 0, 20], [3, 3, 0], [4, 0, 40]])


#---------------------------------------------------------------------
#---------------------------------------------------------------------
def test_timed_agents():
    test_timed_zip_agents()
    test_timed_window()
    test_timed_window_skip_empties()
    test_timed_zip_with_array()
    return

if __name__ == '__main__':
    test_timed_agents()
    
