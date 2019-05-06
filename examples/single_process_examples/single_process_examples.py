"""
This module contains examples of programs consisting of a single
process.

The module has examples of processes with a single source, and
processes with multiple sources.

"""

import sys
import os

sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../timing"))

# multicore is in multiprocessing
from multicore import single_process_single_source
from multicore import single_process_multiple_sources
from multicore import shared_memory_process, Multiprocess
# stream is in core
from stream import Stream
# op, merge, source, sink are in agent_types
from op import map_element, map_window, filter_element
from merge import zip_stream, blend
from source import source_func_to_stream, source_list_to_stream
from sink import stream_to_file, sink_element
# timing is in examples.
from timing import offsets_from_ntp_server


# ----------------------------------------------------------------
#   EXAMPLES: SINGLE PROCESS, SINGLE SOURCE
# ---------------------------------------------------------------- 

def single_process_single_source_example_1():
    """
    The single source generates 1, 2, 3, 4, .....
    The compute function multiplies this sequence by 10
    and puts the result in the file called test.dat
    num_steps is the number of values output by the source.
    For example, if num_steps is 4 and test.dat is empty before the
    function is called then, test.dat will contain 10, 20, 30, 40
    on separate lines.

    The steps to create the process are:
    (1) Define the source: sequence_of_integers(out_stream), where
        out_stream is a stream into which source data is output.
    (2) Define the computational network:
        compute_func(in_streams, out_streams), where
        in_streams and out_streams are lists of streams.
        In this example in_streams is list consisting of
        a single input stream, and out_streams is empty.
    (3) Call proc = shared_memory_process(...) to create a process
        proc.
    Next we make a multiprocess application consisting of the single
    process proc. Since the application has a single process it has
    no connections to other processes.
    (4) Call mp = Multiprocess(processes=[proc], connections=[])
        to make mp, a multiprocess application, and then call
        mp.run() to run the application.
    """

    # STEP 1: DEFINE SOURCES
    def sequence_of_integers(out_stream):
        """
        A simple source which outputs 1, 2, 3,... on
        out_stream.
        """
        def generate_sequence(state): return state+1, state+1

        # Return an agent which takes 10 steps, and
        # sleeps for 0.1 seconds between successive steps, and
        # puts the next element of the sequence in stream s,
        # and starts the sequence with value 0. The elements on
        # out_stream will be 1, 2, 3, ...
        return source_func_to_stream(
            func=generate_sequence, out_stream=out_stream,
            time_interval=0.1, num_steps=4, state=0)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    def compute_func(in_streams, out_streams):
        # A trivial example of a network of agents consisting
        # of two agents where the network has a single input
        # stream: in_stream.
        # The first agent applies function f to each element 
        # of in_stream, and puts the result in its output stream t.
        # The second agent puts values in its input stream t
        # on a file called test.dat.
        # test.dat will contain 10, 20, 30, ....

        def f(x): return x*10
        t = Stream()
        map_element(
            func=f, in_stream=in_streams[0], out_stream=t)
        stream_to_file(in_stream=t, filename='test.dat')

    # STEP 3: CREATE THE PROCESS
    # Create a process with two threads: a source thread and
    # a compute thread. The source thread executes the function
    # sequence_of_integers, and the compute thread executes
    # the function compute_func. The source is connected to
    # the in_stream called 'in' of compute_func.
    # The names of in_streams are arbitrary.
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', sequence_of_integers)],
        connect_actuators=[],
        name='proc')

    # STEP 4: CREATE AND RUN A MULTIPROCESS APPLICATION
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()

# ----------------------------------------------------------------
#   EXAMPLES: SINGLE PROCESS, MULTIPLE SOURCES
# ---------------------------------------------------------------- 

