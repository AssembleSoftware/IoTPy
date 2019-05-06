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

def detect_anomaly_1(v, threshold):
    if v > threshold:
        return 1.0
    else:
        return 0.0
    
def detect_anomaly(window, short_window_size, threshold, cutoff):
    current_average = statistics.mean(window[-short_window_size:])
    clipped_window = [v for v in window if v < cutoff]
    long_term_average = statistics.mean(clipped_window)
    print current_average, long_term_average
    anomaly = current_average > long_term_average * threshold
    return anomaly

if __name__ == '__main__':
    import random
    
    input_sequence = [random.random() for _ in range(100)]
    input_sequence.extend([10 + random.random() for _ in range(5)])
    input_sequence.extend([random.random() for _ in range(100)])

    # Create streams
    s = Stream('s')
    t = Stream('t')

    map_window(
        func=detect_anomaly, in_stream=s, out_stream=t,
        window_size=50, step_size=1, short_window_size=5,
        threshold=3, cutoff=0.9)
    print_stream(t)
    s.extend(input_sequence)

    # Execute a step of the scheduler
    Stream.scheduler.step()

