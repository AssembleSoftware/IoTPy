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
import os
sys.path.append(os.path.abspath("../../IoTPy/"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))

from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from op import map_window

# In the following examples, x is a stream that is an input stream of
# the agents. 
x = Stream('x')

#----------------------------------------------------------------    
# Example with no state and no additional parameters
#----------------------------------------------------------------
s = Stream()
map_window(func=sum, in_stream=x, out_stream=s, 
 window_size=2, step_size=10)
# out_stream[j] = \
# func(in_stream[j*step_size : j*step_size + window_size])
# for all j.
# So:
#       s[j] = x[10*j] + x[10*j+1], for all j

#----------------------------------------------------------------    
# Example with state and no additional parameters
#----------------------------------------------------------------
this_list = range(10)
def comp(this_list, state):
   # Current state is sum_of_previous_list
   # Next state will be sum(this_list)
   # return next element of output stream, next state
   next_state = sum(this_list)
   next_output_element = sum(this_list) > state
   return next_output_element, next_state
c = Stream()
map_window(func=comp, in_stream=x, out_stream=c, 
           state=0, window_size=10, step_size=20)
# The initial state is 0
# The initial value of this_list is x[:window_size]
# The zeroth element of the output stream is:
# func(x[:window_size], state)
# c[0] = sum(x[:10]) > 0 because 0 is the initial state
# c[j] = sum(x[20*j:20*j+10]) > sum(x[20*(j-1):20*(j-1)+10])

#----------------------------------------------------------------    
# Example with no state and additional parameters
#----------------------------------------------------------------
# The additional parameter is threshold
def thresh(in_stream_window, threshold):
   return sum(in_stream_window) > threshold
t = Stream()
map_window(func=thresh, in_stream=x, out_stream=t, window_size=10,
           step_size=20, threshold=5) 
# For all j, : t[j] is True if and only if sum(x[20*j : 20*j+10]) > 5.
#
# Note: You can use any names as arguments in the
# definition of func, as in:
# def thresh(v, s): return sum(v) > w

#----------------------------------------------------------------    
# Example with state and additional parameters
#----------------------------------------------------------------
def maxes(in_stream_window, state, parameter):
   next_output_element = sum(in_stream_window) > parameter * state
   next_state = max(state, sum(in_stream_window))
   return (next_output_element, next_state)
m = Stream()
map_window(func=maxes, in_stream=x, out_stream=m, state=0,
           window_size=20, step_size=10, parameter=0.5)
# in_stream_window on step j is x[10*j : 10*j + 20]
# state[j] = max(state[j-1], sum(x[10*j : 10*j + 20]))
# m[j] = sum(x[10*j : 10*j + 20]) > 0.5 * state[j]
