import numpy as np

import sys
sys.path.append("../../IoTPy/core")
sys.path.append("../../IoTPy/agent_types")
sys.path.append("../../IoTPy/helper_functions")

# stream is in IoTPy/IoTPy/core
from stream import Stream, StreamArray
# op is in IoTPy/IoTPy/agent_types
from op import map_window
from basics import fmap_w
# recent_values is in IoTPy/IoTPy/helper_functions
from recent_values import recent_values



def window_dot_product(in_stream, out_stream, multiplicand_vector, step_size=1):
    """
    Parameters
    ----------
    in_stream: Stream
       input stream of agent
    out_stream: Stream
       output stream of agent
    multiplicand_vector: list or NumPy array
       length of multiplicand_vector must be strictly positive
       The dot product is applied between each sliding window
       and the multiplicand_vector
    step_size: int
       Must be positive
       The amount by which the sliding window moves on each step.

    Operation
    ---------
    Creates an agent which carries out the dot product of the
    multiplicand_vector and each sliding window.

    This example uses the wrapper map_window.

    """
    def f(window, multiplicand_vector):
        return np.dot(window, multiplicand_vector)

    map_window(
        f, in_stream, out_stream,
        window_size=len(multiplicand_vector), step_size=1,
        multiplicand_vector=multiplicand_vector)

def win_dot(in_stream, multiplicand_vector):
    """
    Same as the previous example except that this version
    uses the functional decorator @fmap_w instead of the
    wrapper.

    """
    @fmap_w
    def f(window, multiplicand_vector=multiplicand_vector):
        return np.dot(window, multiplicand_vector)
        
    return f(in_stream, window_size=len(multiplicand_vector), step_size=1,
      multiplicand_vector=multiplicand_vector)
        
    

#----------------------------------------------------------------
# TESTS
#----------------------------------------------------------------
def test_1():
    x = Stream('x')
    y = Stream('y')
    window_dot_product(x, y, multiplicand_vector=[2, 100])
    x.extend(np.arange(8))
    Stream.scheduler.step()
    assert recent_values(y) == [100, 202, 304, 406, 508, 610, 712]
    # y[n] = x[n]*2 + x[n+1]*100, for n = 0, 1, ..., 6
    # so, y[n] = 2*n + 100*(n+1)
    # Note that the length of recent_values(y) is 7 rather than 8
    # because the window size is 2 (i.e. the size of the multiplicand
    # vector).

def test_2():
    x = Stream('x')
    z = win_dot(x, multiplicand_vector=[2, 100])
    x.extend(np.arange(8))
    Stream.scheduler.step()
    assert recent_values(z) == [100, 202, 304, 406, 508, 610, 712]

if __name__ == '__main__':
    test_1()
    test_2()
