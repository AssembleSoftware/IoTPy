import sys
import os
import threading
import random
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../timing"))

from multicore import multithread
from stream import Stream
from source import SourceList, source_list_to_stream, source_func_to_stream
from sink import stream_to_file, print_from_queue, queue_to_file
from print_stream import print_stream
from basics import multiply, map_e, merge_e, multi_e

#-------------------------------------------------------------------
# Example with one source and no actuators.
def multithread_example_1():
    # Step 1: Sources
    def source(s):
        # returns a thread that puts elements of range(10) into
        # stream s at intervals of 0.05 seconds
        return source_list_to_stream(range(10), s, time_interval=0.05)

    # Step 2:Actuators
    # This example has no actuators

    # Step 3: The computation thread.
    def compute_func(in_streams, out_streams):
        print_stream(multiply(in_streams[0], multiplicand=2))

    # Step 4: Call multithread
    multithread([source], [], compute_func)

#-------------------------------------------------------------------
# Example with one source and one actuator.
def multithread_example_2():
    @map_e
    def double(v): return v*2

    # Step 1: Sources
    def source(s):
        return source_list_to_stream(range(5), s)

    # Step 2:Actuators
    # The actuator is print_from_queue imported from sink

    # Step 3: The computation thread.
    def compute_func(in_streams, out_streams):
        double(in_streams[0], out_streams[0])

    # Step 4: Call multithread
    multithread([source], [print_from_queue], compute_func)

#-------------------------------------------------------------------
# Example with two sources and one actuator.
def multithread_example_3():
    @merge_e
    def f(v): return 2*v[0] + 3*v[1]

    # Step 1: Sources
    def source_0(s):
        return source_list_to_stream(range(5), s)
    
    def source_1(s):
        return source_list_to_stream(range(10, 20), s)

    # Step 2:Actuators
    # The actuator is print_from_queue imported from sink

    # Step 3: The computation thread.
    def compute_func(in_streams, out_streams):
        f(in_streams, out_streams[0])

    # Step 4: Call multithread
    multithread([source_0, source_1], [print_from_queue], compute_func)

#-------------------------------------------------------------------
# Example with arbitrarily many sources and two actuators.
def multithread_example_4():
    @multi_e
    def f(list_x):
        return max(list_x), min(list_x)

    # Step 1: Sources
    def source(s):
        return source_func_to_stream(
            func=random.random, out_stream=s,
            time_interval=0.01, num_steps=10)

    # Step 2:Actuators
    # One actuator is print_from_queue imported from sink
    # The other actuator is q2f
    def q2f(q):
        queue_to_file(q, filename='test.txt', timeout=1.0)

    # Step 3: The computation thread.
    def compute_func(in_streams, out_streams):
        f(in_streams, out_streams)

    # Step 4: Call multithread
    in_streams = [source for _ in range(4)]
    multithread(in_streams, [print_from_queue, q2f], compute_func)


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
    ## multithread_example_1()
    ## multithread_example_2()
    ## multithread_example_3()
    multithread_example_4()
    ## print 'Starting example_1'
    ## example_1()
    ## print 'Finished example_1'
    ## print
    ## print 'Starting example_2'
    ## example_2()
    ## print 'Finished example_2'
