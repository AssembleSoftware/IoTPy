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
from op import map_element, map_window
from merge import zip_stream, blend, zip_map
from source import source_func_to_stream, source_function, source_list
from source import SourceList, source_list_to_stream
from sink import stream_to_file
from timing import offsets_from_ntp_server
from print_stream import print_stream
from helper_control import _stop_, _close
from recent_values import recent_values

def example_1():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    
    def compute_0(in_streams, out_streams):
        map_element(
            func=lambda x: x,
            in_stream=in_streams[0], out_stream=out_streams[0])

    proc_0 = shared_memory_process(
        compute_func=compute_0,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[('in', source)],
        name='process_0')

    def compute_1(in_streams, out_streams):
        stream_to_file(in_stream=in_streams[0], filename='result_1.dat')

    proc_1 = shared_memory_process(
        compute_func=compute_1,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[],
        name='process_1'
        )

    mp = Multiprocess(
        processes=[proc_0, proc_1],
        connections=[(proc_0, 'out', proc_1, 'in')])
    mp.run()


def example_2():
    # Specify the process, proc_0
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    
    def compute_0(in_streams, out_streams):
        map_element(
            func=lambda x: x,
            in_stream=in_streams[0], out_stream=out_streams[0])

    proc_0 = shared_memory_process(
        compute_func=compute_0,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[('in', source)],
        name='process_0')

    # Specify the process, proc_1
    def compute_1(in_streams, out_streams):
        map_element(
            func=lambda x: 10*x,
            in_stream=in_streams[0],
            out_stream=out_streams[0])

    proc_1 = shared_memory_process(
        compute_func=compute_1,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='process_1'
        )

    # Specify the process, proc_2
    def compute_2(in_streams, out_streams):
        map_element(
            func=lambda x: 1000*x,
            in_stream=in_streams[0],
            out_stream=out_streams[0])

    proc_2 = shared_memory_process(
        compute_func=compute_2,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='process_2'
        )

    # Specify the process, proc_3
    def compute_3(in_streams, out_streams):
        t = Stream()
        zip_stream(in_streams, t)
        stream_to_file(t, 'result_2.dat')

    proc_3 = shared_memory_process(
        compute_func=compute_3,
        in_stream_names=['in_1', 'in_2'],
        out_stream_names=[],
        connect_sources=[],
        name='process_3'
        )

    # Specify the multiprocess application.
    vm = Multiprocess(
        processes=[proc_0, proc_1, proc_2, proc_3],
        connections=[(proc_0, 'out', proc_1, 'in'),
                     (proc_0, 'out', proc_2, 'in'),
                     (proc_1, 'out', proc_3, 'in_1'),
                     (proc_2, 'out', proc_3, 'in_2')])
    vm.run()


if __name__ == '__main__':
    print 'Starting example_1'
    example_1()
    print 'Finished example_1'
    print
    print 'Starting example_2'
    example_2()
    print 'Finished example_2'
