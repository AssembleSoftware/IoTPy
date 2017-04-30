import sys
import os
scriptpath = "../"

from ..agent import Agent, InList
from ..stream import Stream, StreamArray
from ..stream import _no_value, _multivalue, _close
from ..helper_functions.check_agent_parameter_types import *
import types
import inspect

def timed_merge_agent(in_streams, out_stream, call_streams=None, name=None):
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
        check_in_lists_type(name, in_lists, num_in_streams)
        input_lists = [in_list.list[in_list.start:in_list.stop]
                       for in_list in in_lists]
        pointers = [0 for i in indices]
        stops = [len(input_lists[i]) for i in indices]
        output_list = []
        while all(pointers[i] < stops[i] for i in indices):
            slice = [input_lists[i][pointers[i]] for i in indices]
            earliest_time = min(slice[i][0] for i in indices)
            next_output_value = [slice[i][1:] if slice[i][0] == earliest_time
                           else []  for i in indices]
            pointers = [pointers[i]+1 if slice[i][0] == earliest_time
                        else pointers[i]  for i in indices]
            next_output = [earliest_time]
            next_output.extend(next_output_value)
            output_list.append(next_output)
        return [output_list], state, [in_lists[i].start+pointers[i] for i in indices]
    # Finished transition

    # Create agent
    state = None
    return Agent(in_streams, [out_stream], transition, state, call_streams, name)

def test_timed_merge_agents():
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
    timed_merge_agent(in_streams=[x,y], out_stream=z, name='a')

    x.extend([[1, 'a'], [3, 'b'], [10, 'd'], [15, 'e'], [17, 'f']])
    y.extend([[2, 'A'], [3, 'B'], [9, 'D'], [20, 'E']])
    assert z.recent[:z.stop] == \
      [[1, ['a'], []], [2, [], ['A']], [3, ['b'], ['B']], [9, [], ['D']],
       [10, ['d'], []], [15, ['e'], []], [17, ['f'], []]]

    x.extend([[21, 'g'], [23, 'h'], [40, 'i'], [55, 'j'], [97, 'k']])
    y.extend([[21, 'F'], [23, 'G'], [29, 'H'], [55, 'I']])
    assert z.recent[:z.stop] == \
      [[1, ['a'], []], [2, [], ['A']], [3, ['b'], ['B']], [9, [], ['D']],
       [10, ['d'], []], [15, ['e'], []], [17, ['f'], []],
       [20, [], ['E']], [21, ['g'], ['F']], [23, ['h'], ['G']],
       [29, [], ['H']], [40, ['i'], []], [55, ['j'], ['I']]]

    x.extend([[100, 'l'], [105, 'm']])
    y.extend([[100, 'J'], [104, 'K'], [105, 'L'], [107, 'M']])
    assert z.recent[:z.stop] == \
      [[1, ['a'], []], [2, [], ['A']], [3, ['b'], ['B']], [9, [], ['D']],
       [10, ['d'], []], [15, ['e'], []], [17, ['f'], []],
       [20, [], ['E']], [21, ['g'], ['F']], [23, ['h'], ['G']],
       [29, [], ['H']], [40, ['i'], []], [55, ['j'], ['I']],
       [97, ['k'], []], [100, ['l'], ['J']], [104, [], ['K']], [105, ['m'], ['L']]]

if __name__ == '__main__':
    test_timed_merge_agents()
