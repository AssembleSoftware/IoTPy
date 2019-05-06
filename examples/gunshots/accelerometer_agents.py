
"""
Creates a multiprocess, multithread application to detect high
readings.

See https://www.assemblesoftware.com/examples/

"""

import sys
import os
import math
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# op, merge, source, sink are in agent_types
from op import map_element, map_window
from merge import zip_map, merge_window
from agent import Agent
from check_agent_parameter_types import *
from helper_control import _no_value
from timed_agent import timed_window, timed_zip_agent
from sink import stream_to_file

#----------------------------------------------------
# Agent that subtracts the mean in a stream
#----------------------------------------------------    
def subtract_mean(in_stream, out_stream, window_size):
    """
    Parameters
    ----------
    in_stream: Stream
       Stream of floats.
    out_stream: Stream
       Stream of floats
       The out_stream is the in_stream with the mean subtracted.
       So, the mean of the out_stream will be approximately 0.0.
    window_size: int
       positive value
       The size of the window on which the mean is calculated.
       The larger the window_size the more accurate is the subtraction
       of the mean, but also the slower the computation.

    """
    # Define a terminating function
    def f(window):
        """
        Parameters
        ----------
        window: list
           list of elements of a stream.

        Returns
        -------
           float
           The last element of the window with the mean
           of the window subtracted.

        """
        return window[-1] - sum(window)/float(len(window))

    # Wrap function to create an agent.
    map_window(
        f, in_stream, out_stream, window_size,
        step_size=1,initial_value=0.0)


#----------------------------------------------------
# Agent that computes the magnitude of a vector
#----------------------------------------------------   
def magnitude_of_vector(in_streams, out_stream):
    """
    Parameters
    ----------
     in_streams: list of Stream
       Each component stream in the list is a stream of floats.
       The component streams are the streams of values in the
       x, y, z directions
    out_stream: Stream
       Stream of floats
       The out_stream is the stream of magnitudes of the values.

    """
    # Define a terminating function
    def g(coordinates):
        """
        Parameters
        ----------
        coordinates: list
           list of values of a vector in x, y, z directions.

        Returns
        -------
           float
           The magnitude of the vector

        """
        return math.sqrt(sum([v*v for v in coordinates]))
    # Wrap the terminating function to create an agent
    zip_map(g,in_streams,out_stream)

#----------------------------------------------------
# Agent that computes local anomalies
#----------------------------------------------------
def simple_anomalies(in_stream, out_stream, threshold):
    """
    Parameters
    ----------
     in_stream: Stream
       Stream of floats
    out_stream: Stream
       Stream of floats
       The elements of out_stream are either 0.0 or 1.0
       1.0 if an anomaly is detected
       0.0 otherwise.

    """
    # Define a terminating function
    def simple_anomaly(value, index):
        signal = (index, abs(value)) if abs(value) > threshold else _no_value
        index += 1
        return (signal, index)
    # Wrap the terminating function to create an agent
    map_element(simple_anomaly,in_stream, out_stream, state=0)

def quench(in_stream, out_stream, QUENCH_TIME):
    # state is the start time of the most recent quench period.
    # in_stream consists of a sequence of timestamps.
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
    map_element(f, in_stream, out_stream, state=0)


    
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
    def f(timed_element):
        timestamp, value = timed_element
        time_of_high_magnitude, num_high_magnitude = value
        return time_of_high_magnitude
    stream_to_file(
        in_stream=global_anomalies_stream,
        filename='global_anomalies.txt',
        element_function=f)

class aggregate_large_magnitudes(object):
    def __init__(self, num_streams, threshold):
        self.num_streams = num_streams
        self.threshold = threshold
        self.high_magnitude_streams = [False for _ in range(num_streams)]
        self.latest_output_timestamp = -1
    def func(self, window):
        # window is a list of lists
        first_element = window[0]
        first_timestamp = first_element[0]
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



    
        
        
        
