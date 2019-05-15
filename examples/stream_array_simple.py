import sys
import os
sys.path.append(os.path.abspath("../"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../helper_functions"))

import numpy as np

from agent import Agent
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from op import map_window
from merge import merge_window, merge_window_f
from split import split_window
from multi import multi_window, multi_window_f
from sink import sink_window
from helper_control import _multivalue

def add(in_stream_array, out_stream_array,
              window_size, addend):
    def f(an_array):
        return _multivalue(an_array + addend)
    map_window(f,in_stream_array, out_stream_array,
        window_size=window_size,step_size=window_size)
    
def multiply(in_stream_array, out_stream_array,
              window_size, multiplicand):
    def f(an_array):
        return _multivalue(an_array*multiplicand)
    map_window(f,in_stream_array, out_stream_array,
        window_size=window_size,step_size=window_size)


def test():
    x = StreamArray(name='x', dtype=int)
    y = StreamArray(name='y', dtype=int)
    z = StreamArray(name='z', dtype=int)

    multiply(x, y, window_size=10, multiplicand=4)
    add(x, z, window_size=5, addend=100)
    
    x.extend(np.arange(20))
    Stream.scheduler.step()
    print 'Testing multiply'
    print 'multiplicand = 4'
    print recent_values(y)
    print
    print 'Testing add'
    print 'addend = 100'
    print recent_values(z)

if __name__ == '__main__':
    test()
