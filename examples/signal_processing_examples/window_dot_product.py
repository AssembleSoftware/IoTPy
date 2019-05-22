import numpy as np

import sys
import os
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath("../../gunshots"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
from generate_waves import generate_sine_wave, plot_signal
from stream import Stream, StreamArray
from op import map_window
from recent_values import recent_values

def window_dot_product(in_stream, out_stream, multiplicand_vector):
    def f(window, multiplicand_vector):
        return np.dot(window, multiplicand_vector)
    window_size = len(multiplicand_vector)
    map_window(
        f, in_stream, out_stream,
        window_size, multiplicand_vector=multiplicand_vector)

def test():
    x = Stream('x')
    y = Stream('y')
    window_dot_product(x, y, multiplicand_vector=[2, 100])
    x.extend(np.arange(4))
    Stream.scheduler.step()
    assert recent_values(y) == [100, 202, 304]

if __name__ == '__main__':
    test()
