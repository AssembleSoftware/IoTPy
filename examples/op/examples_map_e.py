"""
This module has examples of @map_e and @fmap_e

"""
import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))

# stream, helper_control are in IoTPy/IoTPy/core
from stream import Stream, _no_value, _multivalue, run
from helper_control import _no_value, _multivalue
# basics is in IoTPy/IoTPy/agent_types
from basics import map_e, fmap_e, map_list
# recent_values is in IoTPy/IoTPy/helper_functions
from recent_values import recent_values

def examples():
    # --------------------------------------------
    # Example: simple example of @map_e and @fmap_e

    # Specify agent functions
    @fmap_e
    def twice(v): return 2*v
    @map_e
    def double(v): return 2*v

    # Create streams
    x = Stream()
    y = Stream()

    # Create agents
    # Relational form: g(in_stream=x, out_stream=y)
    double(in_stream=x, out_stream=y)
    # Functional form: Create stream z.
    z = twice(x)

    # Put data into streams and run
    DATA = list(range(5))
    x.extend(DATA)
    run()

    # Check results.
    assert recent_values(z) == [2*v for v in DATA]
    assert recent_values(y) == [2*v for v in DATA]
    # --------------------------------------------

    # --------------------------------------------
    # Examples: @map_e and @fmap_e with keyword
    # arguments

    # Specify agent functions
    @map_e
    def g(v, addend): return v + addend
    @fmap_e
    def h(v, addend): return v + addend

    # Create streams
    x = Stream('x')
    y = Stream('y')

    # Create agents
    # keyword argument is addend
    ADDEND = 10
    # Relational form: g(in_stream=x, out_stream=y, **kwargs)
    g(x, y, addend=ADDEND)
    # Functional form: Create stream z. h(in_stream=x, **kwargs)
    z = h(x, addend=ADDEND)

    # Put data into streams and run
    DATA = list(range(10))
    x.extend(DATA)
    run()

    # Check results.
    assert recent_values(y) == [v+ADDEND for v in DATA]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------

    # --------------------------------------------
    # Examples @map_e and @fmap_e with keyword
    # arguments

    # Specify agent functions
    @map_e
    def multiply(v, multiplicand): return v * multiplicand
    @fmap_e
    def times(v, multiplicand): return v * multiplicand

    # Create streams
    x = Stream('x')
    y = Stream('y')

    # Create agents
    # keyword argument is multiplicand
    MULTIPLICAND=10
    # Relational form: multiply(in_stream=x, out_stream=y, **kwargs)
    multiply(x, y, multiplicand=MULTIPLICAND)
    # Functional form: Create stream z. times(in_stream=x, **kwargs)
    z = times(x, multiplicand=MULTIPLICAND)

    # Put data into streams and run
    DATA = list(range(4))
    x.extend(DATA)
    run()

    # Check results.
    assert recent_values(y) == [v*MULTIPLICAND for v in DATA]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------

    # --------------------------------------------
    # Examples @map_e and @fmap_e with state

    # Specify agent functions
    @map_e
    def deltas(input_value, state):
        difference = input_value - state
        next_state = input_value
        return difference, next_state
    @fmap_e
    def increments(u, v): return u - v, u

    # Create streams
    x = Stream('x')
    y = Stream('y')

    # Create agents
    # Initial state is 0.
    # Relational form
    deltas(in_stream=x, out_stream=y, state=0)
    # Functional form. Create stream z. increments(in_stream=x, state=0)
    z = increments(x, state=0)

    # Put data into streams and run
    x.extend([0, 1, 5, 21])
    run()

    # Check results.
    assert recent_values(y) == [0, 1, 4, 16]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------
    

    
    # --------------------------------------------
    # Examples @map_e and @fmap_e with state

    # Specify agent functions.
    @map_e
    def g(v, state):
        next_state = state + 1
        return v + state, next_state
    @fmap_e
    def h(v, state):
        next_state = state + 1
        return v + state, next_state

    # Create streams
    x = Stream('x')
    y = Stream('y')

    # Create agents
    # Initial state is 0.
    # Relational form g(in_stream=x, out_stream=y, state=0)
    g(x, y, state=0)
    # Functional form. Create stream z. h(in_stream=x, state=0)
    z = h(x, state=0)

    # Put data into streams and run
    DATA = list(range(10))
    x.extend(DATA)
    run()

    # Check results.
    assert recent_values(y) == [
        0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------

    # --------------------------------------------
    # Examples @map_e and @fmap_e with keyword
    # arguments and state

    # Specify agent functions.
    @map_e
    def g(v, state, addend):
        next_state = state + 1
        return v + addend + state, next_state
    @fmap_e
    def h(v, state, addend):
        next_state = state + 1
        return v + addend + state, next_state

    # Create streams.
    x = Stream('x')
    y = Stream('y')

    # Create agents
    # Initial state is 0, keyword argument is addend
    # Relational form g(in_stream=x, out_stream=y, state=0, **kwargs)
    ADDEND = 10
    g(x, y, state=0, addend=ADDEND)
    z = h(x, state=0, addend=ADDEND)

    # Put data into streams and run
    DATA = list(range(10))
    x.extend(DATA)
    run()

    # Check results.
    assert recent_values(y) == [
        10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------

    # --------------------------------------------
    # Example @map_e with keyword arguments and state

    # Specify agent functions.
    @map_e
    def anomalous_change(v, state, max_change):
        delta = v - state
        next_state = v
        next_output = True if delta > max_change else False
        return next_output, next_state
    @fmap_e
    def big_change(v, state, max_change):
        delta = v - state
        next_state = v
        next_output = True if delta > max_change else False
        return next_output, next_state

    # Create streams.
    x = Stream('x')
    y = Stream('y')

    # Create agents
    # Initial state is 0, keyword argument is max_change
    # Relational form
    # anomalous_change(in_stream=x, out_stream=y, state=0, **kwargs)
    anomalous_change(x, y, state=0, max_change=4)
    # Functional form
    # big_change(in_stream=x, state=0, max_change=4)
    z = big_change(x, state=0, max_change=4)

    # Put data into streams and run
    x.extend([0, 1, 6, 12, 11, 20, 22])
    run()

    # Check results.
    assert recent_values(y) == [
        False, False, True, True, False, True, False]
    assert recent_values(y) == recent_values(z)


    # --------------------------------------------
    # Example @fmap_e with keyword arguments and state
    # Define a function that uses #fmap_e
    # Specify exponential_smoothing
    def exponential_smoothing(x, a):
        """
        Parameters
        ----------
          x: Stream
          a: number
            where 0 <= a <= 1. The smoothing factor
        Returns
        -------
          y: Stream
          y[0] = x[0]
          y[n] = a*x[n] + (1-a)*y[n-1] for n > 0.

        """

        # Specify agent functions.
        @fmap_e
        def f(v, state, a):
            next_state = (v if state is 'empty'
                          else (1.0-a)*state + a*v)
            return next_state, next_state

        # return an agent specification
        return f(x, state='empty', a=a)
    # Finished definition of exponential_smoothing()

    # Create streams x, y and create the network of agents
    # specified by the function exponential_smoothing()
    x = Stream('x')
    y = exponential_smoothing(x, a=0.5)

    # Put data into input streams and run
    x.extend([16, 8, 4, 2, 1])
    run()

    # Check results.
    assert recent_values(y) == [16, 12.0, 8.0, 5.0, 3.0]
    # --------------------------------------------

    # --------------------------------------------
    # Examples @fmap_e with _no_value
    # This example shows how to specify a filter by using
    # _no_value. h(v) returns _no_value for odd v, and
    # so stream z contains only even numbers.

    # Specify agent functions.
    @fmap_e
    def h(v):
        return _no_value if v%2 else v

    # Create streams.
    x = Stream('x')

    # Create agents and stream z.
    z = h(x)

    # Put data into input streams and run
    DATA = list(range(10))
    x.extend(DATA)
    run()

    # Check results.
    assert recent_values(z) == [v for v in DATA if not v%2 ]
    assert recent_values(z) == [
        0, 2, 4, 6, 8]
    # --------------------------------------------

    # --------------------------------------------
    # Examples @fmap_e with _multi_value
    # Illustrates difference between returning
    # _multivalue(v) and v.

    # Specify agent functions.
    @fmap_e
    def h(v): return _multivalue(v)
    @fmap_e
    def g(v): return v

    # Create streams.
    x = Stream('x')

    # Create streams z, y and create the network of agents
    # specified by the functions h() and g().
    z = h(x)
    y = g(x)

    # Put data into input streams and run
    x.extend([('hello', 'Hola'), ('bye', 'adios')])
    run()

    # Check results.
    assert recent_values(z) == [
       'hello', 'Hola', 'bye', 'adios']
    assert recent_values(y) == [
        ('hello', 'Hola'), ('bye', 'adios')]
    # --------------------------------------------

    # --------------------------------------------
    # Examples @fmap_e with _multi_value and _no_value

    # Specify agent functions.
    @fmap_e
    def h(v):
        return _multivalue((v, v+10)) if v%2 else _no_value

    # Create streams.
    s = Stream()

    # Create stream t and create the network of agents
    # specified by the function h().
    t = h(s)

    # Put data into input streams and run.
    DATA = list(range(10))
    s.extend(DATA)
    run()

    # Check results.
    assert recent_values(t) == [
        1, 11, 3, 13, 5, 15, 7, 17, 9, 19]
    # --------------------------------------------

    
    # --------------------------------------------

    # Specify class and create an object of this class.
    class add(object):
        def __init__(self, addend):
            self.addend = addend
        def func(self, v):
            return _multivalue((v, v+self.addend)) if v%2 else _no_value

    add_object = add(10)

    # Specify agent functions.
    @fmap_e
    def h(v):
        return add_object.func(v)

    # Create streams.
    s = Stream()

    # Create stream t and create the network of agents
    # specified by the function h().
    t = h(s)

    # Put data into input streams and run.
    DATA = list(range(10))
    s.extend(DATA)
    run()

    # Check results.
    assert recent_values(t) == [1, 11, 3, 13, 5, 15, 7, 17, 9, 19]
    # --------------------------------------------

    # --------------------------------------------
    # Examples @fmap_e with a class

    # Specify class and create an object of this class.
    class average(object):
        def __init__(self, max_value):
            # Clip elements of the stream greater than max_value
            self.max_value = max_value
            self.count = 0
            self.total = 0.0
        def f(self, v):
            v = min(v, self.max_value)
            self.total += v
            self.count += 1
            return self.total/float(self.count)

    c = average(max_value=10)

    # Specify agent functions.
    @fmap_e
    def avg(v): return c.f(v)

    # Create streams.
    x = Stream('x')

    # Create stream y and create the network of agents
    # specified by the function avg().
    y = avg(x)

    # Put data into input streams and run.
    x.extend([1, 7, 20, 2])
    run()

    # Check results.
    assert recent_values(y) == [
        1, 4, 6, 5]
    # --------------------------------------------

if __name__ == '__main__':
    examples()
