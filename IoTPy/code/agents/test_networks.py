import sys
import os
sys.path.append(os.path.abspath("../"))

import time
#import threading

from agent import Agent, InList
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from element_agent import element_map_agent
from element_agent import element_filter_agent
from split import element_split_agent
from merge import element_merge_agent
from window_agent import window_map_agent
from sink import element_sink_agent, sink
from compute_engine import compute_engine
from helper_functions.check_agent_parameter_types import *
from helper_functions.recent_values import recent_values
from source import list_source

#----------------------------------------------------------
# DEFINE FUNCTIONS ENCAPSULATED BY AGENTS
# Test list_source
def f(v, multiplier):
    return multiplier*v
def double(v):
    return f(v, 2)
    
def split_function(v):
    if v%8:
        return [_no_value, v]
    else:
        return [v, _no_value]
    
def print_index(v, state, output_list):
    output_list.append(str(state) + ' : ' + str(v))
    return state+1 # next state

def check_sink(output_list):
    w =[]
    for i, v in enumerate(output_list):
        w.append((str(i) + ' : ' + str(v)))
    return w

#----------------------------------------------------------
def test_networks():
    # SPECIFY EXPECTED OUTPUT
    test_list = range(16)
    MULTIPLIER = 3
    expected_x = [f(v, MULTIPLIER) for v in test_list]
    expected_y = [double(v) for v in expected_x]
    expected_z = filter(lambda v: not v%4, expected_y)
    expected_r = filter(lambda v: not v%8, expected_z)
    expected_s = filter(lambda v: v%8, expected_z)
    expected_u = [sum(v) for v in zip(expected_r, expected_s)]
    def window_computation(lst, window_size, step_size, func):
        i = 0
        output_list = []
        while i + window_size <= len(lst):
            output_list.append(func(lst[i:i+window_size]))
            i += step_size
        return output_list
    expected_v = window_computation(
        expected_u, window_size=2, step_size=2, func=sum)
    output_list_for_sink = []
    expected_output_list_for_sink = check_sink(expected_v)

    #DECLARE STREAMS------------------------------------------------
    x = Stream('x')
    y = Stream('y')
    z = Stream('z')
    s = Stream('s')
    r = Stream('r')
    u = Stream('u')
    v = Stream('v')

    # DECLARE AGENTS ---------------------------------------------------
    list_thread  = list_source(
        function=f, out_stream=x, in_list=test_list, time_interval=0.1,
        multiplier=MULTIPLIER)
    element_map_agent(func=double, in_stream=x, out_stream=y)
    element_filter_agent(func=lambda v: not v%4, in_stream=y, out_stream=z)
    element_split_agent(func=split_function, in_stream=z, out_streams=[r,s])
    element_merge_agent(func=sum, in_streams=[r,s], out_stream=u)
    window_map_agent(func=sum, in_stream=u, out_stream=v, window_size=2, step_size=2)
    sink(func=print_index, in_stream=v, state=0, output_list=output_list_for_sink)

    # START SOURCE THREADS AND START COMPUTE ENGINE
    compute_engine.start()
    list_thread.start()

    # JOIN SOURCE THREADS AND STOP COMPUTE ENGINE
    list_thread.join()
    compute_engine.stop()

    # CHECK VALUES OF STREAMS
    assert recent_values(x) == expected_x
    assert recent_values(y) == expected_y
    assert recent_values(z) == expected_z
    assert recent_values(r) == expected_r
    assert recent_values(s) == expected_s
    assert recent_values(z) == expected_z
    assert recent_values(v) == expected_v
    assert output_list_for_sink == expected_output_list_for_sink

if __name__ == '__main__':
    test_networks()
