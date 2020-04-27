"""
===================
Map Window Examples
===================
agent maps the function func from its single input stream to its
single output stream.
    
This example demonstrates how to use :function:`filter_element` in 
agent_types/op.py on streams.
"""
import sys
sys.path.append("../../IoTPy/")
sys.path.append("../../IoTPy/core")
sys.path.append("../../IoTPy/agent_types")
sys.path.append("../../IoTPy/helper_functions")

# stream is in IoTPy/IoTPy/core
from stream import Stream, run
# op, check_agent_parameter_types are in IoTPy/IoTPy/agent_types
from op import map_window
from check_agent_parameter_types import *
# recent_values is in IoTPy/IoTPy/helper_functions
from recent_values import recent_values

def map_window_examples_simple():

    #----------------------------------------------------------------    
    # Example with no state and no additional parameters
    #----------------------------------------------------------------
    # Create streams
    x = Stream('x')
    s = Stream()

    # Create agents
    map_window(func=sum, in_stream=x, out_stream=s,
               window_size=3, step_size=10)

    # Explanation of agent
    # The function sum() returns the sum of the window.
    # out_stream[j] = \
    # func(in_stream[j*step_size : j*step_size + window_size])
    # for all j.
    # So if window_size is 3 and step_size is 10:
    #       s[j] = x[10*j] + x[10*j+1] +  x[10*j+2], for all j
    # For window_size of 3 and step_size of 10, the output
    # stream will contain:
    # [0 + 1 + 2, 10 + 11 + 12, 20 + 21 + 22, 30 + 31 + 32]

    # Put data into input streams and run.
    DATA = list(range(40))
    x.extend(DATA)
    run()

    # Inspect output
    assert recent_values(s) == [3, 33, 63, 93]

def map_window_example_simple_with_state():
    #----------------------------------------------------------------    
    # Example with state and no additional parameters
    #----------------------------------------------------------------
    # Declare functions
    def comp(this_list, state):
       # this_list is a list
       # state is a number
       # return next element of output stream, next state
       next_state = sum(this_list)
       next_output_element = sum(this_list) > state
       return next_output_element, next_state

    # Create streams
    x = Stream('x')
    c = Stream('c')

    # Create agents
    map_window(func=comp, in_stream=x, out_stream=c, 
               state=0, window_size=2, step_size=4)

    # Explanation of agent
    # The initial state is 0
    # The initial value of this_list is x[:window_size]
    # The zeroth element of the output stream is:
    # func(x[:window_size], state)
    # c[0] = sum(x[:window_size]) > 0 because 0 is the initial state
    # c[j] = sum(x[step_size*j:step_size*j+window_size]) >
    #        sum(x[step_size*(j-1):step_size*(j-1)+window_size])

    # Put data into input streams and run.
    DATA = [1, 10, 0, -1, 2, 3, -10, -20, 11, 1]
    # With window_size=2, step_size=4, and this DATA the output is:
    # [(1 + 10 > 0), (2 + 3 > 1 + 10), (11 + 1 > 2 + 3)] which is
    # [True, False, True]
    x.extend(DATA)
    run()

    # Inspect output
    assert recent_values(c) == [True, False, True]

def map_window_example_simple_with_parameter():
    #----------------------------------------------------------------    
    # Example with no state and additional parameters
    #----------------------------------------------------------------
    # The additional parameter is threshold
    # Since this agent has no state, this function returns a single
    # value which is appended to the output stream.
    # Declare functions
    def thresh(in_stream_window, threshold):
       return sum(in_stream_window) > threshold

    # Create streams
    x = Stream('x')
    t = Stream('t')

    # Create agents
    map_window(func=thresh, in_stream=x, out_stream=t, window_size=3,
               step_size=2, threshold=0)

    # Explanation of agent
    # For all j, : t[j] is True if and only if
    # sum(x[window_size*j : step_size*j+window_size]) > threshold.
    # With window_size of 3 and step_size of 2, and threshold of 5
    # the output is
    # [sum(x[0:3]) > 0, sum(x[2:5] > 0, sum(x[4:7] > 0, ...]
    #
    # Note: You can use any names as arguments in the
    # definition of func, as in:
    # def thresh(v, s): return sum(v) > w

    # Put data into input streams and run.
    DATA = [1, 1, 0, -1, 0, 3, -1, -20, 11, 1]
    # With window_size=3, step_size=2, and this DATA the output is:
    # [(1 + 1 + 0 > 0), (0 + (-1) + 0 > 0), (0 + 3 + (-1) > 0), ..] which is
    # [True, False, True]
    x.extend(DATA)
    run()

    # Inspect output
    assert recent_values(t) == [True, False, True, False]

def map_window_example_simple_with_state_and_parameter():
    #----------------------------------------------------------------    
    # Example with state and additional parameters
    #----------------------------------------------------------------
    # Declare functions
    # This function returns an element of the output stream and then
    # next state.
    # The parameter is multiplicand.
    def maxes(in_stream_window, state, multiplicand):
       next_output_element = sum(in_stream_window) > multiplicand * state
       next_state = max(state, sum(in_stream_window))
       return (next_output_element, next_state)

    # Create streams
    x = Stream('x')
    m = Stream('m')

    # Create agents
    map_window(func=maxes, in_stream=x, out_stream=m, state=0,
               window_size=2, step_size=3, multiplicand=1.5)

    # Explanation of agent
    # in_stream_window on step j is:
    #  x[step_size*j : step_size*j + window_size]
    # For j > 0: state[j] = \
    #   max(state[j-1], sum(x[step_size*j : step_size*j + window_size]))
    # m[j] = sum(x[step_size*j : step_size*j + window_size]) > \
    #     multiplicand * state[j]
    # With a window_size of 2 and step_size of 3 and multiplicand of 1.5
    # state[j] is max(state[j-1], x[3*j, 3*j+1])
    # m[j] is (x[3*j, 3*j+1]) > 1.5*state[j]

    # Put data into input streams and run.
    DATA = [1, 1, 0, -1, 0, 3, 1, 5, 11, 1]
    # With window_size=3, step_size=2, and this DATA the output steps are:
    # Initially state = 0, because of the specification in max_window
    # m[0] is (DATA[0]+DATA[1]) > 1.5*0, which is (1 + 1) > 0 or True.
    # state[1] is max(0, DATA[0]+DATA[1]) which is 2.
    # m[1] is (DATA[3]+DATA[4]) > 1.5*2 which is (-1 + 0) > 2 or False.
    # state[2] is max(2, DATA[3]+DATA[4]) which is 2.
    # m[2] is (DATA[6]+DATA[7]) > 1.5*2 which is (1 + 5) > 2 or True.
    # state[3] is max(2, DATA[6]+DATA[7]) which is 6.
    # So the output stream is:
    # [True, False, True, ....]
    x.extend(DATA)
    run()

    # Inspect output
    assert recent_values(m) == [True, False, True]


if __name__ == '__main__':
    map_window_examples_simple()
    map_window_example_simple_with_state()
    map_window_example_simple_with_parameter()
    map_window_example_simple_with_state_and_parameter()
