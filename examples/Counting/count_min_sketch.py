"""
Install PyProbables to use this code.
Straightforward use of CountMinSketch.
https://pyprobables.readthedocs.io/en/latest/code.html#count-min-sketches

Implementation is identical to bloom_filter_stream
"""
from probables import CountMinSketch

import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, _no_value, run
from IoTPy.agent_types.op import map_element
from IoTPy.helper_functions.print_stream import print_stream

def count_min_sketch_stream(in_stream, out_stream, count_min_sketch):
    """
    Parameters
    ----------
       in_stream: Stream
          The input stream of the agent.
          Each element of the input stream is a pair which
          is either ('add', object) or ('check', object).
          If ('add', z) appears in the input stream then
          z is added to the set.
          If ('check', z) appears then (z, 'True') appears
          on the output stream if z is in the filter, and
          (z, 'False') appears otherwise.
       out_stream: Stream
          The output stream of the agent.
          An element is added to the output stream when a 'check'
          function_name appears on the input stream.
          The output stream consists of pairs (object, boolean)
          where boolean is True if and only if object
          is in the input stream at this point.
       count_min_sketch: CountMinSketch
          An instance of the CountMinSketch class.

    """
    # The function for the map_element agent.
    def func(element):
        function_name, obj = element
        if function_name == 'add':
            count_min_sketch.add(obj)
            return _no_value
        elif function_name == 'check':
            return (obj, count_min_sketch.check(obj))
        else:
            raise ValueError
    # Create the map_element agent.
    map_element(func, in_stream, out_stream)


#---------------------------------------------------------------------------
#       TEST
#---------------------------------------------------------------------------
def test():
    count_min_sketch = CountMinSketch(width=1000, depth=20)

    x = Stream('Count Min Sketch input')
    y = Stream('Count Min Sketch output')
    count_min_sketch_stream(x, y, count_min_sketch=count_min_sketch)
    print_stream(y, y.name)

    # Run test data
    data=[('add', 'a'), ('add', 'b'), ('add', 'a'),
          ('check', 'c'), ('add', 'd'), ('check','a')]
    x.extend(data)
    run()

    data=[('add', 'c'), ('check', 'b'), ('check', 'a'),
          ('check', 'c'), ('check', 'e'), ('add', 'a')]
    x.extend(data)
    run()

if __name__ == '__main__':
    test()    

