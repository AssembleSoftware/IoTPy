import sys
import os
import threading
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../signal_processing_examples"))

# multicore is in ../../IoTPy/multiprocessing
from multicore import shared_memory_process, Multiprocess
# op, sink, source, merge are in ../../IoTPy/agent_types
from op import map_element
from sink import stream_to_file
from source import source_list_to_stream
from merge import zip_map
# stream is in ../../IoTPy/core
from stream import Stream, StreamArray
# window_dot_product is in ../signal_processing_examples
from window_dot_product import window_dot_product

def exponential_smooth_and_add(in_stream, out_stream, smoothing_factor):
    """
    With input stream x and output stream y:
    y[n] = x[n] + a*x[n-1] + .. + a^m * x[n-m]
    where a is smoothing_factor

    """
    def f(in_stream_element, state, a):
        next_state = state*a + in_stream_element
        # return out_stream_element, next_state
        # Note: out_stream_element = next_state
        return next_state, next_state
    # Create a map_element agent
    map_element(f, in_stream, out_stream,
                state=0.0, a=smoothing_factor)
    
def exponential_smoothing(in_stream, out_stream, smoothing_factor):
    """
    With input stream x and output stream y:
    y[0] = x[0]
    y[n] = a*x[n] + (1-a)*y[n-1]
    where a is smoothing_factor

    """
    def f(in_stream_element, state, a):
        if state is 'empty':
            next_state = in_stream_element
        else:
            next_state = (1.0-a)*state+ a*in_stream_element
            # return out_stream_element, next_state
            # Note: out_stream_element = next_state
            # So, return next_state, next_state
        return next_state, next_state
    # Create a map_element agent
    map_element(f, in_stream, out_stream,
                state='empty', a=smoothing_factor)


#-----------------------------------------------------------------------
#            TESTS
#-----------------------------------------------------------------------
def test_exponential_smooth_and_add(source_list, smoothing_factor):
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)

    def compute_func(in_streams, out_streams):
        stream_for_filing = Stream()
        exponential_smooth_and_add(
            in_streams[0], stream_for_filing, smoothing_factor)
        # Store output
        stream_to_file(stream_for_filing, 'exponential_smooth_and_add.txt')

    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc')
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()

def test_exponential_smoothing(source_list, smoothing_factor):
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)

    def compute_func(in_streams, out_streams):
        stream_for_filing = Stream()
        exponential_smoothing(
            in_streams[0], stream_for_filing, smoothing_factor)
        # Store output
        stream_to_file(stream_for_filing, 'exponential_smoothing.txt')

    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc')
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()

def test():
    """
    The test produces two files:
        exponential_smooth_and_add.txt
    and
        exponential_smoothing.txt
    The file exponential_smooth_and_add.txt should contain:
    1.0
    0.5
    0.25
    0.125
    0.0625
    0.03125
    1.0
    1.5
    1.75
    1.875
    1.9375
    1.96875
    The file exponential_smoothing.txt should contain:
    1
    0.5
    0.25
    0.125
    0.0625
    0.03125
    1
    1.0
    1.0
    1.0
    1.0
    1.0

    """
    source_list = [1, 0, 0, 0, 0, 0]
    multiplier = 0.5
    test_exponential_smooth_and_add(source_list, multiplier)
    test_exponential_smoothing(source_list, multiplier)
    source_list = [1, 1, 1, 1, 1, 1]
    test_exponential_smooth_and_add(source_list, multiplier)
    test_exponential_smoothing(source_list, multiplier)

if __name__ == '__main__':
    test()
    
    
        
    
