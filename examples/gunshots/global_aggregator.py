
"""
Creates a multiprocess, multithread application to detect high
readings.

See https://www.assemblesoftware.com/examples/

"""

import sys
import os
import math

sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# multicore is in multiprocessing
from multicore import shared_memory_process, Multiprocess
# stream is in core
from stream import Stream
# op, merge, source, sink are in agent_types
from op import map_element, map_window
from merge import zip_map, merge_window
from source import source_float_file
from sink import stream_to_file
# print_stream is in helper functions. Useful for debugging.
from print_stream import print_stream
from accelerometer_agents import subtract_mean, magnitude_of_vector
from accelerometer_agents import simple_anomalies, aggregate_anomalies
from detect_anomaly import anomaly_stream
#from local_anomaly_process import local_anomaly_process
from distributed import distributed_process
from VM import VM

def global_aggregator():
    def compute_func(in_streams, out_streams):
        """
        Parameters
        ----------
        in_streams: list of Stream
          in_streams is a list of anomaly streams with one stream from
          each sensor. An anomaly stream is a sequence of 0.0 and 1.0
          where 0.0 indicates no anomaly and 1.0 indicates an anomaly.
        out_streams: list of Stream
          This list consists of a single stream that contains 0.0
          when no global anomaly across all sensors is detected and 1.0
          when a global anomaly is detected.

        """
        aggregate_anomalies(
            in_streams, out_streams, timed_window_size=2)

    proc = distributed_process(
        compute_func=compute_func,
        in_stream_names=['in_1', 'in_2'],
        out_stream_names=[],
        connect_sources=[],
        name='global aggregator')
    
    vm = VM(
        processes=[proc],
        connections=[],
        subscribers=[(proc, 'in_1', 'S1'),
                     (proc, 'in_2', 'S2')])
    vm.start()


if __name__ == '__main__':
    global_aggregator()
    
