
import sys
import os

sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../timing"))


# multicore is in multiprocessing
from multicore import StreamProcess, single_process_single_source
from multicore import single_process_multiple_sources
# stream is in core
from stream import Stream
# op, merge, source, sink are in agent_types
from op import map_element, map_window
from merge import zip_stream, blend
from source import source_function, source_file
from sink import stream_to_file
# timing is in examples.
from timing import offsets_from_ntp_server

def source(out_stream):
    return source_file(
        func=lambda x: float(x), out_stream=out_stream,
        filename='Sensor1.z.txt',
        time_interval=0.01, num_steps=1500)
        

def compute(in_stream):
    def subtract_mean(window):
        return window[-1] - sum(window)/float(len(window))

    zero_mean_stream = Stream('zero mean')
    input_stream = Stream('input')

    map_window(
        func=subtract_mean, 
        in_stream=in_stream, 
        out_stream=zero_mean_stream,
        window_size=50, step_size=1)
    map_window(
        func=lambda window: window[-1],
        in_stream=in_stream, 
        out_stream=input_stream,
        window_size=50, step_size=1)
    stream_to_file(
        in_stream=zero_mean_stream,
        filename='zero_mean_z.txt')

if __name__ == '__main__':
    single_process_single_source(
        source_func=source, compute_func=compute)
