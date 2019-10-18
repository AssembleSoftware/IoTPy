"""
This module tests element_agent.py

"""
import numpy as np

import sys
import os
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))

# agent and stream are in ../core
from agent import Agent
from stream import Stream, StreamArray, _no_value, _multivalue
# recent_values and run are in ../helper_functions
from recent_values import recent_values
from run import run
# op is in ../agent_types
from op import map_element, map_element_f
from op import filter_element, filter_element_f
from op import map_list, map_list_f
from op import timed_window
from basics import fmap_e, map_e

#------------------------------------------------------------------------------------------------
#                                     A SIMPLE EXAMPLE TEST
#------------------------------------------------------------------------------------------------
# This example is to illustrate the steps in the test.
# The later examples test several agents whereas this simple
# test only tests a single agent.
# The seven steps in this test may occur in different orders
# in the later tests.
def test_example_1():
    # Get scheduler
    scheduler = Stream.scheduler
    # Specify streams
    x = Stream('x')
    y = Stream('y')
    # Specify encapsulated functions (if any)
    def f(v): return 2*v
    # Specify agents.
    map_element(func=f, in_stream=x, out_stream=y)

    # Execute a step
    # Put test values in the input streams.
    x.extend(list(range(3)))
    # Execute a step
    run()
    # Look at recent values of output streams.
    assert recent_values(y) == [0, 2, 4]

    # Execute a step
    # Put test values in the input streams.
    x.extend([10, 20, 30])
    # Execute a step
    run()
    # Look at recent values of output streams.
    assert recent_values(y) == [0, 2, 4, 20, 40, 60]

    # Execute a step
    # Put test values in the input streams.
    x.extend([0, -10])
    # Execute a step
    run()
    # Look at recent values of output streams.
    assert recent_values(y) == [0, 2, 4, 20, 40, 60, 0, -20]

def test_example_2():
    # Get scheduler
    scheduler = Stream.scheduler
    # Specify streams
    x = Stream('x')
    y = Stream('y')
    # Specify encapsulated functions (if any)
    def f(v): return v < 3
    # Specify agents.
    filter_element(func=f, in_stream=x, out_stream=y)

    # Execute a step
    # Put test values in the input streams.
    x.extend(list(range(5)))
    # Execute a step
    run()
    # Look at recent values of output streams.
    assert recent_values(y) == [0, 1, 2]

