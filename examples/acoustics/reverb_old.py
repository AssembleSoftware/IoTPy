import sys
import os
import threading
import random
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../timing"))

from multicore import SharedMemoryProcess
from multicore import shared_memory_process, Multiprocess
from multicore import single_process_single_source
from multicore import single_process_multiple_sources
from stream import Stream
from op import map_element, map_window, filter_element, map_list
from merge import zip_stream, blend, zip_map
from source import source_func_to_stream, source_function, source_list
from source import SourceList, source_list_to_stream
from sink import stream_to_file, sink_element
from timing import offsets_from_ntp_server
from print_stream import print_stream
from helper_control import _stop_, _close
from recent_values import recent_values
from copy import deepcopy


source_list = range(10)
def source(out_stream):
    return source_list_to_stream(source_list, out_stream)

def check_correctness_of_output(in_stream, check_list):
    def check(v, index, check_list):
        # v is in_list[index]
        assert v == check_list[index]
        next_index = index + 1
        return next_index
    sink_element(func=check, in_stream=in_stream, state=0,
                 check_list=check_list)
    
def make_and_run_process(compute_func):
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc')
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()



def reverb( alpha=0.5, delay=10):



    def compute_func(in_streams, out_streams):
        ## F1 - Amplitude Adjustment

        def delay_and_attenuate(in_streams):
            tmp = deepcopy(in_streams)
            for i in range(len(tmp)):
                tmp[i]*=alpha
            
            #print("Length of tmp==tmp1 --",len(tmp)==len(tmp1))

            return tmp



        t = Stream(initial_value = [0]*delay)
        w = Stream()
        map_list(
            func=delay_and_attenuate, in_stream = in_streams[0], out_stream = t)
        zip_map(sum, [t, in_streams[0]], w)
        stream_to_file(
            in_stream=w,
            filename = 'Reverb.dat')
    make_and_run_process(compute_func)


if __name__ == '__main__':
    
    print('Running the reverberation test ... ')
    reverb(alpha=0.2,delay=4)
    print('reverb done')
