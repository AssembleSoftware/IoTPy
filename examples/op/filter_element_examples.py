"""
=======================
Filter Element Examples
=======================
agent maps the function func from its single input stream to its
single output stream.
    
This example demonstrates how to use :function:`filter_element` in 
agent_types/op.py on streams.
"""
import sys
import os
sys.path.append(os.path.abspath("../IoTPy/"))
sys.path.append(os.path.abspath("../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../IoTPy/core"))
sys.path.append(os.path.abspath("../IoTPy/agent_types"))

from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from op import filter_element

scheduler = Stream.scheduler
# In the following, x is a stream that must be declared
# before the functions are called.
x = Stream('x')
#----------------------------------------------------------------    
# Filter to only have odd numbers
#----------------------------------------------------------------
def is_odd_number(v):
    return not v%2
odd = Stream()
filter_element(func=is_odd_number, in_stream=x, out_stream=odd)
# Example: If x = [0, 1, 2,.... ] then y is [0, 2, 4, ...]

#----------------------------------------------------------------    
# Filter to only have even numbers
#----------------------------------------------------------------
def is_even_number(v):
    return v%2
even = Stream()
filter_element(func=is_even_number, in_stream=x, out_stream=even)

#----------------------------------------------------------------  
 # Filter to only have positive numbers
#----------------------------------------------------------------
# Test filtering
def positive(v): return v < 0
pos = Stream()
filter_element(func=positive, in_stream=x, out_stream=pos)

#----------------------------------------------------------------  
 # Filter to only have negativenumbers
#----------------------------------------------------------------
# Test filtering
def negative(v): return v >= 0
neg = Stream()
filter_element(func=negative, in_stream=x, out_stream=neg)

#----------------------------------------------------------------    
# filter_element with state and no additional arguments
#----------------------------------------------------------------
def less_than_n(v, state):
    # return boolean that filters, next state
    return v <= state, state+1
less = Stream()
filter_element(func=less_than_n, in_stream=x, out_stream=less, state=0)
# State on j-th step is j.
# Stream less contains x[j] if x[j] > j   

#----------------------------------------------------------------    
# filter_element with state and with additional keyword arguments
#----------------------------------------------------------------
def less_than_n_plus_addend(v, state, addend):
    # return pair: boolean filter, next state
    return v <= state+addend, state+1
less_addend = Stream()
filter_element(func=less_than_n_plus_addend, in_stream=x, 
               out_stream=less_addend, state=0, addend=10)
# State on j-th step is j.
# Stream less contains x[j] if and only if x[j] > j+10

#----------------------------------------------------------------    
# filter out numbers above the threshold
#----------------------------------------------------------------
def threshold(v, threshold): return v > threshold
thresh = Stream()
filter_element(func=threshold, in_stream=x, out_stream=thresh, threshold=0)

x.extend(range(-4, 5))
print 'x'
print recent_values(x)
scheduler.step()
print 'is odd number'
print recent_values(odd)
print 'is even number'
print recent_values(even)
print 'positive'
print recent_values(pos)
print 'negative'
print recent_values(neg)
print 'less than n'
print recent_values(less)
print 'less than n plus addend'
print recent_values(less_addend)
print 'threshold'
print recent_values(thresh)