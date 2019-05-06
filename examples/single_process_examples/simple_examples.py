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


def single_process_single_source_map_element_example_1():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(
            in_list=source_list, out_stream=out_stream)
    def compute_func(in_streams, out_streams):
        def f(x): return x*10
        check_list = map(f, source_list)
        t = Stream()
        map_element(
            func=f, in_stream=in_streams[0], out_stream=t)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='single_process_single_source_map_element_example_1.dat')
    make_and_run_process(compute_func)

def single_process_single_source_map_element_example_3():
    class example(object):
        def __init__(self, multiplicand):
            self.multiplicand = multiplicand
            self.running_sum = 0
        def step(self, v):
            result = v * self.multiplicand + self.running_sum
            self.running_sum += v
            return result

    def compute_func(in_streams, out_streams):
        eg = example(multiplicand=2)
        check_list = [0, 2, 5, 9, 14, 20, 27, 35, 44, 54]
        t = Stream()
        map_element(
            func=eg.step, in_stream=in_streams[0], out_stream=t)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='single_process_single_source_map_element_example_3.dat')
    make_and_run_process(compute_func)

def single_process_single_source_filter_element_example_1():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    def compute_func(in_streams, out_streams):
        def f(x): return x < 5
        check_list = filter(f, source_list)
        t = Stream()
        filter_element(
            func=f, in_stream=in_streams[0], out_stream=t)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='single_process_single_source_filter_example_1.dat')
    make_and_run_process(compute_func)

def single_process_single_source_map_list_example_1():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    def compute_func(in_streams, out_streams):
        def f(lst):
            return [v*2 if v%2 else v/2 for v in lst]
        check_list = f(source_list)
        t = Stream()
        map_list(
            func=f, in_stream=in_streams[0], out_stream=t)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='single_process_single_source_map_list_example_2.dat')
    make_and_run_process(compute_func)

def single_process_single_source_map_list_example_2():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    def compute_func(in_streams, out_streams):
        def h(v): return 10*v
        def f(lst):
            return map(h, lst)
        check_list = f(source_list)
        t = Stream()
        map_list(
            func=f, in_stream=in_streams[0], out_stream=t)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='single_process_single_source_map_list_example_2.dat')
    make_and_run_process(compute_func)

def single_process_single_source_map_list_example_3():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    def compute_func(in_streams, out_streams):
        def h(v): return v < 5
        def f(lst):
            return filter(h, lst)
        check_list = f(source_list)
        t = Stream()
        map_list(
            func=f, in_stream=in_streams[0], out_stream=t)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='single_process_single_source_map_list_example_3.dat')
    make_and_run_process(compute_func)

def single_process_single_source_map_list_example_4():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    def compute_func(in_streams, out_streams):
        def f(lst):
            return lst + lst
        check_list = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6,
                      7, 7, 8, 8, 9, 9]
        t = Stream()
        map_list(
            func=f, in_stream=in_streams[0], out_stream=t)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='single_process_single_source_map_list_example_4.dat')
    make_and_run_process(compute_func)

def single_process_single_source_map_window_example_1():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    def compute_func(in_streams, out_streams):
        check_list = [1, 5, 9, 13, 17]
        t = Stream()
        map_window(
            func=sum, in_stream=in_streams[0], out_stream=t,
            window_size=2, step_size=2)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='single_process_single_source_map_window_example_1.dat')
    make_and_run_process(compute_func)

if __name__ == '__main__':
    print 'starting single_process_single_source_map_element_example_1'
    single_process_single_source_map_element_example_1()
    print 'finished single_process_single_source_map_element_example_1'
    print
    print 'starting single_process_single_source_map_element_example_3'
    single_process_single_source_map_element_example_3()
    print 'finished single_process_single_source_map_element_example_3'
    print
    print 'starting single_process_single_source_filter_element_example_1'
    single_process_single_source_filter_element_example_1()
    print 'finished single_process_single_source_filter_element_example_1'
    print
    print 'starting single_process_single_source_filter_element_example_1'
    single_process_single_source_filter_element_example_1()
    print 'finished single_process_single_source_filter_element_example_1'
    print
    print 'starting single_process_single_source_map_list_example_2'
    single_process_single_source_map_list_example_2()
    print 'finished single_process_single_source_map_list_example_2'
    print    
    print 'starting single_process_single_source_map_list_example_3'
    single_process_single_source_map_list_example_3()
    print 'finished single_process_single_source_map_list_example_3'
    print    
    print 'starting single_process_single_source_map_list_example_4'
    single_process_single_source_map_list_example_4()
    print 'finished single_process_single_source_map_list_example_4'
    print    
    print 'starting single_process_single_source_map_window_example_1'
    single_process_single_source_map_window_example_1()
    print 'finished single_process_single_source_map_window_example_1'
    print    


    
    
    