def single_process_multiple_sources_example_1():
    """
    This example has two sources: sequence_of_integers and random_numbers.
    sequence_of_integers generates 1, 2, 3, 4, ... and random_numbers
    generates random numbers. The computation zips the two
    streams together and writes the result to a file called
    output.dat.
    
    num_steps is the number of values produced by the source. For
    example, if the smaller of the num_steps for each source is 10,
    then (1, r1), (2, r2), ..., (10, r10), ... will be appended to the
    file  output.dat where r1,..., r10 are random numbers.
 
    The steps for creating the process are:
    (1) Define the two sources:
            sequence_of_integers(out_stream), random_numbers(out_stream). 
    (2) Define the computational network:
        compute_func(in_streams, out_streams), where
        in_streams and out_streams are lists of streams.
        In this examples, in_streams is list consisting of
        two input streams, and out_streams is empty.
    (3) Call proc = shared_memory_process(...) to create a process
        proc.
    Next we make a multiprocess application consisting of the single
    process proc. Since the application has a single process it has
    no connections to other processes.
    (4) Call mp = Multiprocess(processes=[proc], connections=[])
        to make mp, a multiprocess application, and then call
        mp.run() to run the application.

    """
    import random

    # STEP 1: DEFINE SOURCES
    def sequence_of_integers(out_stream):
        # A simple source which outputs 1, 2, 3, 4, .... on
        # out_stream.
        def generate_sequence(state):
            return state+1, state+1

        # Return an agent which takes 10 steps, and
        # sleeps for 0.1 seconds between successive steps, and
        # puts the next element of the sequence in out_stream,
        # and starts the sequence with value 0. The elements on
        # out_stream will be 1, 2, 3, ...
        return source_func_to_stream(
            func=generate_sequence, out_stream=out_stream,
            time_interval=0.1, num_steps=10, state=0)

    def random_numbers(out_stream):
        # A simple source which outputs random numbers on
        # out_stream.

        # Return an agent which takes 10 steps, and sleeps for 0.1
        # seconds between successive steps, and puts a random number
        # on out_stream at each step.
        return source_func_to_stream(
            func=random.random, out_stream=out_stream,
            time_interval=0.1, num_steps=10)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    def compute_func(in_streams, out_streams):
        # in_streams and out_streams are lists of streams.
        # This is a simple example of a network of agents consisting
        # of two agents where the network has two input streams and no
        # output stream.
        # The first agent zips the two input streams and puts
        # the result on its output stream t which is internal to the
        # network. 
        # The second agent puts values in its input stream t
        # on a file called output.dat.
        from sink import stream_to_file
        # t is an internal stream of the network
        t = Stream()
        zip_stream(in_streams=in_streams, out_stream=t)
        stream_to_file(in_stream=t, filename='output.dat')

    # STEP 3: CREATE THE PROCESS
    # Create a process with three threads:
    # two source threads and a compute thread.
    # The two source threads execute the functions sequence_of_integers
    # and random_numbers
    # The compute thread executes function compute_func.
    # The names of the inputs of compute_func are:
    # 'sequence_of_integers' and 'data'.
    # The source, sequence_of_integers, is connected to the
    # in_stream called 'sequence_of_integers'. The source
    # random_numbers' is connected to the in_stream called
    # 'data'
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['sequence_of_integers', 'data'],
        out_stream_names=[],
        connect_sources=[('sequence_of_integers', sequence_of_integers),
                         ('data', random_numbers)],
        connect_actuators=[],
        name='proc')
    # STEP 4: CREATE AND RUN A MULTIPROCESS APPLICATION
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()


# ----------------------------------------------------------------
#   EXAMPLE OF A SINK
# ---------------------------------------------------------------- 
def check_correctness_of_output(in_stream, check_list):
    def check(v, index, check_list):
        # v is in_list[index]
        assert v == check_list[index]
        next_index = index + 1
        return next_index
    sink_element(func=check, in_stream=in_stream, state=0,
                 check_list=check_list)


# ----------------------------------------------------------------
#   EXAMPLE OF MAP_ELEMENT
# ----------------------------------------------------------------
def map_element_example_1():
    # STEP 1: DEFINE SOURCES
    source_list = range(10)
    def data_stream(out_stream):
        return source_list_to_stream(
            in_list=source_list, out_stream=out_stream)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
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
            filename='map_element_example_1.dat')

    # STEP 3: CREATE THE PROCESS
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['test_input'],
        out_stream_names=[],
        connect_sources=[('test_input', data_stream)],
        connect_actuators=[],
        name='proc')
    
    # STEP 4: CREATE AND RUN A MULTIPROCESS APPLICATION
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()


