import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# stream is in ../../IoTPy/core
from stream import Stream
# source, sink, op, merge are in ../../IoTPy/agent_types
from source import SourceList, source_list_to_stream, source_func_to_stream
from sink import stream_to_file, print_from_queue, queue_to_file
from op import map_element
from merge import zip_stream
# recent_values, basics are in ../../IoTPy/helper_functions
from recent_values import recent_values
from basics import multiply, map_e, merge_e, multi_e
# multicore is in ../../IoTPy/multiprocessing
from multicore import shared_memory_process, Multiprocess

@map_e
def identity(v): return v

@map_e
def multiply(v, operand): return v * operand

#------------------------------------------------------------
# Example with two processes.
# Neither process has actuators.
def example_1():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    
    def compute_0(in_streams, out_streams):
        identity(in_streams[0], out_stream=out_streams[0])

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

#------------------------------------------------------------
# Example with three processes.
# No process has actuators.
def example_2():
    def source(out_stream):
        return source_list_to_stream(range(10), out_stream)
    
    def compute_0(in_streams, out_streams):
        identity(in_streams[0], out_stream=out_streams[0])

    proc_0 = shared_memory_process(
        compute_func=compute_0,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[('in', source)],
        name='process_0')

    # Specify the process, proc_1
    def compute_1(in_streams, out_streams):
        multiply(in_streams[0], out_streams[0], operand=10)

    proc_1 = shared_memory_process(
        compute_func=compute_1,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='process_1'
        )

    # Specify the process, proc_2
    def compute_2(in_streams, out_streams):
        multiply(in_streams[0], out_streams[0], operand=1000)

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
