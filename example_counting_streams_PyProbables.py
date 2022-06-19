"""
This code uses PyProbables:
https://pyprobables.readthedocs.io/en/latest/index.html
Install PyProbables to use this code.

This code is a straightforward application of the HeavyHitters class in
PyProbables. The heavy hitters (estimates of most frequent elements) in the
input stream are output.

"""
from probables import HeavyHitters

def f(element, heavy_hitters_object):
    """
    Parameters
    ----------
    element: str
        An element of in_stream is the string version of a
        method call to a heavy_hitters object. For example
        'add' for the method add, and 'heavy_hitters' for
        the method heavy_hitters.
    heavy_hitters_object: HeavyHitters
        An instance of HeavyHitters.
    """

    if element == 'heavy_hitters':
        print ('heavy hitters')
        print (heavy_hitters_object.heavy_hitters)
    else:
        # element must be ('add', object)
        function_name, obj = element
        if function_name == 'add':
            heavy_hitters_object.add(obj)
        else:
            raise ValueError

#---------------------------------------------------------------------
#      TESTS
#---------------------------------------------------------------------
def test_heavy_hitters_stream():
    from stream import Stream, run
    from example_operators import single_item
    heavy_hitters_object = HeavyHitters(num_hitters=2, width=2, depth=2)

    # Declare streams
    x = Stream('input_stream')
    # Create agents
    single_item(in_stream=x, func=f,
                    heavy_hitters_object=heavy_hitters_object)

    # Put data into stream and run
    x.extend([('add', 'a'), ('add', 'a'), ('add', 'a'), ('add', 'b'),
              ('add', 'c'), ('add', 'c'), ('add', 'c'),
              ('heavy_hitters'),
              ('add', 'a'), ('add', 'b'), ('add', 'c'), ('add', 'a'),
              ('heavy_hitters'),
              ('add', 'b'), ('add', 'c'), ('add', 'b'), ('add', 'b', ),
              ('heavy_hitters'),
              ('add', 'b'), ('add', 'b'), ('add', 'b'), ('add', 'b',),
              ('add', 'b'), ('add', 'b'), ('add', 'b'), ('add', 'b', ),
              ('heavy_hitters'),
              ('add', 'd'), ('add', 'd'), ('add', 'd'), ('add', 'd'),
              ('add', 'd'), ('add', 'd'), ('add', 'd'), ('add', 'd'),
              ('add', 'd'), ('add', 'd'), ('add', 'd'), ('add', 'd'),
              ('heavy_hitters')
                  ])
    run()

if __name__ == '__main__':
    test_heavy_hitters_stream()
