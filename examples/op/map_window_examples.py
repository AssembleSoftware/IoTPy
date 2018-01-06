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

scheduler = Stream.scheduler
# In the following, x is a stream that must be declared
# before the functions are called.
x = Stream('x')

#----------------------------------------------------------------    
# Example with no state and no additional parameters
#----------------------------------------------------------------
s = Stream()
map_window(func=sum, in_stream=x, out_stream=s, 
 window_size=2, step_size=10)
#y[j] = f(x[j*step_size : j*step_size + window_size]) for all j. 

#----------------------------------------------------------------    
# Example with state and no additional parameters
#----------------------------------------------------------------
this_list = range(10)
def comp(this_list, sum_of_previous_list):
   # Current state is sum_of_previous_list
   # Next state will be sum(this_list)
   return sum(this_list) > sum_of_previous_list, sum(this_list)
c = Stream()
# The initial state is 0
map_window(func=sums, in_stream=x, out_stream=c, 
           state=0, window_size=10, step_size=10)

#----------------------------------------------------------------    
# Example with no state and additional parameters
#----------------------------------------------------------------
def thresh(this_list, threshold):
   return sum(this_list) > threshold
t = Stream()
map_window(thresh, x, t, window_size=10, step_size=10, threshold=10)
# For all j, : y[j] is True if and only if sum(x[2*j : 2*j+4]) > 10.

#----------------------------------------------------------------    
# Example with state and additional parameters
#----------------------------------------------------------------
def maxes(this_list, max_of_sums, alpha):
   # The current window is this_list
   # The current state is max_of_sums
   # max_of_sums is the max over all windows so far
   # of sum(window).
   # alpha is a parameter whose value is specified in
   # the call to map_window.
   # The next state is the max over all past windows
   # and the current window. So, the next state is:
   # max(max_of_sums, sum(this_list))
   return (sum(this_list) > alpha * max_of_sums,
           max(max_of_sums, sum(this_list)))
m = Stream()
map_window(maxes, x, m, state=0, window_size=20, step_size=10, 
           alpha=0.5)

x.extend(range(100))
print 'x'
print recent_values(x)
scheduler.step()
print 'sum'
print recent_values(s)
print 'comp'
print recent_values(c)
print 'threshold'
print recent_values(t)
print 'maxes'
print recent_values(m)
