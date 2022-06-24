"""
Install PyProbables to use this code.
Example of CountMinSketch with stream.
https://pyprobables.readthedocs.io/en/latest/code.html#count-min-sketches

Implementation is identical to bloom_filter_stream
"""
from probables import CountMinSketch


def f(v, count_min_sketch):
    
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
       count_min_sketch: CountMinSketch
          An instance of the CountMinSketch class.

    """
        
    function_name, obj = v
    if function_name == 'add': count_min_sketch.add(obj)
    elif function_name == 'check':
            print (obj, count_min_sketch.check(obj))
    else: raise ValueError

#---------------------------------------------------------------------------
#       TEST
#---------------------------------------------------------------------------
def test_count_min_sketch():
    from stream import Stream, run
    from example_operators import single_item
    count_min_sketch = CountMinSketch(width=1000, depth=20)

    # Declare streams
    x = Stream('Count Min Sketch input')

    # Create agents
    single_item(in_stream=x, func=f,
                    count_min_sketch=CountMinSketch(width=1000, depth=20))

    # Put data into stream and run
    data=[('add', 'a'), ('add', 'b'), ('add', 'a'),
          ('check', 'c'), ('add', 'd'), ('check','a')]
    x.extend(data)
    run()

    data=[('add', 'c'), ('check', 'b'), ('check', 'a'),
          ('check', 'c'), ('check', 'e'), ('add', 'a'),
          ('check', 'a')]
    x.extend(data)
    run()

if __name__ == '__main__':
    test_count_min_sketch()    

