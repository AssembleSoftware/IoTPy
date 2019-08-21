"""
This module has examples of @map_e and @fmap_e

"""
import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))

# stream is in ../../IoTPy/core
from stream import Stream, _no_value, _multivalue
# helper_control, recent_values, run, basics are in
# ../../IoTPy/helper_functions
from recent_values import recent_values
from helper_control import _no_value, _multivalue
from run import run
from basics import map_e, fmap_e

def examples():
    # --------------------------------------------
    # Examples @map_e and @fmap_e
    @fmap_e
    def twice(v): return 2*v

    @map_e
    def double(v): return 2*v
    
    x = Stream()
    y = Stream()
    # Relational form: g(in_stream=x, out_stream=y)
    double(in_stream=x, out_stream=y)
    # Functional form: Create stream z.
    z = twice(x)
    # Put data into input stream and run
    x.extend(range(5))
    run()
    # Check values
    assert recent_values(z) == [0, 2, 4, 6, 8]
    assert recent_values(y) == [0, 2, 4, 6, 8]
    # --------------------------------------------

    # --------------------------------------------
    # Examples @map_e and @fmap_e with keyword
    # arguments
    x = Stream('x')
    y = Stream('y')
    @map_e
    def g(v, addend): return v + addend
    @fmap_e
    def h(v, addend): return v + addend

    g(x, y, addend=10)
    z = h(x, addend=10)
    
    x.extend(range(10))
    run()
    assert recent_values(y) == [
        10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------

    # --------------------------------------------
    # Examples @map_e and @fmap_e with keyword
    # arguments
    x = Stream('x')
    y = Stream('y')
    @map_e
    def multiply(v, multiplicand): return v * multiplicand
    @fmap_e
    def times(v, multiplicand): return v * multiplicand

    multiply(x, y, multiplicand=10)
    z = times(x, multiplicand=10)
    
    x.extend(range(4))
    run()
    assert recent_values(y) == [0, 10, 20, 30]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------

    # --------------------------------------------
    # Examples @map_e and @fmap_e with state
    @map_e
    def deltas(input_value, state):
        difference = input_value - state
        next_state = input_value
        return difference, next_state
    
    @fmap_e
    def increments(u, v): return u - v, u

    x = Stream('x')
    y = Stream('y')
    deltas(in_stream=x, out_stream=y, state=0)
    z = increments(x, state=0)

    x.extend([0, 1, 5, 21])
    run()
    assert recent_values(y) == [0, 1, 4, 16]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------
    

    
    # --------------------------------------------
    # Examples @map_e and @fmap_e with state
    @map_e
    def g(v, state):
        next_state = state + 1
        return v + state, next_state
    @fmap_e
    def h(v, state):
        next_state = state + 1
        return v + state, next_state

    x = Stream('x')
    y = Stream('y')
    g(x, y, state=0)
    z = h(x, state=0)
    x.extend(range(10))
    run()
    assert recent_values(y) == [
        0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------

    # --------------------------------------------
    # Examples @map_e and @fmap_e with keyword
    # arguments and state
    @map_e
    def g(v, state, addend):
        next_state = state + 1
        return v + addend + state, next_state
    @fmap_e
    def h(v, state, addend):
        next_state = state + 1
        return v + addend + state, next_state

    x = Stream('x')
    y = Stream('y')
    g(x, y, state=0, addend=10)
    z = h(x, state=0, addend=10)
    x.extend(range(10))
    run()
    assert recent_values(y) == [
        10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
    assert recent_values(y) == recent_values(z)
    # --------------------------------------------

    # --------------------------------------------
    # Example @map_e with keyword arguments and state
    @map_e
    def anomalous_change(v, state, max_change):
        delta = v - state
        next_state = v
        next_output = True if delta > max_change else False
        return next_output, next_state

    x = Stream('x')
    y = Stream('y')
    anomalous_change(x, y, state=0, max_change=4)
    x.extend([0, 1, 6, 12, 11, 20, 22])
    run()
    assert recent_values(y) == [
        False, False, True, True, False, True, False]


    # --------------------------------------------
    # Example @fmap_e with keyword arguments and state
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
        @fmap_e
        def f(v, state, a):
            next_state = (v if state is 'empty'
                          else (1.0-a)*state + a*v)
            return next_state, next_state

        return f(x, state='empty', a=a)

    x = Stream('x')
    y = exponential_smoothing(x, a=0.5)
    x.extend([16, 8, 4, 2, 1])
    run()
    assert recent_values(y) == [16, 12.0, 8.0, 5.0, 3.0]
    # --------------------------------------------

    # --------------------------------------------
    # Examples @fmap_e with _no_value
    @fmap_e
    def h(v):
        return _no_value if v%2 else v

    x = Stream('x')
    z = h(x)
    x.extend(range(10))
    run()
    assert recent_values(z) == [
        0, 2, 4, 6, 8]
    # --------------------------------------------

    # --------------------------------------------
    # Examples @fmap_e with _multi_value
    @fmap_e
    def h(v): return _multivalue(v)
    @fmap_e
    def g(v): return v
    
    x = Stream('x')
    z = h(x)
    y = g(x)
    x.extend([('hello', 'Hola'), ('bye', 'adios')])
    run()
    assert recent_values(z) == [
       'hello', 'Hola', 'bye', 'adios']
    assert recent_values(y) == [
        ('hello', 'Hola'), ('bye', 'adios')]
    # --------------------------------------------

    # --------------------------------------------
    # Examples @fmap_e with _multi_value
    @fmap_e
    def h(v):
        return _multivalue((v, v+10)) if v%2 else _no_value

    s = Stream()
    t = h(s)
    s.extend(range(10))
    Stream.scheduler.step()
    assert recent_values(t) == [
        1, 11, 3, 13, 5, 15, 7, 17, 9, 19]
    # --------------------------------------------

    
    # --------------------------------------------
    # Examples @fmap_e with a method of an objectclass add(object):
    class add(object):
        def __init__(self, addend):
            self.addend = addend
        def func(self, v):
            return _multivalue((v, v+self.addend)) if v%2 else _no_value

    add_object = add(10)
    @fmap_e
    def h(v):
        return add_object.func(v)

    s = Stream()
    t = h(s)
    s.extend(range(10))
    Stream.scheduler.step()
    assert recent_values(t) == [1, 11, 3, 13, 5, 15, 7, 17, 9, 19]
    # --------------------------------------------

    # --------------------------------------------
    # Examples @fmap_e with a method of an object
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
    @fmap_e
    def avg(v): return c.f(v)

    x = Stream('x')
    y = avg(x)
    x.extend([1, 7, 20, 2])
    run()
    assert recent_values(y) == [
        1, 4, 6, 5]
    # --------------------------------------------

if __name__ == '__main__':
    examples()
