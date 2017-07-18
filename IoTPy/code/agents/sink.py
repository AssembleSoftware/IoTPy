"""
This module consist of sink functions. A sink is a function that reads a
single stream and that carries out operations on an actuator or other
object such as a list, file, queue, printer or display.

Functions in the module:
   1. element_sink_agent
   2. sink   
   3. stream_to_list
   4. stream_to_file
   5. stream_to_queue

Agents:
   1. element_sink_agent is the agent used by sink.

Sink functions:
   1. sink has input arguments: function, input stream, state, and
      positional and keyword arguments. It applies the function to
      each element of the input stream. Typically, this function has
      the side effect of modifying some object such as an actuator.
   2. stream_to_list has input arguments: function, input stream,
      target list and state. It applies the function to each element
      of the input stream and puts the result of the function call on
      the target list.
   3. stream_to_file: has arguments function, input stream, filename,
      and state. It applies the function to each element of the input
      stream and puts the result of the function call on the file
      called filename.
   4. stream_to_queue: has arguments function, input stream, queue,
      and state. It applies the function to each element of the input
      stream and puts the result of the function call on the queue.

Agents:
   1. element_sink_agent is the agent used by sink.

Uses:
stream_to_list, stream_to_file, stream_to_queue use sink.
sink uses element_sink_agent


"""
import sys
import os
sys.path.append(os.path.abspath("../"))

from agent import Agent, InList
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from compute_engine import compute_engine
from helper_functions.check_agent_parameter_types import *
from helper_functions.recent_values import recent_values
from Buffer import Buffer

