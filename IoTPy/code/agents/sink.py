import sys
import os
# sys.path.append(os.path.abspath("../"))

from ..agent import Agent, InList
from ..stream import Stream, StreamArray
from ..stream import _no_value, _multivalue, _close
from ..helper_functions.check_agent_parameter_types import *
from ..helper_functions.recent_values import recent_values

#-----------------------------------------------------------------------
# SINK: SINGLE INPUT STREAM, NO OUTPUT
#-----------------------------------------------------------------------
def element_sink_agent(func, in_stream, state=None, call_streams=None, name=None,
                       *args, **kwargs):
    """
    This agent applies func to its single input stream. It has no output streams.

    Parameters
    ----------
        func: function
           function from an element of the in_stream and args and kwargs
           to None (no return).
        in_stream: Stream
           The single input stream of this agent
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
    check_sink_agent_arguments(func, in_stream, call_streams, name)
    check_num_args_in_func(state, name, func, args, kwargs)

    # The transition function for this agent.
    def transition(in_lists, state):
        num_in_streams = 1
        check_in_lists_type(name, in_lists, num_in_streams)
        in_list = in_lists[0]
        input_list = in_list.list[in_list.start:in_list.stop]
        # If the new input data is empty then return an empty list for
        # the single output stream, and leave the state and the starting
        # point for the single input stream unchanged.
        if not input_list or len(input_list) == 0:
            return ([], state, [in_list.start])

        if state is None:
            for element in input_list:
                func(element, *args, **kwargs)
        else:
            for element in input_list:
                state = func(element, state, *args, **kwargs)

        return ([], state, [in_list.start+len(input_list)])
    # Finished transition

    # Create agent
    return Agent([in_stream], [], transition, state, call_streams, name)

def sink(function, in_stream, state=None, *args, **kwargs):
    element_sink_agent(function, in_stream, state, *args, **kwargs)


#-----------------------------
# MULTIPROCESSING TEST. SINK TO QUEUE
import multiprocessing
def element_stream_to_queue_agent(stream, queue, name=None, descriptor=None):
    # CHECK TYPES
    assert isinstance(stream, Stream) or isinstance(stream, StreamArray),\
      'Error in element_stream_to_queue_agent. stream is of type {0}. It should be a Stream or StreamArray'.\
    format(type(stream))
    assert isinstance(queue, multiprocessing.queues.Queue),\
      'Error in element_stream_to_queue_agent. queue is of type {0}. It should be Queue.Queue'.\
    format(type(queue))
    
    def f(v, queue):
        if descriptor is None:
            queue.put(v)
        else:
            queue.put((descriptor, v))
    element_sink_agent(func=f, in_stream=stream, state=None,
                       call_streams=None, name=name,
                       queue=queue)

#------------------------------------------------------------------------------------------------
#                                     TESTS
#------------------------------------------------------------------------------------------------
def test_element_agents():
    # Test sink
    # func operates on a single element of the single input stream and does
    # not return any value.
    def p(v, lst): lst.append(v)
    in_stream_sink = Stream('in_stream_sink')
    a_list = []
    b_list = []
    sink_agent = element_sink_agent(
        func=p, in_stream=in_stream_sink, name='sink_agent',
        lst=a_list) 
    sink(function=p, in_stream=in_stream_sink, lst=b_list)
    test_list = [1, 13, 29]
    in_stream_sink.extend(test_list)
    assert a_list == test_list
    assert b_list == test_list

    # ------------------------------------
    # Test sink with state
    # func operates on a single element of the single input stream and state.
    # func does not return any value.
    
    def p_s(element, state, lst, stream_name):
        lst.append([stream_name, state, element])
        return state+1
    
    in_stream_sink_with_state = Stream('in_stream_sink_with_state')
    c_list = []
    sink_with_state_agent = element_sink_agent(
        func=p_s, in_stream=in_stream_sink_with_state,
        state=0, name='sink_with_state_agent',
        lst = c_list,
        stream_name ='in_stream_sink_with_state')
    #------------------------------------------------------------------------------
    # Test sink as a function with state
    sink(p_s, in_stream_sink_with_state, state=0,
         lst=c_list, stream_name='in_stream_sink_with_state')
    in_stream_sink_with_state.extend(range(2))

    # ------------------------------------
    # Test sink with side effect
    # func operates on a single element of the single input stream and state.
    # func does not return any value.
    
    def sink_with_side_effect_func(element, side_effect_list, f):
        side_effect_list.append(f(element))
        return None

    side_effect_list_0 = []
    side_effect_list_1 = []

    def ff(element):
        return element*2

    def fff(element):
        return element+10
    in_stream_sink_with_side_effect = Stream('in_stream_sink_with_side_effect')

    sink_with_side_effect_agent_0 = element_sink_agent(
        func=sink_with_side_effect_func,
        in_stream=in_stream_sink_with_side_effect,
        name='sink_with_side_effect_agent_0',
        side_effect_list=side_effect_list_0, f=ff)

    sink_with_side_effect_agent_1 = element_sink_agent(
        func=sink_with_side_effect_func,
        in_stream=in_stream_sink_with_side_effect,
        name='sink_with_side_effect_agent_1',
        side_effect_list=side_effect_list_1, f=fff)

    in_stream_sink_with_side_effect.extend(range(5))

    assert side_effect_list_0 == [0, 2, 4, 6, 8]
    assert side_effect_list_1 == [10, 11, 12, 13, 14]

    # ------------------------------------
    # TEST element_stream_to_queue_agent
    y = Stream('y')
    y_extend_list = [1, 10, 15]
    y.extend(y_extend_list)
    queue = multiprocessing.Queue()
    element_stream_to_queue_agent(stream=y, queue=queue, name='stream_to_queue',
                                  descriptor=y.name)
    queue_output = []
    for i in range(y.stop):
        queue_output.append(queue.get())
    assert queue_output == [('y', v) for v in recent_values(y)]

    return
    
if __name__ == '__main__':
    test_element_agents()
    
    
    
    
    