def test_example_3():
    # Get scheduler
    scheduler = Stream.scheduler
    # Specify streams
    x = Stream('x')
    y = Stream('y')
    # Specify encapsulated functions (if any)
    def f(v, state):
        final, prefinal = state
        next_output = final + prefinal
        # In the next state:
        # prefinal becomes final
        # final becomes next_output
        next_state = next_output, final
        return next_output, next_state
    def g(v, divisor):
        if v % divisor == 0:
            return _no_value
        else:
            return v
    # Specify agents.
    map_element(func=f, in_stream=y, out_stream=x, state=(0, 1))
    map_element(func=g, in_stream=x, out_stream=y, divisor=4)
    # Execute a step
    # Put test values in the input streams.
    y.append(0)
    # Execute a step
    run()
    # Look at recent values of output streams.
    assert recent_values(x) == [1, 1, 2, 3, 5, 8]

    # Execute a step
    # Put test values in the input streams.
    y.append(0)
    # Execute a step
    run()
    # Look at recent values of output streams.
    assert recent_values(x) == \
      [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
    

def test_example_4():
    # Get scheduler
    scheduler = Stream.scheduler

    # Specify network: streams, functions, agents
    # (a) Specify streams
    x = Stream('x')
    y = Stream('y')
    # (b) Specify encapsulated functions (if any)
    def f(v, state):
        final, prefinal = state
        next_output = final + prefinal
        # In the next state:
        # prefinal becomes final
        # final becomes next_output
        next_state = next_output, final
        return next_output, next_state

    class G(object):
        def __init__(self):
            self.divisor = 4
        def g(self, v):
            if v % self.divisor == 0:
                return _no_value
            else:
                return v

    # (c) Specify agents.
    encapsulator = G()
    map_element(func=f, in_stream=y, out_stream=x, state=(0, 1))
    map_element(func=encapsulator.g, in_stream=x, out_stream=y)

    # Drive the network in steps.
    # Execute a step
    # Put test values in the input streams.
    y.append(0)
    # Execute a step
    run()
    # Look at recent values of output streams.
    assert recent_values(x) == [1, 1, 2, 3, 5, 8]

    # Execute a step after changing agent parameters
    encapsulator.divisor = 2
    # Put test values in the input streams.
    y.append(0)
    # Execute a step
    run()
    # Look at recent values of output streams.
    assert recent_values(x) == \
      [1, 1, 2, 3, 5, 8, 13, 21, 34]


def test_1():
    # From map_element_examples
    x = Stream('x')
    y = Stream('y')

    def f(in_stream_element):
        out_stream_element = 2*in_stream_element
        return out_stream_element
    map_element(func=f, in_stream=x, out_stream=y)

    x.extend(list(range(5)))
    run()
    assert recent_values(y) == [0, 2, 4, 6, 8]
      
def test_2():
    # From map_element_examples
    x = Stream('x')
    y = Stream('y')

    def multiply_and_add(
            in_stream_element, multiplicand, addend):
            out_stream_element = \
              multiplicand*in_stream_element + addend
            return out_stream_element

    map_element(func=multiply_and_add, in_stream=x, out_stream=y,
                multiplicand=2, addend=10)
    x.extend(list(range(5)))
    run()
    assert recent_values(y) == [10, 12, 14, 16, 18]

def test_3():
    # From map_element_examples
    x = Stream('x')
    y = Stream('y')

    # In this example, the output stream is the same as the input stream
    # except that only values that are less than the threshold are passed
    # through to the output stream. Here threshold is a keyword argument
    def f(in_stream_element, threshold):
        if in_stream_element < threshold:
                out_stream_element = in_stream_element
        else:
                out_stream_element = _no_value
        return out_stream_element
    map_element(func=f, in_stream=x, out_stream=y, threshold=5)
    x.extend(list(range(20)))
    run()
    assert recent_values(y) == [0, 1, 2, 3, 4]
    # If x is [0, 1, 2, 3, 4,....20] then y is [0, 1, 2, 3, 4]


def test_4():
    # From map_element_examples
    x = Stream('x')
    y = Stream('y')
    def f(in_stream_element):
            x, y = in_stream_element
            if x > 5 and y > 5:
                    out_stream_element = _multivalue((x,y))
            elif x > 5:
                    out_stream_element = x
            elif y > 5:
                    out_stream_element = y
            else:
                    out_stream_element = _no_value
            return out_stream_element
    map_element(func=f, in_stream=x, out_stream=y)
    x.extend( [(10, 10), (2, 20), (30, 3), (4, 4), (1, 3), (60, 70)] )
    run()
    assert recent_values(y) == [10, 10, 20, 30, 60, 70]
    
#------------------------------------------------------------------------------------------------
#                                     ELEMENT AGENT TESTS
#------------------------------------------------------------------------------------------------
def test_element_simple():
    # SPECIFY STREAMS
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
    # SPECIFY ENCAPSULATED FUNCTIONS (IF ANY)
    def double(v): return 2*v

    # SPECIFY AGENTS
    a = map_element(func=double, in_stream=x, out_stream=y, name='a')
    ymap = map_element_f(func=double, in_stream=x)
    #----------------------------------------------------------------    

    #----------------------------------------------------------------
    # Test filtering
    def filtering(v): return v <= 2
    # yfilter is a stream consisting of those elements in stream x with
    # values less than or equal to 2.
    # The elements of stream x that satisfy the boolean, filtering(), are
    # passed through.
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
    # Pass through elements in x0 where x0[i] <= state[i]
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
    filter_element(func=lambda v: v <= 5, in_stream=o, out_stream=n)
    map_element(func=lambda v: v+2, in_stream=n, out_stream=o)
    #----------------------------------------------------------------
            
    #----------------------------------------------------------------    
    # PUT TEST VALUES INTO INPUT STREAMS
    #----------------------------------------------------------------
    #   Put test values into streams x, x0 and n.        
    x.extend(list(range(3)))
    x0.extend([0, 1, 3, 3, 6, 8])
    n.append(0)
    
    # STEP 5: GET SCHEDULER
    scheduler = Stream.scheduler

    # STEP 6: EXECUTE A STEP OF THE SCHEDULER
    scheduler.step()

    # STEP 7: LOOK AT OUTPUT STREAMS
    assert recent_values(x) == [0, 1, 2]
    assert recent_values(y) == [0, 2, 4]
    assert recent_values(q0) == [0, 1, 3]
    assert recent_values(ymap) == recent_values(y)
    assert recent_values(yfilter) == [0, 1, 2]
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
    assert recent_values(q) == [0, 2]
    assert recent_values(q) == recent_values(p)
    assert recent_values(n) == [0, 2, 4]
    assert recent_values(o) == [2, 4, 6]
    #----------------------------------------------------------------

        
    #----------------------------------------------------------------    
    x.extend(list(range(3, 5, 1)))
    run()
    assert recent_values(x) == [0, 1, 2, 3, 4]
    assert recent_values(y) == [0, 2, 4, 6, 8]
    assert recent_values(ymap) == recent_values(y)
    assert recent_values(yfilter) == [0, 1, 2]
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
    assert recent_values(q) == [0, 2, 4]
    assert recent_values(q) == recent_values(p)
    #----------------------------------------------------------------        

    #----------------------------------------------------------------            
    w.append(0)
    run()
    assert recent_values(x) == [0, 1, 2, 3, 4]
    assert recent_values(y) == [0, 2, 4, 6, 8]
    assert recent_values(ymap) == recent_values(y)
    assert recent_values(yfilter) == [0, 1, 2]
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
    assert recent_values(q) == [0, 2, 4]
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
    run()
    expected_output = np.sin(input_array)
    assert np.array_equal(recent_values(n), expected_output)
    expected_output = expected_output[expected_output <= 0.5]
    assert np.array_equal(recent_values(o), expected_output)
    return

def test_timed_window():
    x = Stream('x')
    y = Stream('y')

    def f(v): return v

    timed_window(
        func=f, in_stream=x, out_stream=y,
        window_duration=10, step_time=10)
    x.extend([(1, 'a'), (8, 'b'), (12, 'c')])
    run()
    assert(recent_values(y) == [(10, [(1, 'a'), (8, 'b')])])

    x.extend([(14, 'd'), (36, 'e'), (43, 'g'), (75, 'h')])
    run()
    assert(recent_values(y) == [(10, [(1, 'a'), (8, 'b')]),
                                 (20, [(12, 'c'), (14, 'd')]),
                                 (40, [(36, 'e')]), (50, [(43, 'g')])])

    x.extend([(79, 'i'), (101, 'j')])
    run()
    assert(recent_values(y) == [
        (10, [(1, 'a'), (8, 'b')]), (20, [(12, 'c'), (14, 'd')]),
        (40, [(36, 'e')]), (50, [(43, 'g')]), (80, [(75, 'h'), (79, 'i')])])

    return

def test_map_list():
    scheduler = Stream.scheduler
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
    w = Stream('w')
    map_list(func = lambda v: v, in_stream=x, out_stream=y)
    def f(lst):
        return list(filter(lambda v: v%2, lst))
    def g(lst):
        return [v*2 if v%2 else v/2 for v in lst]
    map_list(f, x, z)
    map_list(g, x, w)

    x_values = list(range(10))
    x.extend(x_values)
    run()
    assert recent_values(y) == recent_values(x)
    assert recent_values(z) == f(x_values)
    assert recent_values(w) == g(x_values)

def test_stream_arrays_2():
    """
    Example where the input stream of an agent is a stream array and
    its output stream is not a stream array.
    """
    x = StreamArray(name='x', dimension=3, dtype=float)
    y = Stream()
    map_element(func=np.median, in_stream=x, out_stream=y)
    x.append(np.array([1., 2., 3.]))
    run()
    assert y.recent[:y.stop] == [2.0]
    x.extend(np.array([[4., 5., 6.], [7., 8., 9.]]))
    run()
    assert y.recent[:y.stop] == [2.0, 5.0, 8.0]

def test_class():
    class example(object):
        def __init__(self, multiplicand):
            self.multiplicand = multiplicand
            self.running_sum = 0
        def step(self, v):
            result = v * self.multiplicand + self.running_sum
            self.running_sum += v
            return result
    x = Stream()
    y = Stream()
    eg = example(multiplicand=2)
    map_element(func=eg.step, in_stream=x, out_stream=y)
    x.extend(list(range(5)))
    run()
    assert y.recent[:y.stop] == [0, 2, 5, 9, 14]

def test_halt_agent():
    def double(v): return v*2
    x = Stream('x')
    y = Stream('y')
    a = map_element(func=double, in_stream=x, out_stream=y)
    x.extend(list(range(5)))
    run()
    assert recent_values(y) == [0, 2, 4, 6, 8]
    a.halt()
    run()
    assert recent_values(y) == [0, 2, 4, 6, 8]
    x.extend(list(range(10,15)))
    run()
    assert recent_values(y) == [0, 2, 4, 6, 8]
    assert recent_values(x) == list(range(5)) + list(range(10,15))
    ##
    ## # What follows is nondeterministic and so may fail
    ## # the test.
    ## a.restart()
    ## run()
    ## assert recent_values(y) == [0, 2, 4, 6, 8]
    ## run()
    ## assert recent_values(y) == [0, 2, 4, 6, 8]
    ## x.extend(list(range(100,101)))
    ## run()
    ## assert recent_values(y) == [
    ##     0, 2, 4, 6, 8, 20, 22, 24, 26, 28, 200]

def test_initial_value():
    def double(v): return v*2
    x = Stream('x')
    y = Stream(name='y', initial_value=[0]*5)
    a = map_element(func=double, in_stream=x, out_stream=y)
    x.extend(list(range(5)))
    run()
    assert recent_values(y) == [0]*5 + [0, 2, 4, 6, 8]

def test_multiple_relations():
    def double(v): return v*2
    def add10(v): return v+10
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
    a = map_element(func=add10, in_stream=z, out_stream=y)
    b = map_element(func=double, in_stream=x, out_stream=y)
    c = map_element(func=double, in_stream=x, out_stream=y)
    x.extend(list(range(5)))
    z.extend(list(range(100, 106)))
    run()
    ## # Nondeterministic.
    ## assert recent_values(y) == [
    ##     0, 2, 4, 6, 8, 0, 2, 4, 6, 8,
    ##     110, 111, 112, 113, 114, 115]

def test_multiple_relations_2():
    @map_e
    def double(v): return v*2
    x = Stream('x', [10, 11])
    y = Stream('y')
    double(x, y)
    double(x, y)
    x.extend(list(range(5)))
    run()

    ## # Nondeterministic.
    ## assert recent_values(y) == [
    ##     0, 2, 4, 6, 8, 0, 2, 4, 6, 8,
    ##     110, 111, 112, 113, 114, 115]

def test_multiple_functions():
    @fmap_e
    def double(v): return v*2
    @fmap_e
    def add10(v): return v+10
    x = Stream('x')
    y = double(x)
    y = add10(x)
    x.extend(list(range(5)))
    run()
    assert recent_values(y) == [10, 11, 12, 13, 14]
    

def test_class():
    class C(object):
        def __init__(self):
            return
        def f(self, value):
            if value > 0:
                return self.pos(value)
            else:
                return self.neg(value)
        def pos(self, value):
            return value * value
        def neg(self, value):
            return value + value

    s = Stream('s')
    t = Stream('t')
    c = C()
    @map_e
    def g(v): return c.f(v)
    g(in_stream=s, out_stream=t)
    s.extend(list(range(-4, 4)))
    run()
    assert (recent_values(t) == [
        -8, -6, -4, -2, 0, 1, 4, 9])
    
def test_None_in_stream():
    x = Stream('x', discard_None=False)
    y = Stream(name='y', discard_None=False)
    z = Stream(name='z')
    map_element(lambda v: v, x, y)
    map_element(lambda v: v, x, z)
    x.extend([0, None, 1, None, 2, _no_value, 3])
    run()
    assert (recent_values(y) == [0, None, 1, None, 2, 3])
    assert (recent_values(z) == [0, 1, 2, 3])
            
        

def test_element():
    test_1()
    test_2()
    test_3()
    test_4()
    test_example_1()
    test_example_2()
    test_example_3()
    test_example_4()
    test_element_simple()
    test_timed_window()
    test_map_list()
    test_stream_arrays_2()
    test_class()
    test_halt_agent()
    test_initial_value()
    test_multiple_relations()
    test_multiple_functions()
    test_multiple_relations_2()
    test_class()
    test_None_in_stream()
    print ('TEST OF OP (ELEMENT) IS SUCCESSFUL')
    
if __name__ == '__main__':
    test_element()

    
    
    
    
    

