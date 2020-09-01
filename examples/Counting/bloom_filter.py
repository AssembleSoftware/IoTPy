"""
Install PyProbables to use this code.
See: https://pyprobables.readthedocs.io/en/latest/code.html#bloomfilter
Straightforward use of BloomFilter.
"""
from probables import BloomFilter

import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, _no_value, run
from IoTPy.agent_types.op import map_element
from IoTPy.helper_functions.print_stream import print_stream

def bloom_filter_stream(in_stream, out_stream, bloom_filter):
    """
    Parameters
    ----------
       in_stream: Stream
          The input stream of the agent.
          Each element of the input stream is a pair which
          is either ('add', object) or ('check', object).
          If ('add', z) appears in the input stream then
          z is added to the Bloom Filter set.
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
       bloom_filter: BloomFilter
          An instance of the BloomFilter class.

    """
    # The function for the map_element agent.
    def func(element):
        function_name, obj = element
        if function_name == 'add':
            bloom_filter.add(obj)
            return _no_value
        elif function_name == 'check':
            return (obj, bloom_filter.check(obj))
        else:
            raise ValueError
    # Create the map_element agent.
    map_element(func, in_stream, out_stream)


#---------------------------------------------------------------------------
#       TEST
#---------------------------------------------------------------------------
def test():
    bloom_filter = BloomFilter(est_elements=1000, false_positive_rate=0.05)

    x = Stream('Bloom Filter input')
    y = Stream('Bloom Filter output')
    bloom_filter_stream(x, y, bloom_filter=bloom_filter)
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

