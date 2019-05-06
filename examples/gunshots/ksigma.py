"""
Subtract the mean (average) from a stream of numbers.

"""
import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../subtract_mean"))

from stream import Stream
from op import map_window
from print_stream import print_stream
import statistics

def ksigma(
        in_stream, out_stream,
        long_window_size, short_window_size,
        threshold):
    def f(window):
        difference_in_means = (
            statistics.mean(window[-short_window_size:]) -
            statistics.mean(window[:-short_window_size]))
        return (abs(difference_in_means)/
                statistics.stdev(window[:-short_window_size])
                > threshold)

def difference_in_means(
        in_stream, out_stream,
        long_window_size, short_window_size,
        threshold):
    
    map_window(f, in_stream, out_stream,
               long_window_size, step_size=1)

if __name__ == '__main__':
    import random

    # Create streams
    s = Stream('s')
    t = Stream('t')

    # Create agents
    ksigma(
        in_stream=s, out_stream=t,
        long_window_size=100, short_window_size=4,
        threshold=5)
    print_stream(t)

    # Drive network of agents with input data
    input_sequence = [random.random() for _ in range(100)]
    input_sequence.extend([10 + random.random() for _ in range(5)])
    input_sequence.extend([random.random() for _ in range(100)])
    s.extend(input_sequence)

    # Execute a step of the scheduler
    Stream.scheduler.step()
    
                
        