# ----------------------------------------------------------------
#   EXAMPLE OF MAP_ELEMENT
# ----------------------------------------------------------------
def map_element_example_2():
    # STEP 1: DEFINE SOURCES
    source_list = 'hello world'
    def source(out_stream):
        return source_list_to_stream(
            in_list=source_list, out_stream=out_stream)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    def compute_func(in_streams, out_streams):
        import string
        f = string.upper
        check_list = map(f, source_list)
        t = Stream()
        map_element(
            func=f, in_stream=in_streams[0], out_stream=t)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='map_element_example_2.dat')

    # STEP 3: CREATE THE PROCESS
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc')
    
    # STEP 4: CREATE AND RUN A MULTIPROCESS APPLICATION
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()

# ----------------------------------------------------------------
#   EXAMPLE OF MAP_ELEMENT
# ----------------------------------------------------------------
def map_element_example_3():
    # STEP 1: DEFINE SOURCES
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(
            in_list=source_list, out_stream=out_stream)

    # Class used in map_element
    class example_class(object):
        def __init__(self, multiplicand):
            self.multiplicand = multiplicand
            self.running_sum = 0
        def step(self, v):
            result = v * self.multiplicand + self.running_sum
            self.running_sum += v
            return result

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    def compute_func(in_streams, out_streams):
        eg = example_class(multiplicand=2)
        check_list = [0, 2, 5, 9, 14, 20, 27, 35, 44, 54]
        t = Stream()
        map_element(
            func=eg.step, in_stream=in_streams[0], out_stream=t)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='map_element_example_3.dat')

    # STEP 3: CREATE THE PROCESS
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc')
    
    # STEP 4: CREATE AND RUN A MULTIPROCESS APPLICATION
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()

# ----------------------------------------------------------------
#   EXAMPLE OF FILTER_ELEMENT
# ----------------------------------------------------------------
def filter_element_example_1():
    # STEP 1: DEFINE SOURCES
    source_list = source_list = [1, 1, 3, 3, 5, 5, 7, 7, 9, 9]
    def source(out_stream):
        return source_list_to_stream(
            in_list=source_list, out_stream=out_stream)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    def compute_func(in_streams, out_streams):
        def less_than_n(v, n):
            return v <= n, n+1
        check_list = [1, 3, 5, 7, 9]
        t = Stream()
        filter_element(
            func=less_than_n, in_stream=in_streams[0], out_stream=t,
            state=0)
        check_correctness_of_output(
            in_stream=t, check_list=check_list)
        stream_to_file(
            in_stream=t,
            filename='filter_element_example_1.dat')

    # STEP 3: CREATE THE PROCESS
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc')
    
    # STEP 4: CREATE AND RUN A MULTIPROCESS APPLICATION
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()

