"""
This module tests element_agent.py

"""

import sys
import os
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))

from agent import Agent
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from op import *


#------------------------------------------------------------------------------------------------
#                                     ELEMENT AGENT TESTS
#------------------------------------------------------------------------------------------------
def test_element_simple():
    m = Stream('m')
    n = Stream('n')
    o = Stream('o')
    q = Stream('q')
    r = Stream('r')
    s = Stream('s')
    t = Stream('t')
    u = Stream('u')
    v = Stream('v')
    w = Stream('w')
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
    
    
    #----------------------------------------------------------------    
    # Test simple map using map_element
    # func operates on an element of the input stream and returns an element of
    # the output stream.
    def double(v): return 2*v

    a = map_element(func=double, in_stream=x, out_stream=y, name='a')
    ymap = map_element_f(func=double, in_stream=x)
    #----------------------------------------------------------------    

    #----------------------------------------------------------------
    # Test filtering
    def filtering(v): return v <= 2
    # yfilter is a stream consisting of those elements in stream x with
    # values greater than 2.
    # The elements of stream x that satisfy the boolean, filtering(), are
    # filtered out.
    yfilter = filter_element_f(func=filtering, in_stream=x)
    #----------------------------------------------------------------    

    #----------------------------------------------------------------
    # Test map with state using map_element
    # func operates on an element of the input stream and state and returns an
    # element of the output stream and the new state.
    def f(x, state):
        return x+state, state+2

    b = map_element(func=f, in_stream=x, out_stream=z, state=0, name='b')
    bmap = map_element_f(func=f, in_stream=x, state=0)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test map with call streams
    # The agent executes a state transition when a value is added to call_streams.
    c = map_element(func=f, in_stream=x, out_stream=v, state=10,
                          call_streams=[w], name='c')
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test _no_value
    # func returns _no_value to indicate that no value
    # is placed on the output stream.
    def f_no_value(v):
        """ Filters out odd values
        """
        if v%2:
            # v is odd. So filter it out.
            return _no_value
        else:
            # v is even. So, keep it in the output stream.
            return v

    no_value_stream = Stream(name='no_value_stream')
    no_value_agent = map_element(
        func=f_no_value, in_stream=x, out_stream=no_value_stream,
        name='no_value_agent')

    no_value_map = map_element_f(func=f_no_value, in_stream=x)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test _multivalue
    # func returns _multivalue(output_list) to indicate that
    # the list of elements in output_list should be placed in the
    # output stream.
    def f_multivalue(v):
        if v%2:
            return _no_value
        else:
            return _multivalue([v, v*2])

    multivalue_stream = Stream('multivalue_stream')
    multivalue_agent = map_element(
        func=f_multivalue, in_stream=x, out_stream=multivalue_stream,
        name='multivalue_agent')
    multivalue_map = map_element_f(func=f_multivalue, in_stream=x)
    #----------------------------------------------------------------    

    #----------------------------------------------------------------    
    # Test map_element with args
    def function_with_args(x, multiplicand, addition):
        return x*multiplicand+addition

    ## EXPLANATION FOR agent BELOW
    ## agent_test_args = map_element(
    ##     func=function_with_args, in_stream = x, out_stream=r,
    ##     state=None, call_streams=None, name='agent_test_args',
    ##     multiplicand=2, addition=10)

    agent_test_args = map_element(
        function_with_args, x, r,
        None, None, 'agent_test_args',
        2, 10)
    stream_test_args = map_element_f(function_with_args, x, None, 2, 10)
    #----------------------------------------------------------------        

    #----------------------------------------------------------------
    # Test map_element with kwargs
    agent_test_kwargs = map_element(
        func=function_with_args, in_stream = x, out_stream=u,
        state=None, call_streams=None, name='agent_test_kwargs',
        multiplicand=2, addition=10)
    #----------------------------------------------------------------    

    #----------------------------------------------------------------
    # Test map_element with state and kwargs
    # func operates on an element of the input stream and state and returns an
    # element of the output stream and the new state.
    def f_map_args_kwargs(u, state, multiplicand, addend):
        return u*multiplicand+addend+state, state+2

    agent_test_kwargs_and_state = map_element(
        func=f_map_args_kwargs, in_stream=x, out_stream=s,
        state=0, name='agent_test_kwargs_and_state',
        multiplicand=2, addend=10)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test map_element with state and args
    aa_map_args_agent = map_element(
        f_map_args_kwargs, x, t,
        0, None, 'aa_map_args_agent',
        2, 10)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test filter_element
    def is_even_number(v):
        return not v%2
    filter_element(func=is_even_number, in_stream=x, out_stream=q)
    #----------------------------------------------------------------

    
    #----------------------------------------------------------------
    # Test filter_element with state
    def less_than_n(v, state):
        return v <= state, state+1
    x0 = Stream('x0')
    q0 = Stream('q0')
    # state[i] = i
    # Discard elements in x0 where x0[i] <= state[i]
    filter_element(
        func=less_than_n, in_stream=x0, out_stream=q0, state=0)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test filter_element_stream
    # p is a stream consisting of odd-numbered elements of x
    # Even-numbered elements are filtered out.
    p = filter_element_f(is_even_number, x)
    #----------------------------------------------------------------

    #----------------------------------------------------------------
    # Test cycles in the module connection graph
    filter_element(func=lambda v: v >= 5, in_stream=o, out_stream=n)
    map_element(func=lambda v: v+2, in_stream=n, out_stream=o)
    #----------------------------------------------------------------
            
    #----------------------------------------------------------------    
    # PUT VALUES INTO STREAMS
    #----------------------------------------------------------------
    #   FIRST STEP        
    x.extend(range(3))
    x0.extend([0, 1, 3, 3, 6, 8])
    n.append(0)
    scheduler = Stream.scheduler
    scheduler.step()
    assert recent_values(x) == [0, 1, 2]
    assert recent_values(y) == [0, 2, 4]
    assert recent_values(q0) == [3, 6, 8]
    assert recent_values(ymap) == recent_values(y)
    assert recent_values(yfilter) == []
    assert recent_values(z) == [0, 3, 6]
    assert recent_values(bmap) == recent_values(z)
    assert recent_values(v) == []
    assert recent_values(no_value_stream) == [0, 2]
    assert recent_values(no_value_map) == recent_values(no_value_stream)
    assert recent_values(multivalue_stream) == [0, 0, 2, 4]
    assert recent_values(multivalue_map) == recent_values(multivalue_stream)
    assert recent_values(r) == [10, 12, 14]
    assert recent_values(stream_test_args) == recent_values(r)
    assert recent_values(u) == recent_values(r)
    assert recent_values(s) == [10, 14, 18]
    assert recent_values(s) == recent_values(t)
    assert recent_values(q) == [1]
    assert recent_values(q) == recent_values(p)
    assert recent_values(n) == [0, 2, 4]
    assert recent_values(o) == [2, 4, 6]
    #----------------------------------------------------------------

        
    #----------------------------------------------------------------    
    x.extend(range(3, 5, 1))
    scheduler.step()
    assert recent_values(x) == [0, 1, 2, 3, 4]
    assert recent_values(y) == [0, 2, 4, 6, 8]
    assert recent_values(ymap) == recent_values(y)
    assert recent_values(yfilter) == [3, 4]
    assert recent_values(z) == [0, 3, 6, 9, 12]
    assert recent_values(bmap) == recent_values(z)
    assert recent_values(no_value_stream) == [0, 2, 4]
    assert recent_values(no_value_map) == recent_values(no_value_stream)
    assert recent_values(multivalue_stream) == [0, 0, 2, 4, 4, 8]
    assert recent_values(multivalue_map) == recent_values(multivalue_stream)
    assert recent_values(r) == [10, 12, 14, 16, 18]
    assert recent_values(stream_test_args) == recent_values(r)
    assert recent_values(u) == recent_values(r)
    assert recent_values(s) == [10, 14, 18, 22, 26]
    assert recent_values(s) == recent_values(t)
    assert recent_values(q) == [1, 3]
    assert recent_values(q) == recent_values(p)
    #----------------------------------------------------------------        

    #----------------------------------------------------------------            
    w.append(0)
    scheduler.step()
    assert recent_values(x) == [0, 1, 2, 3, 4]
    assert recent_values(y) == [0, 2, 4, 6, 8]
    assert recent_values(ymap) == recent_values(y)
    assert recent_values(yfilter) == [3, 4]
    assert recent_values(z) == [0, 3, 6, 9, 12]
    assert recent_values(bmap) == recent_values(z)
    assert recent_values(v) == [10, 13, 16, 19, 22]
    assert recent_values(no_value_stream) == [0, 2, 4]
    assert recent_values(no_value_map) == recent_values(no_value_stream)
    assert recent_values(multivalue_stream) == [0, 0, 2, 4, 4, 8]
    assert recent_values(multivalue_map) == recent_values(multivalue_stream)
    assert recent_values(r) == [10, 12, 14, 16, 18]
    assert recent_values(stream_test_args) == recent_values(r)
    assert recent_values(u) == recent_values(r)
    assert recent_values(s) == [10, 14, 18, 22, 26]
    assert recent_values(s) == recent_values(t)
    assert recent_values(q) == [1, 3]
    assert recent_values(q) == recent_values(p)
    #----------------------------------------------------------------


    #------------------------------------------------------------------------------------------------
    #                                     ELEMENT AGENT TESTS FOR STREAM ARRAY
    #------------------------------------------------------------------------------------------------
    import numpy as np

    m = StreamArray('m')
    n = StreamArray('n')
    o = StreamArray('o')

    map_element(func=np.sin, in_stream=m, out_stream=n)
    filter_element(func=lambda v: v <= 0.5, in_stream=n, out_stream=o)
    input_array = np.linspace(0.0, 2*np.pi, 20)
    m.extend(input_array)
    scheduler.step()
    expected_output = np.sin(input_array)
    assert np.array_equal(recent_values(n), expected_output)
    expected_output = expected_output[expected_output > 0.5]
    assert np.array_equal(recent_values(o), expected_output)
    return

