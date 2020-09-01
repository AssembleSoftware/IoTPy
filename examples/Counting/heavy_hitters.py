"""
This code uses PyProbables:
https://pyprobables.readthedocs.io/en/latest/index.html
Install PyProbables to use this code.

This code is a straightforward application of the HeavyHitters class in
PyProbables. The heavy hitters (estimates of most frequent elements) in the
input stream are placed on the result stream when ever the length of the
input stream is a multiple of the parameter, window_size.

"""
import copy
from probables import HeavyHitters

import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, _no_value, run
from IoTPy.agent_types.op import map_element
from IoTPy.helper_functions.print_stream import print_stream

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
            raise ValueError
        return _no_value
    map_element(func, in_stream, out_stream)

#---------------------------------------------------------------------
#      TESTS
#---------------------------------------------------------------------
def test_heavy_hitters_stream():
    heavy_hitters_object = HeavyHitters(width=1000, depth=5)
    x = Stream('input')
    y = Stream('output')
    #y = ggg(x, heavy_hitters_object=heavy_hitters_object)
    heavy_hitters_stream(x, y, heavy_hitters_object)
    x.extend([('add', 'a'), ('add', 'a'), ('add', 'a'), ('add', 'b'),
              ('heavy_hitters'),
              ('add', 'a'), ('add', 'b'), ('add', 'c'), ('add', 'a'),
              ('heavy_hitters'),
              ('add', 'b'), ('add', 'c'), ('add', 'b'), ('add', 'b'),
              ('heavy_hitters')])
    print_stream(y, y.name)
    run()

if __name__ == '__main__':
    test_heavy_hitters_stream()