#-----------------------------------------------------------------------
# SINK: SINGLE INPUT STREAM, NO OUTPUT
#-----------------------------------------------------------------------
def element_sink_agent(func, in_stream, state=None,
                       call_streams=None, name=None,
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
    #check_num_args_in_func(state, name, func, args, kwargs)

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

def sink(func, in_stream, state=None, *args, **kwargs):
    element_sink_agent(func, in_stream, state, *args, **kwargs)

    
# -----------------------------
def stream_to_list(
        in_stream, target_list, element_function=None, state=None,
        **kwargs):
    def simple_append(element, target_list):
        target_list.append(element)
    def function_stateless_append(
            element, target_list, element_function, **kw):
        target_list.append(element_function(element, **kw))
    def function_stateful_append(
            element, state, target_list, element_function, **kw):
        next_output, next_state = element_function(
            element, state, **kw) 
        target_list.append(next_output)
        return next_state

    if element_function is None:
        sink(simple_append, in_stream, target_list=target_list)
    elif state is None:
        ext_kw = kwargs
        ext_kw['target_list'] = target_list
        ext_kw['element_function'] = element_function
        sink(function_stateless_append, in_stream, **ext_kw)  
    else:
        # function and state are both non None
        ext_kw = kwargs
        ext_kw['target_list'] = target_list
        ext_kw['element_function'] = element_function
        sink(function_stateful_append, in_stream, state, **ext_kw) 

# -----------------------------
def stream_to_file(
        in_stream, filename, element_function=None, state=None,
        **kwargs):
    def simple_append(element, filename):
        with open(filename, 'a') as the_file:
            the_file.write(str(element) + '\n')
    def function_stateless_append(
            element, filename, element_function, **kw):
        with open(filename, 'a') as the_file:
            the_file.write(str(element_function(element, **kw)) + '\n')
    def function_stateful_append(
            element, state, filename, element_function, **kw):
        next_output, next_state = element_function(element, state, **kw)
        with open(filename, 'a') as the_file:
            the_file.write(str(next_output) + '\n')
        return next_state

    if element_function is None:
        sink(simple_append, in_stream, filename=filename)
    elif state is None:
        ext_kw = kwargs
        ext_kw['filename'] = filename
        ext_kw['element_function'] = element_function
        sink(function_stateless_append, in_stream, **ext_kw) 
    else:
        # function and state are both non None
        ext_kw = kwargs
        ext_kw['filename'] = filename
        ext_kw['element_function'] = element_function
        sink(function_stateful_append, in_stream, state, **ext_kw)

#----------------------------------------------------
def stream_to_queue(
        in_stream, queue, element_function=None, state=None,
        **kwargs): 
    def simple_append(element, queue):
        queue.put(element)
    def function_stateless_append(
            element, queue, element_function, **kw):
        queue.put(element_function(element, **kw))
    def function_stateful_append(
            element, state, queue, element_function, **kw):
        next_output, next_state = element_function(element, state, **kw)
        queue.put(next_output)
        return next_state

    if element_function is None:
        sink(simple_append, in_stream, queue=queue)
    elif state is None:
        ext_kw = kwargs
        ext_kw['queue'] = queue
        ext_kw['element_function'] = element_function
        sink(function_stateless_append, in_stream, **ext_kw) 
    else:
        # function and state are both non None
        ext_kw = kwargs
        ext_kw['queue'] = queue
        ext_kw['element_function'] = element_function
        sink(function_stateful_append, in_stream, state, **ext_kw)

def stream_to_buffer(in_stream, target_buffer):
    def append_target_buffer(element):
        target_buffer.append(element)
    sink(append_target_buffer, in_stream)
    
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#                                     TESTS
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------

def test_sink_agents():
    ## ----------------------------------------------
    ## # Examples from AssembleSoftware website: KEEP!!
    ## ----------------------------------------------
    ## def print_index(v, state, delimiter):
    ##     print str(state) + delimiter + str(v)
    ##     return state+1 # next state
    ## s = Stream()
    ## sink(print_index, s, 0, delimiter=':')
    ## s.extend(range(100,105))

    ## s = Stream()
    ## def print_index(v, state, delimiter):
    ##     print str(state) + delimiter + str(v)
    ##     return state+1 # next state
    ## sink(print_index, s, 0, delimiter=':')
    ## s.extend(range(100,105))
    # Set up parameters for call to stream_to_list
    ## ----------------------------------------------
    ## # Finished examples from AssembleSoftware website
    ## ----------------------------------------------

    #-----------------------------------------------
    # Set up parameters for call to sink
    print_list = []
    print_list_for_array = []
    def print_index(v, state, print_list):
      print_list.append(str(state) + ':' + str(v))
      return state+1 # next state
    s = Stream('s')
    s_array = StreamArray('s_array', dtype=int)

    #-----------------------------------------------
    # Call sink with initial state of 0
    sink(func=print_index, in_stream=s, state=0,
         print_list=print_list)
    sink(func=print_index, in_stream=s_array, state=0,
         print_list=print_list_for_array)
    
    s.extend(range(100,103))
    s_array.extend(np.arange(100, 103))
    compute_engine.execute_single_step()
    assert print_list == ['0:100', '1:101', '2:102']
    assert print_list_for_array == print_list
    s.extend(range(200, 203))
    compute_engine.execute_single_step()
    assert print_list == ['0:100', '1:101', '2:102',
                          '3:200', '4:201', '5:202']

    #-----------------------------------------------
    input_stream = Stream('input stream')
    input_stream_array = StreamArray('input stream array', dtype=int)
    output_list = []
    output_list_array = []

    # Call stream_to_list with no function
    stream_to_list(input_stream, output_list)
    stream_to_list(input_stream_array, output_list_array)
    # A test
    a_test_list = range(100, 105)
    a_test_array = np.arange(100, 105)
    input_stream.extend(a_test_list)
    input_stream_array.extend(a_test_array)
    compute_engine.execute_single_step()
    assert output_list == a_test_list
    assert output_list_array == a_test_list

    #-----------------------------------------------
    # test stream to list with a function
    def h(v, multiplier, addend): return v*multiplier+addend
    ss = Stream('ss')
    ss_array = StreamArray('ss_array', dtype=int)
    l = []
    l_array = []
    stream_to_list(ss, l, h, multiplier=2, addend=100)
    stream_to_list(in_stream=ss_array, target_list=l_array,
                   element_function=h, multiplier=2, addend=100 )
    test_list = [3, 23, 14]
    ss.extend(test_list)
    ss_array.extend(np.array(test_list))
    compute_engine.execute_single_step()
    assert l == [v*2+100 for v in test_list]
    assert l_array == l


    #-----------------------------------------------
    # test stream to list with a function and state
    def h(v, state, multiplier, addend):
        return v*multiplier+addend+state, v+state

    ss = Stream('ss')
    ss_array = StreamArray('ss_array', dtype=int)
    l = []
    l_array = []
    stream_to_list(ss, l, h, 0, multiplier=2, addend=100)
    stream_to_list(in_stream=ss_array, target_list=l_array, 
                   element_function=h, state=0,
                   multiplier=2, addend=100 )
    test_list = [3, 23, 14]
    ss.extend(test_list)
    ss_array.extend(np.array(test_list))
    compute_engine.execute_single_step()
    assert l == [106, 149, 154]
    assert l_array == l

    ss = Stream('ss')
    ss_array = StreamArray('ss_array', dtype=int)
    l = []
    l_array = []
    stream_to_list(ss, l, h, 0, multiplier=2, addend=100)
    stream_to_list(in_stream=ss_array, target_list=l_array, 
                   element_function=h, state=0,
                   multiplier=2, addend=100 )
    test_list = range(5)
    ss.extend(test_list)
    ss_array.extend(np.array(test_list))
    compute_engine.execute_single_step()
    assert l == [100, 102, 105, 109, 114]
    assert l_array == l

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
    sink(func=p, in_stream=in_stream_sink, lst=b_list)
    test_list = [1, 13, 29]
    in_stream_sink.extend(test_list)
    compute_engine.execute_single_step()
    assert a_list == test_list
    assert b_list == test_list

    # ------------------------------------
    # Test sink with state
    # func operates on a single element of the single input stream and state.
    # func does not return any value.
    
    def p_s(element, state, lst, stream_name):
        lst.append([stream_name, element])
        return state+1
    
    in_stream_sink_with_state = Stream('s')
    c_list = []
    sink_with_state_agent = element_sink_agent(
        func=p_s, in_stream=in_stream_sink_with_state,
        state=0, name='sink_with_state_agent',
        lst = c_list,
        stream_name ='s')

    #------------------------------------------------------------------------------
    # Test sink as a function with state
    d_list = []
    sink(p_s, in_stream_sink_with_state, state=0,
         lst=d_list, stream_name='s')
    in_stream_sink_with_state.extend(range(2))
    compute_engine.execute_single_step()
    assert c_list == [['s', 0], ['s', 1]]
    assert d_list == c_list

    # ------------------------------------
    # Test sink with side effect
    # func operates on a single element of the single input stream and state.
    # func does not return any value.
    
    def sink_with_side_effect_func(element, side_effect_list, f):
        side_effect_list.append(f(element))
        return None

    side_effect_list_0 = []
    side_effect_list_1 = []
    side_effect_list_2 = []

    def ff(element):
        return element*2

    def fff(element):
        return element+10
    stm = Stream('stm')

    sink_with_side_effect_agent_0 = element_sink_agent(
        func=sink_with_side_effect_func,
        in_stream=stm,
        name='sink_with_side_effect_agent_0',
        side_effect_list=side_effect_list_0, f=ff)

    sink_with_side_effect_agent_1 = element_sink_agent(
        func=sink_with_side_effect_func,
        in_stream=stm,
        name='sink_with_side_effect_agent_1',
        side_effect_list=side_effect_list_1, f=fff)
    
    def f_stateful(element, state):
        return element+state, element+state
    def f_stateful_2(element, state):
        return element*state, element+state
    target_stream_to_list_simple= []
    stream_to_list(stm,
                   target_stream_to_list_simple)
    stream_to_list(
        in_stream=stm,
        target_list=side_effect_list_2,
        element_function=lambda v: 2*v)
    target_stream_to_list_stateful= []
    stream_to_list(
        in_stream=stm,
        target_list=target_stream_to_list_stateful,
        element_function=f_stateful, state=0)
    target_stream_to_list_stateful_2= []
    stream_to_list(
        in_stream=stm,
        target_list=target_stream_to_list_stateful_2,
        element_function=f_stateful_2, state=0)
    
    stream_to_file(stm, 'test1.txt') 
    stream_to_file(stm, 'test2.txt', lambda v: 2*v)
    stream_to_file(stm, 'test3.txt', f_stateful, state=0)

    import Queue
    queue_1 = Queue.Queue()
    queue_2 = Queue.Queue()
    queue_3 = Queue.Queue()
    stream_to_queue(stm, queue_1)
    stream_to_queue(stm, queue_2, lambda v: 2*v)
    stream_to_queue(stm, queue_3, f_stateful, 0)

    stm.extend(range(5))
    compute_engine.execute_single_step()
    assert target_stream_to_list_stateful == [0, 1, 3, 6, 10]
    assert target_stream_to_list_stateful_2 == [0, 0, 2, 9, 24]
    assert side_effect_list_0 == [0, 2, 4, 6, 8]
    assert side_effect_list_1 == [10, 11, 12, 13, 14]
    assert side_effect_list_0 == side_effect_list_2
    assert target_stream_to_list_simple == range(5)

    with open('test1.txt') as the_file:
        file_contents_integers = [int(v) for v in (the_file.readlines())]
    assert file_contents_integers == recent_values(stm)

    with open('test2.txt') as the_file:
        file_contents_integers = [int(v) for v in (the_file.readlines())]
    assert file_contents_integers == [2*v for v in recent_values(stm)]

    with open('test3.txt') as the_file:
        file_contents_integers = [int(v) for v in (the_file.readlines())]
    assert file_contents_integers == [0, 1, 3, 6, 10]
    os.remove('test1.txt')
    os.remove('test2.txt')
    os.remove('test3.txt')

    def h(v, multiplier, addend): return v*multiplier+addend
    ss = Stream()
    stream_to_file(ss, 'test4.txt', h, multiplier=2, addend=100)
    test_list = [3, 23, 14]
    ss.extend(test_list)
    compute_engine.execute_single_step()
    with open('test4.txt') as the_file:
        file_contents_integers = [
            int(v) for v in (the_file.readlines())]
    assert file_contents_integers == [v*2+100 for v in test_list]
    os.remove('test4.txt')

    def h(v, state, multiplier, addend):
        return v*multiplier+addend+state, v+state
    ss = Stream()
    stream_to_file(ss, 'test5.txt', h, 0, multiplier=2, addend=100)
    test_list = [3, 23, 14]
    ss.extend(test_list)
    compute_engine.execute_single_step()
    with open('test5.txt') as the_file:
        file_contents_integers = [
            int(v) for v in (the_file.readlines())]
    compute_engine.execute_single_step()
    assert file_contents_integers == [106, 149, 154]
    os.remove('test5.txt')

    # ------------------------------------
    # TEST stream_to_queue
    
    queue_contents=[]
    while not queue_1.empty():
        queue_contents.append(queue_1.get())
    assert queue_contents == range(5)

    queue_contents=[]
    while not queue_2.empty():
        queue_contents.append(queue_2.get())
    assert queue_contents == [0, 2, 4, 6, 8]

    
    queue_contents=[]
    while not queue_3.empty():
        queue_contents.append(queue_3.get())
    compute_engine.execute_single_step()
    assert queue_contents == [0, 1, 3, 6, 10]
    
    # Testing stream_to_queue
    def h(v, state, multiplier, addend):
        return v*multiplier+addend+state, v+state
    ss = Stream()
    queue_4 = Queue.Queue()
    stream_to_queue(ss, queue_4, h, 0, multiplier=2, addend=100)
    test_list = [3, 23, 14]
    ss.extend(test_list)
    compute_engine.execute_single_step()
    queue_contents = []
    while not queue_4.empty():
        queue_contents.append(queue_4.get())
    assert queue_contents == [106, 149, 154]

    # Test with state and keyword arguments
    def h(v, state, multiplier, addend):
        return v*multiplier+addend+state, v+state
    ss = Stream()
    stream_to_queue(ss, queue_4, h, 0, multiplier=2, addend=100)
    test_list = [3, 23, 14]
    ss.extend(test_list)
    queue_contents = []
    compute_engine.execute_single_step()
    while not queue_4.empty():
        queue_contents.append(queue_4.get())
    assert queue_contents == [106, 149, 154]

    # Another test with state and keyword arguments
    ss = Stream()
    queue_5 = Queue.Queue()
    stream_to_queue(ss, queue_5, h, 0, multiplier=2, addend=100)
    test_list = range(5)
    ss.extend(test_list)
    compute_engine.execute_single_step()
    queue_contents = []
    while not queue_5.empty():
        queue_contents.append(queue_5.get())
    assert queue_contents == [100, 102, 105, 109, 114]

    # Test stream_to_buffer
    s = Stream()
    buf = Buffer(max_size=10)
    stream_to_buffer(s, buf)
    test_list = range(5)
    s.extend(test_list)
    compute_engine.execute_single_step()
    assert buf.get_all() == test_list
    next_test = range(5, 10, 1)
    s.extend(next_test)
    compute_engine.execute_single_step()
    assert buf.read_all() == next_test
    assert buf.get_all() == next_test

    return
    
if __name__ == '__main__':
    test_sink_agents()
    
    
    
    
    

