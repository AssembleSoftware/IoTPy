
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
from run import run
from recent_values import recent_values
from basics import map_w, map_e, merge_e

#----------------------------------------------------
# Agent that subtracts the mean in a stream
#----------------------------------------------------
@map_w
def subtract_mean(window):
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
    Note
    ----
    The annotated function has the following parameters.
    Parameters
    ----------
    in_stream: Stream of floats.
    out_stream: Stream of floats
       The out_stream is the in_stream with the mean subtracted.
       So, the mean of the out_stream will be approximately 0.0.
    window_size: int, positive
       The size of the window on which the mean is calculated.
       The larger the window_size the more accurate is the
       calculation of the mean, but the slower the computation.
    step_size: int, positive
       The amount that the sliding window is moved on each step.

    """
    return window[-1] - sum(window)/float(len(window))

#----------------------------------------------------
# Agent that computes the magnitude of a vector
#----------------------------------------------------
@merge_e 
def magnitude_of_vector(coordinates):
    """
    Parameters
    ----------
     coordinates: a list or array
        The coordinates of the vector

    Note
    ----
    The decorated function has the following parameters:
    
     in_streams: list of Stream
       Each component stream in the list is a stream of floats.
       in_streams[0], in_streams[1], in_streams[2]  are the
       streams of coordinates in the x, y, z directions.
       So, in_streams[0][j], in_streams[1][j], in_streams[2][j]
       are the coordinates of the j-th sample.
    out_stream: Stream
       Stream of floats
       out_stream[j] is the magnitude of the vector with coordinates
       in_streams[0][j], in_streams[1][j], in_streams[2][j]
    
    """
    return math.sqrt(sum([v*v for v in coordinates]))


#----------------------------------------------------
# Agent that computes local anomalies
#----------------------------------------------------

def simple_anomalies(in_stream, out_stream, MAGNITUDE_THRESHOLD):
    """
    Parameters
    ----------
    in_stream: stream of floats
       stream of magnitudes
    out_stream: stream of pairs (magnitude, timestamp)
    MAGNITUDE_THRESHOLD: float or int

    Note
    ----
    out_stream contains the timestamps at which in_stream values
    exceeded MAGNITUDE_THRESHOLD.

    """
    @map_e
    def f(value, state, THRESHOLD):
        """
        Parameters
        ----------
        value: float
          An element of an input stream
        state: int
          state = n on the n-th call to f, where n=0, 1, 2, ...
        
        """
        signal = (state, abs(value)) if abs(value) > THRESHOLD else _no_value
        state += 1
        return (signal, state)

    f(in_stream, out_stream, THRESHOLD=MAGNITUDE_THRESHOLD, state=0)


def quench(in_stream, out_stream, QUENCH_TIME):
    """
    Parameters
    ----------
    in_stream: stream of pairs (timestamp, value)
       where value is a magnitude
    out_stream: stream of pairs (timestamp, value)
       where value is a magnitude
    QUENCH_TIME: int, positive (constant)

    """
    @map_e
    def f(timestamped_value, state):
        """
        Parameters
        ----------
        timestamped_value: (timestamp, value)
           where value is a float
        state: int
           state is the time at which the last quench
           period began.
           Initially set state to -QUENCH_TIME
           so that there are no quenches until the
           timestamp exceeds 0.

        """
        timestamp, value = timestamped_value
        if timestamp - state < QUENCH_TIME:
            # The current quench period goes up to:
            # QUENCH_TIME + time at which quench began.
            # This input arrived during the quench period
            # So, this input is discarded, and the state
            # doesn't change.
            # _no_value indicates that nothing is placed
            # in the output.
            return _no_value, state
        else:
            # This input arrived outside a quench period.
            # Start a new quench period.
            state = timestamp
            # This input is passed through because it
            # arrived outside a quench period.
            return timestamped_value, state
    # The function annotated with @map_e has a single
    # in_stream, a single out_stream and an initial
    # state.
    f(in_stream, out_stream, state=-QUENCH_TIME)

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
       in_streams where s[j-W: j] contains at least one
       1.0 value where W is timed_window_size.  We treat
       anomalies in different sensor streams as simultaneous
       if they are within W time units of each other.

    """
    aggregator = aggregate_large_magnitudes(
        num_streams=2, THRESHOLD=2)
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
    THRESHOLD: int
       Generates a large magnitude if the number of
       input streams with anomalies equals or exceeds
       THRESHOLD

    Attributes
    ----------
    high_magnitude_streams: list of Boolean
       high_magnitude_streams[j] is True if the j-th
       stream is anomalously high magnitude.
    latest_output_timestamp: timestamp
       The last timestamp output by this agent.

    """
    def __init__(self, num_streams, THRESHOLD):
        self.num_streams = num_streams
        self.THRESHOLD = THRESHOLD
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
            if num_high_magnitude_streams >= self.THRESHOLD:
                new_timestamp = (first_timestamp + timestamp)/2
                self.high_magnitude_streams = [False for _ in range(self.num_streams)]
                if new_timestamp != self.latest_output_timestamp:
                    self.latest_output_timestamp = new_timestamp
                    return (new_timestamp, num_high_magnitude_streams)
            return _no_value


def test():
    x = Stream('x')
    y = Stream('y')
    subtract_mean(x, y, window_size=10, step_size=10)
    x.extend(list(range(100)))
    run()
    print (recent_values(y))

if __name__ == '__main__':
    test()
    
        
        
        
        
