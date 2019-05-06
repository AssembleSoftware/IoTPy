import json
import statistics

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
from recent_values import recent_values
from sink import stream_to_file

def short_term_long_term_anomaly(
        window, short_term_duration, threshold, cutoff):
    """
    Parameters
    ----------
    window: list or array
    short_term_duration: int
        must be less or equal to len(window)
    cutoff: int or float
        long-term behavior consists of only those elements
        which are less than cutoff * average over the window.
    threshold: int or float

    Returns
    -------
    anomaly_signal: float
        0.0 indicating no anomaly or
        1.0 indicating anomaly.

    Notes
    -----
    anomaly occurs when average of clipped window is significantly
    lower (determined by threshold) than the average of the most
    recent short_term_duration elements.

    """
    # Compute recent_average from the latest short_term_duration
    # elements of window. 
    recent_average = statistics.mean(window[-short_term_duration:])
    # clipped_window strips out extreme readings.
    clipped_window = [v for v in window if
                      abs(v) < cutoff * abs(statistics.mean(window))]
    # If too many values in window have been stripped off then replace
    # them. 
    if len(clipped_window) < len(window)/2.0:
        clipped_window = window
    long_term_average = statistics.mean(clipped_window)
    anomaly = recent_average > long_term_average * threshold
    anomaly_signal = 1.0 if anomaly else 0.0
    return anomaly_signal

def anomaly_stream(in_stream, out_stream, long_term_duration,
                   short_term_duration, threshold, cutoff):
    """
    Parameters
    ----------
    in_stream: Stream
      input stream of function
    out_stream: Stream
      output stream of function
    long_term_duration: int
    short_term_duration: int
    cutoff: int or float
    threshold: int or float

    Note
    ----
    out_stream is a stream of anomalies determined by the function
    detect_anomaly().

    An anomaly occurs when average of the clipped window is
    significantly lower (determined by threshold) than the average of
    the most recent short_term_duration elements in the window.
    
    """
    map_window(
        func=short_term_long_term_anomaly,
        in_stream=in_stream, out_stream=out_stream, 
        window_size=long_term_duration, step_size=1,
        short_term_duration=short_term_duration, 
        threshold=threshold, cutoff=cutoff)

    
