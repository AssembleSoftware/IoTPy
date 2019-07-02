import numpy as np

import sys
import os
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath("../../gunshots"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
from stream import Stream, StreamArray
from op import map_window
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

    """
    def f(window, multiplicand_vector):
        return np.dot(window, multiplicand_vector)
    window_size = len(multiplicand_vector)
    map_window(
        f, in_stream, out_stream,
        window_size, multiplicand_vector=multiplicand_vector)

#----------------------------------------------------------------
# TESTS
#----------------------------------------------------------------
def test():
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

if __name__ == '__main__':
    test()