def clock_offset_estimation_single_process_multiple_sources():
    """
    Another test of single_process_multiple_sources().
    This process merges offsets received from two ntp sources and
    computes their average over a moving time window, and puts the
    result on a file, average.dat
    This process has two sources, each of which receives ntp offsets
    from ntp servers. The computational network consists of three
    agents: 
    (1) an agent that merges the two sources, and
    (2) an agent that computes the average of the merged stream over a
    window, and
    (3) a sink agent that puts the averaged stream in file called
    'average.dat'. 

    The steps for creating the process are:
    (1) Define the two sources:
            ntp_0(out_stream), ntp_1(out_stream). 
    (2) Define the computational network:
        compute_func(in_streams, out_streams), where
        in_streams and out_streams are lists of streams.
        In this examples, in_streams is list consisting of
        two input streams, and out_streams is empty.
    (3) Call proc = shared_memory_process(...) to create a process
        proc.
    Next we make a multiprocess application consisting of the single
    process proc. Since the application has a single process it has
    no connections to other processes.
    (4) Call mp = Multiprocess(processes=[proc], connections=[])
        to make mp, a multiprocess application, and then call
        mp.run() to run the application.


    """
    ntp_server_0 = '0.us.pool.ntp.org'
    ntp_server_1 = '1.us.pool.ntp.org'
    time_interval = 0.1
    num_steps = 20
    def average_of_list(a_list):
        if a_list:
            # Remove None elements from the list
            a_list = [i for i in a_list if i is not None]
            # Handle the non-empty list.
            if a_list:
                return sum(a_list)/float(len(a_list))
        # Handle the empty list
        return 0.0

    # STEP 1: DEFINE SOURCES
    def ntp_0(out_stream):
        return offsets_from_ntp_server(
            out_stream, ntp_server_0, time_interval, num_steps)

    def ntp_1(out_stream):
        return offsets_from_ntp_server(
            out_stream, ntp_server_1, time_interval, num_steps)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    # This network has two input streams, one from each source
    # It has two internal streams: merged_stream and averaged_stream.
    # It has 3 agents.
    # (1) The networks two input streams feed a blend agent which
    # outputs merged_stream.
    # (2) The map_window agent reads merged_stream and outputs
    # averaged_stream.
    # (3) The stream_to_file agent inputs averaged_stream. This agent
    # is a sink which puts the stream into the file called
    # 'average.dat'. The file will contain floating point numbers that
    # are the averages of the specified sliding winow.
    def compute_func(in_streams, out_streams):
        merged_stream = Stream('merge of two ntp server offsets')
        averaged_stream = Stream('sliding window average of offsets')
        blend(
            func=lambda x: x, in_streams=in_streams,
            out_stream=merged_stream)
        map_window(
            func=average_of_list,
            in_stream=merged_stream, out_stream=averaged_stream,
            window_size=2, step_size=1)
        stream_to_file(
            in_stream=averaged_stream, filename='average.dat') 

    # STEP 3: CREATE THE PROCESS
    # Create a process with three threads:
    # two source threads and a compute thread.
    # The two source threads execute the functions ntp_0
    # and ntp_1
    # The compute thread executes function compute_func.
    # The names of the inputs of compute_func are:
    # 'source_0' and 'source_1'.
    # The source, ntp_0, is connected to the
    # in_stream called 'source_0'. The source
    # ntp_1 is connected to the in_stream called
    # 'source_1'
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['source_0', 'source_1'],
        out_stream_names=[],
        connect_sources=[('source_0', ntp_0),
                         ('source_1', ntp_1)],
        connect_actuators=[],
        name='proc')
    # STEP 4: CREATE AND RUN A MULTIPROCESS APPLICATION
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()



# ----------------------------------------------------------------
# ----------------------------------------------------------------
#             TESTS
# ----------------------------------------------------------------
# ---------------------------------------------------------------- 

if __name__ == '__main__':
    print
    print '-----------------------------------------------------'
    print 'Each process terminates when no more inputs arrive'
    print
    print '-----------------------------------------------------'
    print 'Starting single_process_single_source_example_1()'
    #single_process_single_source_example_1()
    print 'Finished single_process_single_source_example_1()'
    print '10, 20, 30, 40 will be appended to file test.dat'
    print
    print '-----------------------------------------------------'
    print
    print 'Starting single_process_multiple_sources_example_1()'
    #single_process_multiple_sources_example_1()
    print 'Finished single_process_multiple_sources_example_1()'
    print '(1, r1), (2, r2), ... will be appended to file output.dat'
    print 'where r1, r2, .. are random numbers.'
    print
    print 'Starting map_element_example_1()'
    #map_element_example_1()
    print 'Finished map_element_example_1()'
    print '[0, 10, 20, ... ,90] will be appended to map_element_example_1.dat'
    print
    print 'Starting map_element_example_2()'
    #map_element_example_2()
    print 'Finished map_element_example_1()'
    print 'HELLO WORLD will be appended to map_element_example_2.dat'
    print
    print 'Starting map_element_example_3()'
    map_element_example_3()
    print 'Finished map_element_example_3()'
    print '[0, 2, 5, 9, 14, 20, 27, 35, 44, 54] appended to map_element_example_3.dat'
    print
    print 'Starting filter_element_example_1()'
    filter_element_example_1()
    print 'Finished filter_element_example_1()'
    print '[1, 3, 5, 7, 9] appended to filter_element_example_1.dat'
    print
    print '-----------------------------------------------------'
    print
    print 'Starting'
    print 'clock_offset_estimation_single_process_multiple_sources'
    print 'This step takes time detecting that source threads have'
    print 'terminated. These sources get data from ntp servers.'
    clock_offset_estimation_single_process_multiple_sources()
    print 'Finished'
    print 'clock_offset_estimation_single_process_multiple_sources'
    print 'The average of offsets will be appended to average.dat'
    print
    print '-----------------------------------------------------'
