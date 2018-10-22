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
from multicore import StreamProcess, single_process_single_source
from multicore import single_process_multiple_sources
# stream is in core
from stream import Stream
# op, merge, source, sink are in agent_types
from op import map_element, map_window
from merge import zip_stream, blend
from source import source_function
from sink import stream_to_file
# timing is in examples.
from timing import offsets_from_ntp_server

def identity(x): return x

# ----------------------------------------------------------------
# ----------------------------------------------------------------
#   EXAMPLES: SINGLE PROCESS, SINGLE SOURCE
# ----------------------------------------------------------------
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

    The steps for creating the process are:
    (1) Define the source: source(out_stream), where out_stream is a
        stream, and is stream into which source data is output.
    (2) Define the computational network: compute(in_stream), where
        in_stream is a stream, and is the only input stream of the
        network. 
    (3) Call single_process_single_source()

    """

    # STEP 1: DEFINE SOURCES
    def source(out_stream):
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
        return source_function(
            func=generate_sequence, out_stream=out_stream,
            time_interval=0.1, num_steps=4, state=0)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    def compute(in_stream):
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
            func=f, in_stream=in_stream, out_stream=t)
        stream_to_file(in_stream=t, filename='test.dat')

    # STEP 3: CREATE THE PROCESS
    # Use single_process_multiple_sources() to create the process. 
    # Create a process with two threads: a source thread and
    # a compute thread. The source thread executes the function
    # g, and the compute thread executes function h.
    single_process_single_source(
        source_func=source, compute_func=compute)


# ----------------------------------------------------------------
# ----------------------------------------------------------------
#   EXAMPLES: SINGLE PROCESS, MULTIPLE SOURCES
# ----------------------------------------------------------------
# ---------------------------------------------------------------- 

def single_process_multiple_sources_example_1():
    """
    This example has two sources: source_0 generates 1, 2, 3, 4, ...
    and source_1 generates random numbers. The computation zips the two
    streams together and writes the result to a file called
    output.dat.
    
    num_steps is the number of values produced by the source. For
    example, if the smaller of the num_steps for each source is 10,
    then (1, r1), (2, r2), ..., (10, r10), ... will be appended to the
    file  output.dat where r1,..., r10 are random numbers.
 
    The steps for creating the process are:
    (1) Define the two sources:
            source_0(out_stream), source_1(out_stream). 
    (2) Define the computational network: compute(in_streams) where
       in_streams is a list of streams. In this example, in_streams is
       a list of two streams, one from each source.
    (3) Call single_process_multiple_sources()

    """
    import random

    # STEP 1: DEFINE SOURCES
    def source_0(out_stream):
        # A simple source which outputs 1, 2, 3, 4, .... on
        # out_stream.
        def generate_sequence(state):
            return state+1, state+1

        # Return an agent which takes 10 steps, and
        # sleeps for 0.1 seconds between successive steps, and
        # puts the next element of the sequence in out_stream,
        # and starts the sequence with value 0. The elements on
        # out_stream will be 1, 2, 3, ...
        return source_function(
            func=generate_sequence, out_stream=out_stream,
            time_interval=0.1, num_steps=10, state=0)

    def source_1(out_stream):
        # A simple source which outputs random numbers on
        # out_stream.

        # Return an agent which takes 10 steps, and sleeps for 0.1
        # seconds between successive steps, and puts a random number
        # on out_stream at each step.
        return source_function(
            func=random.random, out_stream=out_stream,
            time_interval=0.1, num_steps=10)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    def compute(in_streams):
        # in_streams is a list of streams.
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
    # Use single_process_multiple_sources() to create the process. 
    # Create a process with three threads: two source threads and
    # a compute thread. The source threads execute the functions
    # source_0 and source_1, and the compute thread executes function
    # compute. 
    single_process_multiple_sources(
        list_source_func=[source_0, source_1], compute_func=compute)
    

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
            source_0(out_stream), source_1(out_stream). 
    (2) Define the computational network: compute(in_streams) where
       in_streams is a list of streams. In this example, in_streams is
       a list of two streams, one from each source.
    (3) Call single_process_multiple_sources()

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
    def source_0(out_stream):
        return offsets_from_ntp_server(
            out_stream, ntp_server_0, time_interval, num_steps)

    def source_1(out_stream):
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
    def compute(in_streams):
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
    # Use single_process_multiple_sources() to create the process.
    single_process_multiple_sources(
        list_source_func=[source_0, source_1], compute_func=compute)



# ----------------------------------------------------------------
# ----------------------------------------------------------------
#             TESTS
# ----------------------------------------------------------------
# ---------------------------------------------------------------- 

if __name__ == '__main__':
    print
    print '-----------------------------------------------------'
    print 'You will see input queue empty a few times.'
    print 'Each process waits till no more inputs arrive before'
    print 'it terminates.'
    print
    print '-----------------------------------------------------'
    print 'Starting single_process_single_source_example_1()'
    single_process_single_source_example_1()
    print 'Finished single_process_single_source_example_1()'
    print '10, 20, 30, 40 will be appended to file test.dat'
    print
    print '-----------------------------------------------------'
    print
    print 'Starting single_process_multiple_sources_example_1()'
    single_process_multiple_sources_example_1()
    print 'Finished single_process_multiple_sources_example_1()'
    print '(1, r1), (2, r2), ... will be appended to file output.dat'
    print 'where r1, r2, .. are random numbers.'
    print
    print '-----------------------------------------------------'
    print
    print 'Starting'
    print 'clock_offset_estimation_single_process_multiple_sources' 
    clock_offset_estimation_single_process_multiple_sources()
    print 'Finished'
    print 'clock_offset_estimation_single_process_multiple_sources'
    print 'The average of offsets will be appended to average.dat'
    print
    print '-----------------------------------------------------'
