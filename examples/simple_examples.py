
"""
Creates a multiprocess, multithread application to detect high
readings.

See https://www.assemblesoftware.com/examples/

"""

import sys
import os
import math
import numpy as np

sys.path.append(os.path.abspath("../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../IoTPy/core"))
sys.path.append(os.path.abspath("../IoTPy/helper_functions"))

# op, merge, source, sink, timed_agent are in ../../IoTPy/agent_types
from op import map_element, map_window
from merge import zip_map, merge_window
from timed_agent import timed_window, timed_zip_agent
from sink import stream_to_file
# agent is in ../../IoTPy/core
from agent import Agent
# check_agent_parameter_types is in ../../IoTPy/helper_functions
# helper_control and basics are in ../../IoTPy/helper_functions
from check_agent_parameter_types import *
from helper_control import _no_value
from print_stream import print_stream
from run import run
from recent_values import recent_values
from basics import map_w, map_e, merge_e


#--------------------------------------------------------
# Agent that evaluates a polynomial on values in a stream
#--------------------------------------------------------
@map_e
def evaluate_polynomial(number, polynomial):
    return np.polyval(polynomial, number)


#----------------------------------------------------
# Agent that computes the magnitude of a vector
#----------------------------------------------------
@merge_e 
def magnitude_of_vector(coordinates):
    return np.linalg.norm(coordinates)

#----------------------------------------------------
# Agent that subtracts the mean in a stream
#----------------------------------------------------
@map_w
def subtract_mean(window):
    return window[-1] - np.mean(window)

@map_w
def subtract_mean_block(window, block_size):
    return window[:block_size] - np.mean(window)


#---------------------------------------------------------
# Agent that subtracts the mean in a stream incrementally
#---------------------------------------------------------
class Incremental(object):
    def __init__(self):
        self.starting = True
        self.total = 0.0
        self.leaving_window = 0.0
    def subtract_mean(self, window):
        if self.starting:
            self.starting = False
            self.total = np.sum(window)
            self.leaving_window = window[0]
        else:
            self.total += window[-1] - self.leaving_window
            self.leaving_window = window[0]
        return window[-1] - self.total/float(len(window))


#----------------------------------------------------
# Agent that computes local anomalies
#----------------------------------------------------

@map_e
def time_of_crossing_threshold_f(value, state, threshold):
    signal = state if abs(value) > threshold else _no_value
    state += 1
    return (signal, state)

def time_of_crossing_threshold(in_stream, out_stream, threshold):
    time_of_crossing_threshold_f(
        in_stream, out_stream, state=0, threshold=threshold)

@map_e
def quenched_time_of_crossing_threshold_f(
        value, state, threshold, quench_duration):
    current_time, last_quench_time = state
    if ((current_time < last_quench_time + quench_duration) or
        (abs(value) <= threshold)):
        signal = _no_value
    else:
        signal = current_time
        last_quench_time = current_time
    next_state = (current_time+1, last_quench_time)
    return signal, next_state
    
def quenched_time_of_crossing_threshold(
        in_stream, out_stream, threshold, quench_duration):
    quenched_time_of_crossing_threshold_f(
        in_stream, out_stream, state=(0,0),
        threshold=threshold, quench_duration=quench_duration )

def quench(in_stream, out_stream, QUENCH_TIME):
    # state is the start time of the most recent quench period.
    # in_stream consists of a sequence of timestamps.
    @map_e
    def f(timestamped_value, state):
        timestamp, value = timestamped_value
        if timestamp - state < QUENCH_TIME:
            # This input arrived during the quench period
            # So, this input is discarded, and the state
            # doesn't change.
            return _no_value, state
        else:
            # This input arrived outside a quench period.
            # Start a new quench period.
            state = timestamp
            # This input is passed through.
            return timestamped_value, state
    f(in_stream, out_stream, state=-QUENCH_TIME-1)

