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
sys.path.append("../../IoTPy/")
sys.path.append("../../IoTPy/core")
sys.path.append("../../IoTPy/agent_types")
sys.path.append("../../IoTPy/helper_functions")

# stream is in IoTPy/IoTPy/core
from stream import Stream, run
# op, check_agent_parameter_types are in IoTPy/IoTPy/agent_types
from op import filter_element
from check_agent_parameter_types import *
# recent_values is in IoTPy/IoTPy/helper_functions
from recent_values import recent_values

def examples_filter_element():
    x = Stream('x')
    #----------------------------------------------------------------    
    # Filter to only have even numbers
    #----------------------------------------------------------------
    even = Stream()
    filter_element(func=lambda v: not v%2, in_stream=x, out_stream=even)
    # Example: If x = [0, 1, 2, 3, ... ] then y is [0, 2, 4, ...]

    #----------------------------------------------------------------    
    # Filter to only have odd numbers
    #----------------------------------------------------------------
    odd = Stream()
    filter_element(func=lambda v: v%2, in_stream=x, out_stream=odd)

    #----------------------------------------------------------------  
     # Filter to only have negative numbers
    #----------------------------------------------------------------
    neg = Stream('negative')
    filter_element(func=lambda v: v < 0, in_stream=x, out_stream=neg)

    #----------------------------------------------------------------  
     # Filter to only have non_negativenumbers
    #----------------------------------------------------------------
    non_neg = Stream('non_negative')
    filter_element(func=lambda v: v >= 0, in_stream=x, out_stream=non_neg)

    #----------------------------------------------------------------    
    # filter_element with state and no additional arguments
    #----------------------------------------------------------------
    def less_than_n(v, state):
        next_output_element = (v <= state)
        next_state = state+1
        return next_output_element, next_state
    y = Stream('y')
    less = Stream()
    filter_element(func=less_than_n, in_stream=y, out_stream=less, state=0)
    # State on j-th step is j.
    # less_than_n(v, state) returns (v < j) on the j-th step.
    # less filters out all elements v for which v > j
    # So if y is [1, 5, 0, 2, 6, 3] then since states are [ 0, 1, 2, 3, 4,..]
    # then since not(y[0] <= 0), not(y[1] <= 1),
    # y[2] <= 2, y[3] <=3, .... the sequence of outputs of the function
    # less_than_v are [(False, 0), (False, 1), (True, 2), (True, 3), ...]. So
    # the output stream contains y[2], y[3], ... or [0, 2, ...]

    #----------------------------------------------------------------    
    # filter_element with state and with additional keyword arguments
    #----------------------------------------------------------------
    # The keyword argument is addend.
    def less_than_n_plus_addend(v, state, addend):
        # return pair: boolean filter, next state
        return v <= state+addend, state+1
    z = Stream('z')
    less_addend = Stream()
    filter_element(func=less_than_n_plus_addend, in_stream=z, 
                   out_stream=less_addend, state=0, addend=3)
    # State on j-th step is j.
    # Stream less contains z[j] if and only if z[j] <= j+3
    # For example, if z = [2, 3, 3, 4, 10, 15, 7, .....] then the
    # output stream is [2, 3, 3, 4, 7, ...]

    #----------------------------------------------------------------    
    # filter out numbers above the threshold
    #----------------------------------------------------------------
    def threshold(v, threshold): return v > threshold
    above_threshold = Stream('above threshold')
    filter_element(func=threshold, in_stream=x,
                   out_stream=above_threshold, threshold=0)

    # Put data into input streams and run.
    DATA_x = list(range(-5, 5, 1))
    x.extend(DATA_x)
    DATA_y = [1, 5, 0, 2, 6, 3]
    y.extend(DATA_y)
    DATA_z = [2, 3, 3, 4, 10, 15, 7]
    z.extend(DATA_z)
    
    run()

    # Inspect output
    assert recent_values(even) == [-4, -2, 0, 2, 4]
    assert recent_values(odd) == [-5, -3, -1, 1, 3]
    assert recent_values(non_neg) == [0, 1, 2, 3, 4]
    assert recent_values(neg) == [-5, -4, -3, -2, -1]
    assert recent_values(less) == [0, 2, 3]
    assert recent_values(less_addend) == [2, 3, 3, 4, 7]
    assert recent_values(above_threshold) == [1, 2, 3, 4]

if __name__ == '__main__':
    examples_filter_element()
    
