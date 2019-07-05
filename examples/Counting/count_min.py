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
"""
import sys
import os

sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# stream is in ../../IoTPy/core
from stream import Stream
# op is in ../../IoTPy/agent_types
from op import map_window
# recent_values is in ../../IoTPy/helper_functions
from recent_values import recent_values

import copy
from probables import (HeavyHitters)

def heavy_hitters_stream(
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
    
def test_heavy_hitters():
    heavy_hitters_object = HeavyHitters(width=1000, depth=5)
    x = Stream('input')
    y = Stream('output')
    window_size = 4
    heavy_hitters_stream(x, y, window_size, heavy_hitters_object)
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

if __name__ == '__main__':
    test_heavy_hitters()