def test_timed_window():
    scheduler = Stream.scheduler

    x = Stream('x')
    y = Stream('y')

    def f(v): return v

    timed_window(
        func=f, in_stream=x, out_stream=y,
        window_duration=10, step_time=10)

    x.extend([(1, 'a'), (8, 'b'), (12, 'c'), (14, 'd'), (32, 'e'), (50, 'f')])
    scheduler.step()
    assert recent_values(y) == [
        (10, [(1, 'a'), (8, 'b')]), (20, [(12, 'c'),
        (14, 'd')]), (40, [(32, 'e')])]

    return

def test_map_list():
    scheduler = Stream.scheduler
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
    w = Stream('w')
    map_list(func = lambda v: v, in_stream=x, out_stream=y)
    def f(lst):
        return filter(lambda v: v%2, lst)
    def g(lst):
        return [v*2 if v%2 else v/2 for v in lst]
    map_list(f, x, z)
    map_list(g, x, w)

    x_values = range(10)
    x.extend(x_values)

    scheduler.step()
    assert recent_values(y) == recent_values(x)
    assert recent_values(z) == f(x_values)
    assert recent_values(w) == g(x_values)

    
def test_element():
    test_element_simple()
    test_timed_window()
    test_map_list()
    print 'TEST OF OP (ELEMENT) IS SUCCESSFUL'
    
if __name__ == '__main__':
    test_element()

    
    
    
    
    

