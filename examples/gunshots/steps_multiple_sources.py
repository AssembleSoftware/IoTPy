
import sys
import os
import math

sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
#sys.path.append(os.path.abspath("../timing"))


# multicore is in multiprocessing
from multicore import StreamProcess, single_process_single_source
from multicore import single_process_multiple_sources
# stream is in core
from stream import Stream
# op, merge, source, sink are in agent_types
from op import map_element, map_window
from merge import zip_stream, blend, zip_map
from source import source_function, source_file
from sink import stream_to_file
# timing is in examples.
#from timing import offsets_from_ntp_server

## def source_z(out_stream):
##     return source_file(
##         func=lambda x: float(x), out_stream=out_stream,
##         filename='Sensor1.z.txt',
##         time_interval=0.001, num_steps=1500)
        
## def source_e(out_stream):
##     return source_file(
##         func=lambda x: float(x), out_stream=out_stream,
##         filename='Sensor1.e.txt',
##         time_interval=0.001, num_steps=1500)

## def source_n(out_stream):
##     return source_file(
##         func=lambda x: float(x), out_stream=out_stream,
##         filename='Sensor1.n.txt',
##         time_interval=0.001, num_steps=1500)

sources = range(3)
filenames = ['Sensor1.e.txt', 'Sensor1.n.txt', 'Sensor1.z.txt']
for i in range(3):
    def source(out_stream):
        return source_file(
            func=lambda x: float(x), out_stream=out_stream,
            filename=filenames[i],
            time_interval=0.001
            #num_steps=0
            )
    sources[i] = source
    

def compute(in_streams):
    def subtract_mean(window):
        return window[-1] - sum(window)/float(len(window))
    def magnitude_of_vector(coordinates):
        return math.sqrt(sum([v*v for v in coordinates]))
    def simple_anomaly(value, threshold):
        if value > threshold: return 1.0
        else: return 0.0

    zero_mean_streams = [Stream('zero mean e'),
                         Stream('zero mean n'),
                         Stream('zero mean z')]
    magnitude_stream = Stream('magnitude')
    anomaly_stream = Stream('anomalies')
    filenames = ['zero_mean_e.txt', 'zero_mean_n.txt', 'zero_mean_z.txt']
    for i in range(3):
        map_window(
            func=subtract_mean, 
            in_stream=in_streams[i], 
            out_stream=zero_mean_streams[i],
            window_size=8000, step_size=1)
        zip_map(
            func=magnitude_of_vector,
            in_streams=zero_mean_streams,
            out_stream=magnitude_stream
            )
    map_element(
        func=simple_anomaly,
        in_stream=magnitude_stream,
        out_stream=anomaly_stream,
        threshold=0.1
        )
    stream_to_file(
        in_stream=magnitude_stream,
        filename='magnitude.txt')
    stream_to_file(
        in_stream=anomaly_stream,
        filename='anomaly.txt')

if __name__ == '__main__':
    single_process_multiple_sources(
        list_source_func=sources,
        compute_func=compute)
