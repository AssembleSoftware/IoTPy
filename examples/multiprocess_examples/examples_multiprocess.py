import random
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
from multi import multi_element
from merge import zip_stream
# recent_values, basics are in ../../IoTPy/helper_functions
from recent_values import recent_values
from basics import r_mul, map_e, merge_e, multi_e, print_stream
# multicore is in ../../IoTPy/multiprocessing
from multicore import shared_memory_process, Multiprocess

@map_e
def identity(v): return v

@merge_e
def total(v): return sum(v)

@merge_e
def maximize(v):
    ## print 'maximize. v is ', v
    return max(v)

@merge_e
def minimize(v):
    ## print 'minimize. v is ', v
    return min(v)


@multi_e
def max_min(any_list): return max(any_list), min(any_list)


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
# Example with four processes.
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
        r_mul(in_streams[0], out_streams[0], arg=10)

    proc_1 = shared_memory_process(
        compute_func=compute_1,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='process_1'
        )

    # Specify the process, proc_2
    def compute_2(in_streams, out_streams):
        r_mul(in_streams[0], out_streams[0], arg=1000)

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


#------------------------------------------------------------
# Example with four processes.
# Process 3 has an actuator.
def example_3():

    def q2f(q):
        queue_to_file(q, filename='result.dat', timeout=1.0)

    def source(s):
        return source_list_to_stream(range(10), s)
    
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
        r_mul(in_streams[0], out_streams[0], arg=20)

    proc_1 = shared_memory_process(
        compute_func=compute_1,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='process_1'
        )

    # Specify the process, proc_2
    def compute_2(in_streams, out_streams):
        r_mul(in_streams[0], out_streams[0], arg=1000)

    proc_2 = shared_memory_process(
        compute_func=compute_2,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='process_2'
        )

    # Specify the process, proc_3
    def compute_3(in_streams, out_streams):
        total(in_streams, out_streams[0])

    proc_3 = shared_memory_process(
        compute_func=compute_3,
        in_stream_names=['in_1', 'in_2'],
        out_stream_names=['out'],
        connect_sources=[],
        connect_actuators=[('out', q2f)],
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


def example_4():

    def q2f(q):
        queue_to_file(q, filename='result_max.dat', timeout=1.0)

    def q2f2(q):
        queue_to_file(q, filename='result_min.dat', timeout=1.0)

    def source(s):
        return source_func_to_stream(
            func=random.random, out_stream=s, num_steps=10)

    proc_0 = shared_memory_process(
        compute_func=max_min,
        in_stream_names=['in_0_0', 'in_0_1'],
        out_stream_names=['out_0_0', 'out_0_1'],
        connect_sources=[('in_0_0', source), ('in_0_1', source)],
        name='process_0')

    proc_1 = shared_memory_process(
        compute_func=max_min,
        in_stream_names=['in_1_0', 'in_1_1'],
        out_stream_names=['out_1_0', 'out_1_1'],
        connect_sources=[],
        connect_actuators=[('out_1_0', q2f), ('out_1_1', q2f2)],
        name='process_1'
        )

    # Specify the multiprocess application.
    vm = Multiprocess(
        processes=[proc_0, proc_1],
        connections=[(proc_0, 'out_0_0', proc_1, 'in_1_0'),
                     (proc_0, 'out_0_1', proc_1, 'in_1_1')])
    vm.run()

def example_5():

    def q2f(q):
        queue_to_file(q, filename='result_max.dat', timeout=1.0)

    def q2f2(q):
        queue_to_file(q, filename='result_min.dat', timeout=1.0)

    def source(s):
        return source_func_to_stream(
            func=random.random, out_stream=s, num_steps=10)

    num_procs=4
    num_in = 5
    procs = []
    in_stream_names=['in_'+str(j) for j in range(num_in)]
    out_stream_names=['max_values', 'min_values']
    for i in range(num_procs):
        proc = shared_memory_process(
            max_min, in_stream_names, out_stream_names,
            connect_sources=[(in_stream_name, source) for
                             in_stream_name in in_stream_names],
            name='process'+str(i))
        procs.append(proc)

    aggregator = shared_memory_process(
        compute_func=max_min,
        in_stream_names=['max_val', 'min_val'],
        out_stream_names=['max_max', 'min_min'],
        connect_sources=[],
        connect_actuators=[('max_max', q2f), ('min_min', q2f2)],
        name='aggregator'
        )

    # Specify the multiprocess application.
    vm = Multiprocess(
        processes=procs+[aggregator],
        connections=[
            (proc, 'max_values', aggregator, 'max_val') for proc in procs] + [
            (proc, 'min_values', aggregator, 'min_val') for proc in procs])
    vm.run()



if __name__ == '__main__':
    print ('Starting example_1')
    example_1()
    print ('Finished example_1')
    print
    print ('Starting example_2')
    example_2()
    print ('Finished example_2')
    print
    print ('Starting example_3')
    example_3()
    print ('Finished example_3')
    print
    print ('Starting example_4')
    example_4()
    print ('Finished example_4')
    print
    print ('Starting example_5')
    example_5()
    print ('Finished example_5')
