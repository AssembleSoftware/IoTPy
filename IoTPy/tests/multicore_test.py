"""
This module contains tests:
* test_single_process_single_source()
* test_single_process_multiple_sources()
* offset_estimation_test()
which tests code from multicore.py in multiprocessing.

"""

import sys
import os
import threading
import random
sys.path.append(os.path.abspath("../multiprocessing"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../../examples/timing"))

from multicore import StreamProcess, single_process_single_source
from multicore import single_process_multiple_sources
from multicore import make_process, run_multiprocess
from stream import Stream
from op import map_element, map_window
from merge import zip_stream, blend
from source import source_func_to_stream, source_function, source_list
from sink import stream_to_file
from timing import offsets_from_ntp_server
from print_stream import print_stream

def identity(x): return x

# ----------------------------------------------------------------
# ----------------------------------------------------------------
#   EXAMPLES: SINGLE PROCESS, SINGLE SOURCE
# ----------------------------------------------------------------
# ---------------------------------------------------------------- 

def single_process_single_source_example_1():
    """
    The application in this example consists of single process.
    The process has a single source and no actuator.
    The single source generates 1, 2, 3, 4, .....
    The compute function multiplies this sequence by 10
    and puts the result in the file called test.dat
    num_steps is the number of values output by the source.
    For example, if num_steps is 4 and test.dat is empty before the
    function is called then, test.dat will contain 10, 20, 30, 40
    on separate lines.

    The steps for creating a process are:
    (1) Define the sources.
        In this example we have two sources, source_0 and source_1
    (2) Define the actuators.
        In this example we have no actuators.
    (3) Define compute_func
    (4) Create the process by calling make_process()

    Final step
    After creating all processes, specify the connections between
    processes and run the application by calling run_multiprocess.

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
        return source_func_to_stream(
            func=generate_sequence, out_stream=out_stream,
            time_interval=0.1, num_steps=4, state=0)

    # STEP 2: DEFINE ACTUATORS
    # This example has no actuators
    
    # STEP 3: DEFINE COMPUTE_FUNC
    def compute_func(in_streams, out_streams):
        # This is a simple example of a composed agent consisting
        # of two component agents where the network has a single input
        # stream and no output stream.
        # The first component agent applies function f to each element 
        # of in_stream, and puts the result in its output stream t.
        # The second component agent puts values in its input stream t
        # on a file called test.dat.
        # test.dat will contain 10, 20, 30, ....

        def f(x): return x*10
        t = Stream()
        map_element(
            func=f, in_stream=in_streams[0], out_stream=t)
        stream_to_file(in_stream=t, filename='test.dat')

    # STEP 4: CREATE PROCESSES
    # This process has a single input stream that we call 'in' and it
    # has no output streams. We connect the source to the input stream
    # called 'in'.
    proc = make_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', source)],
        connect_actuators=[])

    # FINAL STEP: RUN APPLICATION
    # Since this application has a single process it has no
    # connections between processes.
    run_multiprocess(processes=[proc], connections=[])

# ----------------------------------------------------------------
# ----------------------------------------------------------------
#   EXAMPLES: SINGLE PROCESS, MULTIPLE SOURCES
# ----------------------------------------------------------------
# ---------------------------------------------------------------- 

def single_process_multiple_sources_example_1():
    """
    The application in this example consists of a single process.
    This process has two sources: source_0 generates 1, 2, 3, 4, ...
    and source_1 generates random numbers. The agent zips the
    two streams together and writes the result to a file called
    output.dat. This file will have
           (1, r1), (2, r2), (3, r3), ...
    where r1, r2,.... are random numbers.

    The steps for creating a process are:
    (1) Define the sources.
        In this example we have two sources, source_0 and source_1
    (2) Define the actuators.
        In this example we have no actuators.
    (3) Define compute_func
    (4) Create the process by calling make_process()

    Final step
    After creating all processes, specify the connections between
    processes and run the application by calling run_multiprocess. 

    """
    import random

    # STEP 1: DEFINE SOURCES
    def source_0(out_stream):
        # A simple source which outputs 1, 2, 3, 4, .... on
        # out_stream.
        def generate_sequence(state):
            return state+1, state+1

        # Return a source which takes 10 steps, and
        # sleeps for 0.1 seconds between successive steps, and
        # puts the next element of the sequence in out_stream,
        # and starts the sequence with value 0. The elements on
        # out_stream will be 1, 2, 3, ...
        return source_func_to_stream(
            func=generate_sequence, out_stream=out_stream,
            time_interval=0.1, num_steps=10, state=0)

    def source_1(out_stream):
        # A simple source which outputs random numbers on
        # out_stream.

        # Return a source which takes 10 steps, and sleeps for 0.1
        # seconds between successive steps, and puts a random number
        # on out_stream at each step.
        return source_func_to_stream(
            func=random.random, out_stream=out_stream,
            time_interval=0.1, num_steps=10)

    # STEP 2: DEFINE ACTUATORS
    # This example has no actuators

    # STEP 3: DEFINE COMPUTE_FUNC
    def compute_func(in_streams, out_streams):
        # This is a simple example of a composed agent consisting
        # of two component agents where the composed agent has two
        # input streams and no output stream.
        # The first component agent zips the two input streams and puts
        # the result on its output stream t which is internal to the
        # network. 
        # The second component agent puts values in its input stream t
        # on a file called output.dat.
        from sink import stream_to_file
        # t is an internal stream of the network
        t = Stream()
        zip_stream(in_streams=in_streams, out_stream=t)
        stream_to_file(in_stream=t, filename='output.dat')

    # STEP 4: CREATE PROCESSES
    proc = make_process(
        compute_func=compute_func,
        in_stream_names=['source_0','source_1'],
        out_stream_names=[],
        connect_sources=[('source_0', source_0), ('source_1', source_1)],
        connect_actuators=[],
        process_name='multiple source test')

    # FINAL STEP: RUN APPLICATION
    # Since this application has a single process it has no
    # connections between processes.
    run_multiprocess(
        processes=[proc], connections=[])

# ----------------------------------------------------------------
# ----------------------------------------------------------------
#   EXAMPLES: SINGLE PROCESS WITH ACTUATOR
# ----------------------------------------------------------------
# ----------------------------------------------------------------

def simple_actuator_example():
    """
    This example has a single source which generates the sequence:
    1, 2, 3, .... It has a single actuator which gets messages from a
    queue and prints the message.
    
    The steps for creating a process are:
    (1) Define the sources.
        In this example we have two sources, source_0 and source_1
    (2) Define the actuators.
        In this example we have no actuators.
    (3) Define compute_func
    (4) Create the process by calling make_process()

    Final step
    After creating all processes, specify the connections between
    processes and run the application by calling run_multiprocess.

    """
    # STEP 1: DEFINE SOURCES
    def sequence_of_integers(current_integer, max_integer):
        next_integer = current_integer + 1
        if next_integer > max_integer:
            # return next output, next state
            return None, next_integer
        else:
            return next_integer, next_integer
        
    def sequence_of_integers_source(out_stream):
        return source_func_to_stream(
            func=sequence_of_integers,
            out_stream=out_stream,
            num_steps=15, window_size=1, state=0,
            max_integer=10)

    # STEP 2: DEFINE ACTUATORS
    def print_from_queue(q):
        while True:
            v = q.get()
            if v is None:
                # exit loop
                return True
            else:
                print 'next value in queue is ', v

    # STEP 3: DEFINE COMPUTE_FUNC
    def f(in_streams, out_streams):
        def identity(v): return v
        map_element(func=identity,
                    in_stream=in_streams[0],
                    out_stream=out_streams[0])

    # STEP 4: CREATE PROCESSES
    proc=make_process(
        compute_func=f,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[('in', sequence_of_integers_source)],
        connect_actuators=[['out', print_from_queue]]
        )

    # FINAL STEP: RUN APPLICATION
    # Since this application has a single process it has no
    # connections between processes.
    run_multiprocess(processes=[proc], connections=[]) 

    
def clock_offset_estimation_single_process_multiple_sources():
    """
    Another test of a single process with multiple sources and no
    actuators. 
    This process merges offsets received from two ntp sources and
    computes their average over a moving time window, and puts the
    result on a file, average.dat
    This process has two sources, each of which receives ntp offsets
    from ntp servers. The composed agent consists of three component
    agents: 
    (1) a component agent that merges the two sources, and
    (2) a component agent that computes the average of the merged
    stream over a window, and
    (3) a component sink agent that puts the averaged stream in file
    called 'average.dat'. 

    The steps for creating a process are:
    (1) Define the sources.
        In this example we have two sources, source_0 and source_1
    (2) Define the actuators.
        In this example we have no actuators.
    (3) Define compute_func
    (4) Create the process by calling make_process()

    Final steps: After creating all processes, specify the connections
    between processes and then run the application by calling
    run_multiprocess.

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

    # STEP 2: DEFINE ACTUATORS
    # This process has no actuators

    # STEP 3: DEFINE COMPUTE_FUNC
    # This composed agent has two input streams, one from each
    # source. 
    # It has two internal streams: merged_stream and averaged_stream.
    # It has 3 component agents:
    # (1) blend: The composed agent's two input streams feed a blend
    # agent which outputs merged_stream.
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

    # STEP 4: CREATE PROCESSES
    proc=make_process(
        compute_func=compute_func,
        in_stream_names=['ntp_0', 'ntp_1'],
        out_stream_names=[],
        connect_sources=[('ntp_0', source_0), ('ntp_1', source_1)],
        connect_actuators=[]
        )

    # FINAL STEP: RUN APPLICATION
    run_multiprocess(processes=[proc], connections=[]) 

# ----------------------------------------------------------------
# ----------------------------------------------------------------
#   EXAMPLES: MULTIPROCESS
# ----------------------------------------------------------------
# ---------------------------------------------------------------- 

def multiprocess_example_1():
    """
    A simple example of a multiprocess application with two processes,
    proc_0 and proc_1. 
    proc_0 has a source, no input streams and a single output stream
    called 's'. 
    proc_1 has no sources, a single input stream called 't', and no
    output streams.
    The connections between processes is as follows:
       the output stream called 's' from proc_0 is the input stream
       called 't' in proc_1.
    The source in proc_0 generates 1, 2, 3, 4,.... and the
    agent in proc_0 multiplies these values by 10, and
    so proc_0 outputs 10, 20, 30, 40, ... on its output stream.
    proc_1 reads the output stream of proc_0, and its agent
    multiplies the elements in this stream by 200 and puts the
    values in a file called 'result.dat' which will contain:
    2000, 4000, 6000, ...

     The steps for creating a process are:
    (1) Define the sources.
        In this example we have two sources, source_0 and source_1
    (2) Define the actuators.
        In this example we have no actuators.
    (3) Define compute_func
    (4) Create the process by calling make_process()

    Final step
    After creating all processes, specify the connections between
    processes and run the application by calling run_multiprocess.

    """
    # A helper function
    def increment_state(state):
        return state+1, state+1
    
    # ----------------------------------------------------------------
    #    DEFINE EACH OF THE PROCESSES
    # ----------------------------------------------------------------

    # ----------------------------------------------------------------
    # MAKE PROCESS proc_0
    # proc_0 has no input streams and has a single output
    # stream which is called 't'.
    # It has a single source: see source_0.
    # ----------------------------------------------------------------    
    # STEP 1: DEFINE SOURCES
    def source_0(out_stream):
        return source_func_to_stream(
            func=increment_state, out_stream=out_stream,
            time_interval=0.1, num_steps=10, state=0, window_size=1,
            name='source')

    # STEP 2: DEFINE ACTUATORS
    # This process has no actuators

    # # STEP 3: DEFINE COMPUTE_FUNC
    # The agent for this process is a single map_element agent.
    # The map element agent has a single input stream: in_streams[0],
    # and it has a single output stream: out_streams[0]. The elements
    # of the output stream are 10 times the elements of the input
    # stream. 
    def compute_0(in_streams, out_streams):
        map_element(
            func=lambda x: 10*x,
            in_stream=in_streams[0], out_stream=out_streams[0])

    # STEP 4: CREATE PROCESSES
    # This process has no input streams and has a single output stream
    # which is the stream produced by the compute_0() network of
    # agents, and this output stream is called 's'. It has a single
    # source agent: source_0().
    proc_0 = make_process(
        compute_func=compute_0,
        in_stream_names=['in'],
        out_stream_names=['s'],
        connect_sources=[('in', source_0)],
        process_name='process_0')

    # ----------------------------------------------------------------
    # MAKE PROCESS proc_1
    # proc_1 has one input stream, called 't' and has no output
    # streams
    # It has no sources.
    # ----------------------------------------------------------------    

    # STEP 1: DEFINE SOURCES
    # This process has no sources; so skip this step.

    # # STEP 2: DEFINE ACTUATORS
    # This process has no actuators

    # # STEP 3: DEFINE COMPUTE_FUNC
    # This network consists of a map_element agent and
    # a file_to_stream agent which is a type of sink agent and which
    # puts the elements of result_stream on a file called 'results.dat.'
    # result_stream is internal to the network.
    def compute_1(in_streams, out_streams):
        result_stream = Stream('result of computation')
        map_element(
            func=lambda x: 200*x, in_stream=in_streams[0],
            out_stream=result_stream)
        stream_to_file(in_stream=result_stream, filename='result.dat')

    # # STEP 4: CREATE PROCESSES
    # This process has a single input stream, called 't', produced by
    # proc_1. It has no output streams.
    proc_1 = make_process(
        compute_func=compute_1,
        in_stream_names=['t'],
        out_stream_names=[],
        connect_sources=[],
        process_name='process_1'
        )

    # ----------------------------------------------------------------
    # FINAL STEP: RUN APPLICATION
    # Specify connections: A list of 4-tuples:
    # (process, output stream name, process, input stream name)
    # ----------------------------------------------------------------    
    run_multiprocess(
        processes=[proc_0, proc_1],
        connections=[(proc_0, 's', proc_1, 't')])


def clock_offset_estimation_multiprocess():
    """
    An example of a multiprocess app. This example has three
    processes: proc_0 and proc_1 get time offsets from an ntp server,
    and put them on output streams. proc_2 gets these two streams as
    input, merges them and puts the resulting stream on a file called
    'offsets.dat'.

    """    
    # ----------------------------------------------------------------
    #    DEFINE EACH OF THE PROCESSES
    # ----------------------------------------------------------------       
    # The steps for creating a process are:
    # STEP 1: Define the sources: source()
    # STEP 2: Define the computational network: compute()
    # STEP 3: Call single_process_multiple_sources()
    # Carry out the above three steps for each process
    # STEP 4: The last step is to specify the connections between
    # processes, and then make and run the multiprocess app by
    # executing run_multiprocess()

    # Constants
    ntp_server_0 = '0.us.pool.ntp.org'
    ntp_server_1 = '1.us.pool.ntp.org'
    time_interval = 0.1
    num_steps = 20

    # ----------------------------------------------------------------
    # MAKE PROCESS proc_0
    # proc_0 has no input streams and has a single output
    # stream which is called 's'.
    # It has a single source: see source_0.
    # ----------------------------------------------------------------

    # STEP 1: DEFINE SOURCES
    def source_0(out_stream):
        return offsets_from_ntp_server(
            out_stream, ntp_server_0, time_interval, num_steps)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    # This network is empty; it merely passes its in_stream to its
    # out_stream.
    def compute(in_streams, out_streams):
        map_element(
            func=lambda x: x,
            in_stream=in_streams[0], out_stream=out_streams[0]) 

    # STEP 3: CREATE THE PROCESS
    # This process has a single source, no input stream, and an output
    # stream called 's'
    proc_0 = make_process(
        compute_func=compute,
        in_stream_names=['in'],
        out_stream_names=['s'],
        connect_sources=[('in', source_0)], 
        process_name='process_1'
        )

    # ----------------------------------------------------------------
    # MAKE PROCESS proc_1
    # proc_1 has no input streams and has a single output
    # stream which is called 's'.
    # It has a single source: see source_1.
    # ----------------------------------------------------------------    
    
    # STEP 1: DEFINE SOURCES
    def source_1(out_stream):
        return offsets_from_ntp_server(
            out_stream, ntp_server_1, time_interval, num_steps)

    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS
    # This network is empty; it merely passes its in_stream to its
    # out_stream.
    def compute(in_streams, out_streams):
        map_element(
            func=lambda x: x,
            in_stream=in_streams[0], out_stream=out_streams[0]) 

    # STEP 3: CREATE THE PROCESS
    # This process has a single source, no input stream, and an output
    # stream called 's'
    proc_1 = make_process(
        compute_func=compute,
        in_stream_names=['in'],
        out_stream_names=['s'],
        connect_sources=[('in', source_1)],
        process_name='process_1'
        )

# ----------------------------------------------------------------
    # MAKE PROCESS proc_2
    # proc_2 has two input streams and no output stream.
    # It has no sources.
    # ----------------------------------------------------------------

    # STEP 1: DEFINE SOURCES
    # This process has no sources.

    # STEP 2: DEFINE COMPUTE_FUNC
    # The composed agent consists of two component agents:
    # (1) blend: an agent which blends (merges) in_streams and outputs
    #     merged_stream, and 
    # (2) stream_to_file: a sink agent which inputs merged_stream and
    #     prints it.
    def compute(in_streams, out_streams):
        merged_stream = Stream('merge of two ntp server offsets')
        blend(
            func=identity, in_streams=in_streams,
            out_stream=merged_stream)
        stream_to_file(
            in_stream=merged_stream, filename='offsets.dat') 

    # STEP 3: CREATE THE PROCESS
    # This process has no sources, two input streams, and no output
    # streams. We call the input streams 'u' and 'v'.
    proc_2 = make_process(
        compute_func=compute,
        in_stream_names=['u', 'v'],
        out_stream_names=[],
        connect_sources=[], 
        process_name='process_2'
        )

    # ----------------------------------------------------------------
    # FINAL STEP: RUN APPLICATION
    # Specify connections: A list of 4-tuples:
    # (process, output stream name, process, input stream name)
    # ----------------------------------------------------------------    
    run_multiprocess(
        processes=[proc_0, proc_1, proc_2],
        connections=[ (proc_0, 's', proc_2, 'u'),
                      (proc_1, 's', proc_2, 'v') ])

## def source_from_func_example():
##     def f():
##         return random.random()
##     source_function_object = source_function(
##         func=f, time_interval=0.01, num_steps=10)
##     single_process_single_source(
##         source_func=source_function_object.source_func,
##         compute_func=print_stream)

## def source_from_list_example():
##     source_list_object = source_list(
##         in_list=range(10), num_steps=10)
##     single_process_single_source(
##         source_func=source_list_object.source_func,
##         compute_func=print_stream)
    

# ----------------------------------------------------------------
# ----------------------------------------------------------------
#             TESTS
# ----------------------------------------------------------------
# ---------------------------------------------------------------- 

if __name__ == '__main__':
    print 'You will see input queue empty a few times.'
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
    print 'Starting simple_actuator_example()'
    simple_actuator_example()
    print 'Finished simple_actuator_example()'
    print 'This example prints: next value in queue is i'
    print 'for i to max_integer which is set to 10.'
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
    print
    print 'Starting multiprocess_example_1()'
    multiprocess_example_1()
    print 'Finished multiprocess_example_1()'
    print '2000, 4000, 6000, ... will be appended to result.dat'
    print
    print '-----------------------------------------------------'
    print
    print 'Starting clock_offset_estimation_multiprocess()'
    clock_offset_estimation_multiprocess()
    print 'Finished clock_offset_estimation_multiprocess()'
    print 'offsets from 2 servers will be appended to offsets.dat' 
    print
    print '-----------------------------------------------------'