#----------------------------------------------------
# Agent that aggregates local anomalies to form
# global anomalies
#----------------------------------------------------
def aggregate_anomalies(in_streams, out_stream, timed_window_size):
    """
    Parameters
    ----------
     in_streams: list of Stream
       Each stream in the list is a stream of floats with
       values 1.0 or 0.0
    out_stream: Stream
       Stream of floats.
       outstream[j] is a count of the number of streams s in
       in_streams where s[j-window: j] contains at least one
       1.0 value. The window_size allows for anomalies in
       different sensor streams to be treated as simultaneous
       provided they are within window_size of each other.

    """
    aggregator = aggregate_large_magnitudes(
        num_streams=2,
        threshold=2)
    zipped_stream = Stream('time zipped stream')
    global_anomalies_stream = Stream('global anomalies stream')
    timed_zip_agent(
        in_streams=in_streams,
        out_stream=zipped_stream)
    timed_window(
        func=aggregator.func,
        in_stream=zipped_stream,
        out_stream=global_anomalies_stream,
        window_duration=timed_window_size,
        step_time=1)
    def get_time(timed_element):
        timestamp, value = timed_element
        time_of_high_magnitude, num_high_magnitude = value
        return time_of_high_magnitude
    stream_to_file(
        in_stream=global_anomalies_stream,
        filename='global_anomalies.txt',
        element_function=get_time)

class aggregate_large_magnitudes(object):
    """
    Parameters
    ----------
    num_streams: int
       Positive integer, greater than 1.
       The number of streams that are aggregated
    threshold: int
       Generates a large magnitude if the number of
       input streams with anomalies equals or exceeds
       threshold

    Attributes
    ----------
    high_magnitude_streams: list of Boolean
       high_magnitude_streams[j] is True if the j-th
       stream is anomalously high magnitude.
    latest_output_timestamp: timestamp
       The last timestamp output by this agent.

    """
    def __init__(self, num_streams, threshold):
        self.num_streams = num_streams
        self.threshold = threshold
        # Initially assume that none of the streams are anomalously
        # high magnitude
        self.high_magnitude_streams = [False for _ in range(num_streams)]
        self.latest_output_timestamp = -1

    def func(self, window):
        # window is a list of pairs (timestamp, magnitudes)
        # magnitudes is a list of vector magnitudes with
        # one value for each stream.
        first_timestamp, first_magnitudes = window[0]
        for time_and_magnitudes in window:
            timestamp, magnitudes = time_and_magnitudes
            for i in range(self.num_streams):
                if (magnitudes[i] is not None and
                    not self.high_magnitude_streams[i]):
                    self.high_magnitude_streams[i] = True
            num_high_magnitude_streams = sum(self.high_magnitude_streams)
            if num_high_magnitude_streams >= self.threshold:
                new_timestamp = (first_timestamp + timestamp)/2
                self.high_magnitude_streams = [False for _ in range(self.num_streams)]
                if new_timestamp != self.latest_output_timestamp:
                    self.latest_output_timestamp = new_timestamp
                    return (new_timestamp, num_high_magnitude_streams)
            return _no_value


#----------------------------------------------------------------------
#   TESTS
#----------------------------------------------------------------------

def test_evaluate_polynomial():
    # Declare streams
    x = StreamArray('x')
    y = StreamArray('y')
    # Create agent
    evaluate_polynomial(x, y, polynomial=[1, 0, 1])
    # Put data in streams and run
    x.extend(np.array([1.0, 4.0, 3.0, 0.0]))
    run()
    assert np.array_equal(
        recent_values(y), np.array([2.0, 17.0, 10.0, 1.0]))

