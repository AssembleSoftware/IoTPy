
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
from multicore import make_process, run_multiprocess
# stream is in core
from stream import Stream
# op, merge, source, sink are in agent_types
from op import map_element, map_window
from merge import zip_map, merge_window
from source import source_float_file
from sink import stream_to_file
# print_stream is in helper functions. Useful for debugging.
from print_stream import print_stream

# --------------------------------------------------------
# THE FUNCTION f FOR THE SOURCE PROCESS
# --------------------------------------------------------
def f(in_streams, out_streams):
    # DECLARE STREAMS
    zero_means = [
        Stream('zero_means_' + str(i))
        for i in range(len(in_streams))]
    magnitudes = Stream('magnitudes')

    # CREATE AGENTS
    # create subtract_mean agents
    # Define the terminating function
    def subtract_mean(window):
        return window[-1] - sum(window)/float(len(window))
    # Wrap the terminating function to create an agent
    for i in range(len(in_streams)):
        map_window(
            func=subtract_mean, 
            in_stream=in_streams[i], 
            out_stream=zero_means[i],
            window_size=500, step_size=1,
            initial_value=0.0)

    # Create the magnitude agent
    # Define the terminating function
    def magnitude_of_vector(coordinates):
        return math.sqrt(sum([v*v for v in coordinates]))
    # Wrap the terminating function to create an agent
    zip_map(
        func=magnitude_of_vector,
        in_streams=zero_means,
        out_stream=magnitudes
        )

    # Create the local anomaly agent
    # Define the terminating function
    def simple_anomaly(value):
        return 1.0 if value > 1 else 0.0
    # Wrap the terminating function to create an agent
    map_element(
        func=simple_anomaly,
        in_stream=magnitudes,
        out_stream=out_streams[0]
        )
    

# --------------------------------------------------------
# THE FUNCTION g FOR THE AGGREGATION PROCESS
# --------------------------------------------------------    
def g(in_streams, out_streams):
    # DECLARE STREAMS
    regional_anomalies = Stream('Regional anomalies')

    # CREATE AGENTS
    # Create the aggregation agent
    # Define the terminating function
    def aggregate(windows):
        number_local_anomalies = [
            any(window) for window in windows].count(True)
        return 1.0 if number_local_anomalies > 1 else 0.0
    # Wrap the terminating function to create an agent
    merge_window(
        func=aggregate,
        in_streams=in_streams, out_stream=regional_anomalies,
        window_size=250, step_size=1, initial_value=0.0)
    # Agent that copies a stream to a file
    # Plot these files to understand the application.
    for i in range(len(in_streams)):
        stream_to_file(in_streams[i], 'Anomalies_'+str(i+1)+'_.txt')
    stream_to_file(regional_anomalies, 'regional_anomalies.txt')


# DEFINE PROCESSES
local_anomaly_processes = []
NUM_STEPS=10000
TIME_INTERVAL=0.0005

# Sensor data in horizontal (e, n) and vertical (z)
# directions for 3 sensors.
source_files = [
    ['S0515.HNE.txt', 'S0515.HNN.txt', 'S0515.HNZ.txt'],
    ['S0516.HNE.txt', 'S0516.HNN.txt', 'S0516.HNZ.txt'],
    ['S0517.HNE.txt', 'S0517.HNN.txt', 'S0517.HNZ.txt']
    ]

sensors = {'S1':
           {'e': 'S0515.HNE.txt',
            'n': 'S0515.HNN.txt',
            'z': 'S0515.HNZ.txt'
           },
           'S2':
           {'e': 'S0516.HNE.txt',
            'n': 'S0516.HNN.txt',
            'z': 'S0516.HNZ.txt'
           },
           'S3':
           {'e': 'S0517.HNE.txt',
            'n': 'S0517.HNN.txt',
            'z': 'S0517.HNZ.txt'
           }
         }

source_sensor_direction = {}
for sensor_name in sensors.keys():
    source_sensor_direction[sensor_name] = {}
    for direction in ['e', 'n', 'z']:
        source_sensor_direction[sensor_name][direction] = \
          source_float_file(
              filename=sensors[sensor_name][direction],
              time_interval=0.0005,
              num_steps=10000).source_func

source_processes = [
    make_process(
        compute_func=f,
        in_stream_names=['e', 'n', 'z'],
        out_stream_names=['out'],
        connect_sources=[
            (direction,
             source_sensor_direction[sensor_name][direction])
            for direction in ['e', 'n', 'z']])
    for sensor_name in sensors.keys()]

aggregation_process = make_process(
    compute_func=g,
    in_stream_names=[
      'in_'+ str(i) for i in range(len(sensors))],
    out_stream_names=[],
    connect_sources=[])

run_multiprocess(
    processes=source_processes + [aggregation_process],
    connections = [
        (source_processes[i],  'out',
         aggregation_process, 'in_'+str(i))
        for i in range(len(sensors))])
