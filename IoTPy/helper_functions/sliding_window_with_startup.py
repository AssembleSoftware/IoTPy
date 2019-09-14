import numpy as np
import sys
import os
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("/agent_types"))
from agent import Agent, InList
from stream import Stream, StreamArray
from helper_control import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from run import run
from iot import iot

class sliding_window_with_startup(object):
    def __init__(self, func, in_stream, out_stream, window_size, step_size):
        self.func = func
        self.in_stream = in_stream
        self.out_stream = out_stream
        self.window_size = window_size
        self.step_size = step_size
        self.starting = True
        self.start_ptr = 0
        self.end_ptr = 0
        iot(func=self.extend, in_stream=self.in_stream)
    def extend(self, A):
        if self.starting:
            while self.end_ptr < len(A):
                self.end_ptr = self.end_ptr + self.step_size
                if self.end_ptr > self.window_size:
                    self.start_ptr = self.end_ptr - self.window_size
                window = A[self.start_ptr : self.end_ptr]
                self.out_stream.append(self.func(window))
            if self.end_ptr > self.window_size:
                self.starting = False
                return self.start_ptr + self.step_size
            else:
                return 0
        else:
            self.start_ptr = 0
            while self.start_ptr + self.window_size <= len(A):
                window = A[self.start_ptr : self.start_ptr + self.window_size]
                self.out_stream.append(self.func(window))
                self.start_ptr += self.step_size
            return self.start_ptr
#---------------------------------------------------------------------------
#     TESTS
#---------------------------------------------------------------------------

def test_sliding_window_with_startup():
    x = StreamArray(dtype=int)
    y = StreamArray(dtype=int)
    sw = sliding_window_with_startup(
        func=np.sum, in_stream=x, out_stream=y, window_size=10, step_size=3)
    # tests
    x.extend(np.arange(6, dtype=int))
    run()
    assert np.array_equal(recent_values(y), np.array([3, 15]))
    x.extend(np.arange(6, 9, dtype=int))
    run()
    assert np.array_equal(recent_values(y), np.array([3, 15, 36]))
    x.extend(np.arange(9, 15, dtype=int))
    run()
    assert np.array_equal(
        recent_values(y),
        np.array([3,  15,  36,  65,  95]))
    x.extend(np.arange(15, 30, dtype=int))
    run()
    assert np.array_equal(
        recent_values(y),
        np.array([3,  15,  36,  65,  95, 125, 155, 185, 215, 245]))


if __name__ == '__main__':
    test_sliding_window_with_startup()
    
    
    