def test_magnitude_of_vector():
    # Declare streams
    x = StreamArray('x')
    y = StreamArray('y')
    z = StreamArray('z')
    magnitude_stream = StreamArray('magnitudes')
    # Create agent
    magnitude_of_vector([x,y,z], magnitude_stream)
    # Put data in streams and run
    x.extend(np.array([1.0, 4.0, 3.0]))
    y.extend(np.array([2.0, 4.0, 0.0]))
    z.extend(np.array([2.0, 2.0, 4.0]))
    run()
    assert np.array_equal(recent_values(magnitude_stream),
                           np.array([3.0, 6.0, 5.0]))



def test_subtract_mean():
    x = StreamArray('x')
    y = StreamArray('y')
    subtract_mean(x, y, window_size=4, step_size=1)
    x.extend(np.arange(8, dtype=float))
    run()
    assert (np.array_equal(
        recent_values(y),
        np.array([1.5, 1.5, 1.5, 1.5, 1.5])))

    x = StreamArray('x')
    y = StreamArray('y')
    window_size=3
    step_size=1
    subtract_mean(x, y, window_size, step_size)
    x.extend(np.array([1.0, 2.0, 0.0, 4.0, 2.0,
                       0.0, 1.0, 2.0, 0.0]))
    run()
    assert (np.array_equal(
        recent_values(y),
        np.array([-1.0,  2.0,  0.0, -2.0,  0.0,  1.0, -1.0])))

    x = StreamArray('x')
    y = StreamArray(name='y', initial_value=np.zeros(window_size-1))
    subtract_mean(x, y, window_size=3, step_size=1)
    x.extend(np.array([1.0, 2.0, 0.0, 4.0, 2.0,
                       0.0, 1.0, 2.0, 0.0]))
    run()
    assert (np.array_equal(
        recent_values(y),
        np.array([0.0, 0.0, -1.0,  2.0,  0.0, -2.0,  0.0,  1.0, -1.0])))

    
    x = StreamArray('x')
    y = StreamArray('y')
    incremental = Incremental()
    @map_w
    def incremental_subtract_mean(window):
        return incremental.subtract_mean(window)
    
    incremental_subtract_mean(x, y, window_size=3, step_size=1)
    x.extend(np.array([1.0, 2.0, 0.0, 4.0, 2.0,
                       0.0, 1.0, 2.0, 0.0]))
    run()
    assert (np.array_equal(
        recent_values(y),
        np.array([-1.0,  2.0,  0.0, -2.0,  0.0,  1.0, -1.0])))
    
def test_subtract_mean_block():
    x = StreamArray('x')
    y = StreamArray('y')
    subtract_mean_block(x, y, window_size=4, step_size=4, block_size=4)
    x.extend(np.arange(20, dtype=float))
    run()
    print (recent_values(y))

def test_time_of_crossing_threshold():
    # Declare streams
    x = StreamArray('x')
    y = StreamArray('y', dtype='int')
    # Declare agent
    time_of_crossing_threshold(x, y, threshold=2.5)
    # Put data in streams and run
    x.extend(np.array([1.0, 2.0, 4.0, 3.0, 1.5, 5.0, 10.0, -2.0, -3.0]))
    run()
    assert np.array_equal(recent_values(y),
                          np.array([2, 3, 5, 6, 8]))

def test_quenched_time_of_crossing_threshold():
    # Declare streams
    x = StreamArray('x')
    y = StreamArray('y', dtype='int')
    # Declare agent
    quenched_time_of_crossing_threshold(x, y, threshold=2.5, quench_duration=2)
    # Put data in streams and run
    x.extend(np.array([1.0, 2.0, 4.0, 3.0, 1.5, 5.0, 10.0, -2.0, -3.0]))
    run()
    assert np.array_equal(recent_values(y),
                          np.array([2, 5, 8]))
    

if __name__ == '__main__':
    test_evaluate_polynomial()
    test_magnitude_of_vector()
    test_subtract_mean()
    #test_subtract_mean_block()
    test_time_of_crossing_threshold()
    test_quenched_time_of_crossing_threshold()
    
     
    
        
        
        
