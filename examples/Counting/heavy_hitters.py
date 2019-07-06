"""
This code uses PyProbables:
https://pyprobables.readthedocs.io/en/latest/index.html
Install PyProbables to use this code.

This code is a straightforward application of the
HeavyHitters class in PyProbables to create an agent with a
single input stream and a single output stream. The
heavy hitters (estimates of most frequent elements) in the
input stream are placed on the output stream when ever the
length of the input stream is a multiple of the
parameter window_size.

The direct way to use objects, such as instances of heavy_hitters,
in a stream is using map_element as shown below in the
heavy_hitters_stream agent

The heavy_hitters_window agent is an example of using such objects
with map_window.
"""
import sys
import os

sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# stream is in ../../IoTPy/core
from stream import Stream
# op is in ../../IoTPy/agent_types
from op import map_element, map_window
# recent_values is in ../../IoTPy/helper_functions
from recent_values import recent_values
# helper_control is in ../../IoTPy/helper_functions
from helper_control import _no_value

import copy
from probables import (HeavyHitters)

def heavy_hitters_stream(
        in_stream, out_stream, heavy_hitters_object):
    """
    Parameters
    ----------
       in_stream: Stream
          The input stream of the agent.
          An element of in_stream is the string version of a
          method call to a heavy_hitters object. For example
          'add' for the method add, and 'heavy_hitters' for
          the method heavy_hitters.
       out_stream: Stream
          The output stream of the agent.
          Each element of the output stream is a dict which
          represents the heavy hitters.
       heavy_hitters_object: HeavyHitters
          An instance of HeavyHitters.
    """
    def func(element):
        if element is 'heavy_hitters':
            return copy.copy(heavy_hitters_object.heavy_hitters)
        function_name, obj = element
        if function_name == 'add':
            heavy_hitters_object.add(obj)
        else:
            # The only functions supported here are heavy_hitters
            # and add. Include more functions when needed.
            raise ValueError
        return _no_value

    map_element(func, in_stream, out_stream)
            

def heavy_hitters_window(
        in_stream, out_stream, window_size,
        heavy_hitters_object):
    """
    Parameters
    ----------
       in_stream: Stream
          The input stream of the agent.
       out_stream: Stream
          The output stream of the agent.
          Each element of the output stream is a dict which
          represents the heavy hitters.
      window_size: int, positive
          An element is appended to the output stream when
          ever the input stream is a multiple of window_size.
       heavy_hitters_object: HeavyHitters
          An instance of HeavyHitters.
    """
    def f(window):
        for element in window:
            heavy_hitters_object.add(element)
        return copy.copy(heavy_hitters_object.heavy_hitters)
    map_window(f, in_stream, out_stream, window_size, step_size=window_size)
    
def test_heavy_hitters_window():
    heavy_hitters_object = HeavyHitters(width=1000, depth=5)
    x = Stream('input')
    y = Stream('output')
    window_size = 4
    heavy_hitters_window(x, y, window_size, heavy_hitters_object)
    x.extend(['a', 'a', 'a', 'b',
              # next window
              'a', 'b', 'c', 'a',
              # next window
              'b', 'c', 'b', 'b'])
    Stream.scheduler.step()
    print recent_values(y)
    # Output will be:
    # [{'a': 3, 'b': 1},
    # After next window
    # {'A': 5, 'c': 1, 'b': 2},
    # After next window
    # {'a': 5, 'c': 2, 'b': 5}]

def test_heavy_hitters_stream():
    heavy_hitters_object = HeavyHitters(width=1000, depth=5)
    x = Stream('input')
    y = Stream('output')
    heavy_hitters_stream(x, y, heavy_hitters_object)
    x.extend([('add', 'a'), ('add', 'a'), ('add', 'a'), ('add', 'b'),
              ('heavy_hitters'),
              ('add', 'a'), ('add', 'b'), ('add', 'c'), ('add', 'a'),
              ('heavy_hitters'),
              ('add', 'b'), ('add', 'c'), ('add', 'b'), ('add', 'b'),
              ('heavy_hitters')])

    Stream.scheduler.step()
    print recent_values(y)
    # Output will be:
    # [{'a': 3, 'b': 1},
    # {'A': 5, 'c': 1, 'b': 2},
    # {'a': 5, 'c': 2, 'b': 5}]

if __name__ == '__main__':
    #test_heavy_hitters_window()
    test_heavy_hitters_stream()
