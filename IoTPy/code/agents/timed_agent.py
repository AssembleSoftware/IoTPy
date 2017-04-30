""" This module has timed_zip and timed_window which are described
in the manual documentation.

"""
import sys
import os
# scriptpath = "../"
# sys.path.append(os.path.abspath(scriptpath))

from ..agent import Agent, InList
from ..stream import Stream, StreamArray
from ..stream import _no_value, _multivalue, _close
from ..helper_functions.check_agent_parameter_types import *

####################################################
#                     TIMED ZIP
####################################################

def timed_zip_agent(in_streams, out_stream, call_streams=None, name=None):
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
            output_list.append((window_end_time,output_increment))
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


def timed_window(function, in_stream, window_duration, step_time, state=None, args=[], kwargs={}):
    out_stream = Stream(function.__name__+in_stream.name)
    timed_window_agent(function, in_stream, out_stream, window_duration, step_time,
                    state=state, args=args, kwargs=kwargs)
    return out_stream


###############################################################
#                          TESTS
###############################################################

def test_timed_zip_agents():
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
    # timed_zip_agent(in_streams=[x,y], out_stream=z, name='a')
    z = timed_zip([x, y])

    def concat_operator(timed_list):
        result = ''
        for timestamp_value in timed_list:
            result = result + timestamp_value[1]
        return result

    r = timed_window(concat_operator, x, 5, 5)
    s = timed_window(concat_operator, x, 20, 10)

    x.extend([[1, 'a'], [3, 'b'], [10, 'd'], [15, 'e'], [17, 'f']])
    y.extend([[2, 'A'], [3, 'B'], [9, 'D'], [20, 'E']])
    assert z.recent[:z.stop] == \
      [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
       [10, ['d', None]], [15, ['e', None]], [17, ['f', None]]]
    assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd')]
    assert s.recent[:s.stop] == []
    
    x.extend([[21, 'g'], [23, 'h'], [40, 'i'], [55, 'j'], [97, 'k']])
    y.extend([[21, 'F'], [23, 'G'], [29, 'H'], [55, 'I']])
    assert z.recent[:z.stop] == \
      [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
       [10, ['d', None]], [15, ['e', None]], [17, ['f', None]],
       [20, [None, 'E']], [21, ['g', 'F']], [23, ['h', 'G']],
       [29, [None, 'H']], [40, ['i', None]], [55, ['j', 'I']]]
    assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd'), (20, 'ef'),
                                 (25, 'gh'), (45, 'i'), (60, 'j')]
    assert s.recent[:s.stop] == [(20, 'abdef'), (30, 'defgh'), (40, 'gh'),
                                 (50, 'i'), (60, 'ij'), (70, 'j')]

    x.extend([[100, 'l'], [105, 'm']])
    y.extend([[100, 'J'], [104, 'K'], [105, 'L'], [107, 'M']])
    assert z.recent[:z.stop] == \
      [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
       [10, ['d', None]], [15, ['e', None]], [17, ['f', None]],
       [20, [None, 'E']], [21, ['g', 'F']], [23, ['h', 'G']],
       [29, [None, 'H']], [40, ['i', None]], [55, ['j', 'I']],
       [97, ['k', None]], [100, ['l', 'J']], [104, [None, 'K']], [105, ['m', 'L']]]
    assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd'), (20, 'ef'),
                                 (25, 'gh'), (45, 'i'), (60, 'j'),
                                 (100, 'k'), (105, 'l')]
    assert s.recent[:s.stop] == [(20, 'abdef'), (30, 'defgh'), (40, 'gh'),
                                 (50, 'i'), (60, 'ij'), (70, 'j'), (100, 'k')
                                 ]

    x.extend([[106, 'n'], [110, 'o']])
    assert z.recent[:z.stop] == \
      [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
       [10, ['d', None]], [15, ['e', None]], [17, ['f', None]],
       [20, [None, 'E']], [21, ['g', 'F']], [23, ['h', 'G']],
       [29, [None, 'H']], [40, ['i', None]], [55, ['j', 'I']],
       [97, ['k', None]], [100, ['l', 'J']], [104, [None, 'K']], [105, ['m', 'L']],
       [106, ['n', None]], [107, [None, 'M']]
     ]
    assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd'), (20, 'ef'),
                                 (25, 'gh'), (45, 'i'), (60, 'j'),
                                 (100, 'k'), (105, 'l'), (110, 'mn')]
    assert s.recent[:s.stop] == [(20, 'abdef'), (30, 'defgh'), (40, 'gh'),
                                 (50, 'i'), (60, 'ij'), (70, 'j'), (100, 'k'),
                                 (110, 'klmn')]
    return


if __name__ == '__main__':
    test_timed_zip_agents()
