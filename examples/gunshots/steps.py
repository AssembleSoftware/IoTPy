
"""
Creates a multiprocess, multithread application to detect explosive
sounds such as gunshots.

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
from multicore import make_process, run_multiprocess
# stream is in core
from stream import Stream
# op, merge, source, sink are in agent_types
from op import map_element, map_window
from merge import zip_stream, blend, zip_map, merge_window
from source import source_function, source_file
from sink import stream_to_file
from print_stream import print_stream

# Sensor data in horizontal (e, n) and vertical (z)
# directions for 3 sensors.
sensors_e_n_z = [
    ['Sensor1.e.txt', 'Sensor1.n.txt', 'Sensor1.z.txt'],
    ['Sensor2.e.txt', 'Sensor2.n.txt', 'Sensor2.z.txt'],
    ['Sensor3.e.txt', 'Sensor3.n.txt', 'Sensor3.z.txt']
    ]


class source(object):
    """
    source.source_func() returns an agent that puts data from a file
    called self.filename into the specified out_stream.
    """
    def __init__(self, filename, time_interval=0.0, num_steps=0):
        """
        Parameters
        ----------
        filename: str
          name of a file that contains floating point numbers, one
          number per line.
        time_interval: int or float, optional
          The time elapsed between successive numbers, from the file,
          that are placed on the output stream.
        num_steps: int, optional
          The number of elements from the file placed on the output
          stream. If this is omitted or is 0 then the entire file
          is placed on the output stream.

        """
        self.filename=filename
        self.time_interval=time_interval
        self.num_steps=num_steps
    def source_func(self, out_stream):
        return source_file(
            lambda v: float(v), out_stream,
            self.filename, self.time_interval,
            self.num_steps)

def compute(in_streams, out_streams):
    """
    Parameters
    ----------
    in_streams: list of Stream
    out_streams: list of Stream

    Creates a network of agents with input streams, in_streams and
    output streams, out_streams.
    instreams has a stream for each direction (e.g. East, North,
    vertical) of a sensor.
    out_streams is a singleton list, and out_streams[0] is the output
    stream of this nework

        """
    # SPECIFY CONSTANTS
    THRESHOLD = 0.01

    # Define functions that are wrapped to create agents. 
    def subtract_mean(window):
        return window[-1] - sum(window)/float(len(window))
    def magnitude_of_vector(coordinates):
        return math.sqrt(sum([v*v for v in coordinates]))
    def simple_anomaly(value):
        if value > THRESHOLD:
        return 1.0 if value > THRESHOLD else 0.0

    # Define the internal and output streams
    zero_mean_streams = [Stream() for i in range(len(in_streams))]
    magnitude_stream = Stream('magnitude')
    anomaly_stream = Stream('anomaly_stream')
    out_streams[0] = anomaly_stream

    # Create agents
    for i in range(len(in_streams)):
        map_window(
            func=subtract_mean, 
            in_stream=in_streams[i], 
            out_stream=zero_mean_streams[i],
            window_size=500, step_size=1,
            initial_value=0.0)
    zip_map(
        func=magnitude_of_vector,
        in_streams=zero_mean_streams,
        out_stream=magnitude_stream
        )
    map_element(
        func=simple_anomaly,
        in_stream=magnitude_stream,
        out_stream=anomaly_stream
        )
    
def detect_regional_anomalies(in_streams, out_streams):
    """
    Parameters
    ----------
    in_streams: list of Stream
    out_streams: list of Stream

    Creates a network of agents with input streams, in_streams and
    output streams, out_streams.
    instreams has a stream from each sensor.
    out_streams is empty because this network has no output stream.

    This network detects regional anomalies by aggregating local
    anomalies. 

    """
    THRESHOLD = 1
    # Define functions that are wrapped to create agents. 
    def f(windows):
        number_local_anomalies = [
            any(window) for window in windows].count(True)
        return 1.0 if number_local_anomalies > THRESHOLD else 0.0

    # Define the internal and output streams.
    # This network has no output stream.
    regional_anomalies = Stream('Regional anomalies')

    # # Create agents
    merge_window(
        func=f, in_streams=in_streams, out_stream=regional_anomalies,
        window_size=2000, step_size=1, initial_value=0.0)
    for i in range(len(in_streams)):
        stream_to_file(in_streams[i], 'Anomalies_'+str(i+1)+'_.txt')
    stream_to_file(regional_anomalies, 'regional_anomalies.txt')


# DEFINE PROCESSES
processes = []
NUM_STEPS=100000
TIME_INTERVAL=0.0005
for sensor_e_n_z in sensors_e_n_z:
    # sensor_e_n_z is a list of 3 files of accelerations in the
    # directions east, north, vertical.
    # sensor_sources will be a list of source_func for data obtained
    # from the 3 files: east, north, vertical
    sensor_sources = []
    for direction in sensor_e_n_z:
        # direction is a file which contains sensor data from either
        # east or north or vertical directions.
        source_object = source(direction, TIME_INTERVAL, NUM_STEPS)
        sensor_sources.append(source_object.source_func)
    # Make a process for this sensor, and append it to the list of
    # processes.
    # The sources for this process are in the list sensor_sources.
    # The process has no input streams from other processes and so
    # in_stream_names is empty.
    # It has a single output stream called anomaly_stream.
    # The computational network is defined by the function compute.
    proc = make_process(
        list_source_func=sensor_sources, compute_func=compute,
        in_stream_names=[], out_stream_names=['anomaly_stream'])
    processes.append(proc)

# Make a process for the aggregation sensor.
# This process has no sources.
# It gets anomaly streams from each of the three sensor processes.
# We call the anomaly stream from sensor j, "anomaly_j", for j =1,2,3
# We could use any name.
proc = make_process(
    list_source_func=[], compute_func=detect_regional_anomalies,
    in_stream_names=['anomaly_0', 'anomaly_1', 'anomaly_2'],
    out_stream_names=[])
processes.append(proc)

# RUN MULTIPROCESS APPLICATION
# Create and run a multiprocess application with the four
# processes[0,1,2,3]
# The output stream called 'anomaly_stream' of processes[0] is
# connected to the input stream called 'anomaly_0' of processes[3]
# which is the same as processes[-1].
# Likewise, the output stream of processes[1], called 'anomaly_stream'
# is connected to the input stream called 'anomaly_1' of processes[3].
# Similarly for processes[2].
run_multiprocess(
    processes=processes,
    connections=[
        (processes[0], 'anomaly_stream', processes[-1], 'anomaly_0'),
        (processes[1], 'anomaly_stream', processes[-1], 'anomaly_1'),
        (processes[2], 'anomaly_stream', processes[-1], 'anomaly_2')
        ])                

