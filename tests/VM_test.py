"""
This module contains tests:

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

from multicore import SharedMemoryProcess, shared_memory_process
from multicore import shared_memory_process, Multiprocess
from multicore import single_process_single_source
from multicore import single_process_multiple_sources
from distributed import distributed_process
from VM import VM
from stream import Stream
from op import map_element, map_window
from merge import zip_stream, blend
from source import source_func_to_stream, source_function, source_list
from sink import stream_to_file, sink_element
from timing import offsets_from_ntp_server
from print_stream import print_stream

# ----------------------------------------------------------------

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
    (4) Create the process by calling distributed_process()

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
    # proc = distributed_process(
    proc = distributed_process(
        compute_func=compute_func,
        in_stream_names=['source_0','source_1'],
        out_stream_names=[],
        connect_sources=[('source_0', source_0), ('source_1', source_1)],
        connect_actuators=[],
        name='multiple source test')

    # FINAL STEP: RUN APPLICATION
    # Since this application has a single process it has no
    # connections between processes.
    vm = Multiprocess(processes=[proc], connections=[])
    vm.run()

#-----------------------------------------------------------------
def single_process_publication_example_1():
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
    (4) Create the process by calling distributed_process()

    Final step
    After creating all processes, specify the connections between
    processes and run the application by calling run_multiprocess.

    """
    #------------------------
    #------------------------
    # VM_0
    #------------------------
    #------------------------

    #------------------------
    # proc_0 in VM_0
    #------------------------

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
    def f(in_streams, out_streams):
        map_element(
            func=lambda x: x,
            in_stream=in_streams[0],
            out_stream=out_streams[0])

    # STEP 4: CREATE PROCESSES
    # This process has a single input stream that we call 'in' and it
    # has no output streams. We connect the source to the input stream
    # called 'in'.
    proc_0 = distributed_process(
        compute_func=f,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc_0')

    # STEP 5: CREATE VM
    # Since this application has a single process it has no
    # connections between processes.
    vm_0 = VM(
        processes=[proc_0],
        connections=[],
        publishers=[(proc_0, 'out', 'sequence')])

    #------------------------
    #------------------------
    # VM_1
    #------------------------
    #------------------------

    #------------------------
    # proc_1 in VM_1
    #------------------------
    # STEP 1: DEFINE SOURCES
    # skip this step since proc_1 has no sources.

    # STEP 2: DEFINE ACTUATORS
    # # skip this step since proc_1 has no actuators.

    # STEP 3: DEFINE COMPUTE_FUNC
    def g(in_streams, out_streams):
        def print_element(v): print 'stream element is ', v
        sink_element(
            func=print_element, in_stream=in_streams[0])

    # STEP 4: CREATE PROCESSES
    proc_1 = distributed_process(
        compute_func=g,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[],
        connect_actuators=[],
        name='proc_1')

    # STEP 5: CREATE VM
    # Since this application has a single process it has no
    # connections between processes.
    vm_1 = VM(
        processes=[proc_1],
        connections=[],
        subscribers=[(proc_1, 'in', 'sequence')])

    # STEP 6: START PROCESSES
    vm_0.start()
    vm_1.start()

    # STEP 7: JOIN PROCESSES
    vm_0.join()
    vm_1.join()


#-----------------------------------------------------------------
def two_process_publication_example_1():

    """
    The application in this example consists of two VMs. It is a
    small extension of def single_process_publication_example_1(). The
    first VM has two processes, proc_0 and proc_1. The second VM has two
    processes, proc_2 and proc_3.

    THE FIRST VM

    PROC_0
    proc_0 has a single source and no actuator.
    The single source generates 1, 2, 3, 4, .....
    num_steps is the number of values output by the source.
    The compute function has a single in_stream and a single
    out_stream. commpute_func merely passes its in_stream to its
    out_stream. 

    PROC_1
    proc_1 has no sources or actuators.
    Its compute function has a single in_stream and a single
    out_stream. compute_func multiples its input elements by 10 and
    puts the results on out_stream.

    THE SECOND VM

    PROC_2
    proc_2 has no sources or actuators. Its compute function has a
    single in_stream and a single out_stream. compute_func multiplies
    elements in in_stream by 2 and places results on out_stream.

    PROC_3
    proc_2 has no sources or actuators. Its compute function has a
    single in_stream and no out_stream. compute_func prints its
    in_stream. 

    The steps for creating a process are:
    (1) Define the sources.
        In this example we have two sources, source_0 and source_1
    (2) Define the actuators.
        In this example we have no actuators.
    (3) Define compute_func
    (4) Create the process by calling distributed_process()
    (5) Create a VM fter creating all processes in the VM. Do this by
        specifying the connections between processes within the VM and
        by specifying the streams published by the VM and the streams 
        subscribed to by the VM.
    (6) Start the VMs.
    (7) Join the VMs. Skip this step if a VM is persistent.

    """

    #------------------------
    #------------------------
    # VM_0
    #------------------------
    #------------------------

    #------------------------
    # proc_0 in VM_0
    #------------------------

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
    def f(in_streams, out_streams):
        map_element(
            func=lambda x: x,
            in_stream=in_streams[0],
            out_stream=out_streams[0])


    # STEP 4: CREATE PROCESSES
    # This process has a single input stream that we call 'in' and it
    # has no output streams. We connect the source to the input stream
    # called 'in'.
    proc_0 = distributed_process(
        compute_func=f,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc_0')

    #------------------------
    # proc_1 in VM_0
    #------------------------
    # STEP 1: DEFINE SOURCES
    # skip this step since proc_1 has no sources.

    # STEP 2: DEFINE ACTUATORS
    # # skip this step since proc_1 has no actuators.

    # STEP 3: DEFINE COMPUTE_FUNC
    def g(in_streams, out_streams):
        map_element(
            func=lambda x: 10*x,
            in_stream=in_streams[0],
            out_stream=out_streams[0])

    # STEP 4: CREATE PROCESSES
    proc_1 = distributed_process(
        compute_func=g,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        connect_actuators=[],
        name='proc_1')

    # STEP 5: CREATE VM
    vm_0 = VM(
        processes=[proc_0, proc_1],
        connections=[
            (proc_0, 'out', proc_1, 'in')
            ],
        publishers=[(proc_1, 'out', 'sequence')])


    #------------------------
    #------------------------
    # VM_1
    #------------------------
    #------------------------

    #------------------------
    # proc_2 in VM_1
    #------------------------
    # STEP 1: DEFINE SOURCES
    # skip this step since proc_1 has no sources.

    # STEP 2: DEFINE ACTUATORS
    # # skip this step since proc_1 has no actuators.

    # STEP 3: DEFINE COMPUTE_FUNC
    def h(in_streams, out_streams):
        map_element(
            func=lambda x: 2*x,
            in_stream=in_streams[0],
            out_stream=out_streams[0])

    # STEP 4: CREATE PROCESSES
    proc_2 = distributed_process(
        compute_func=h,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        connect_actuators=[],
        name='proc_2')

    #------------------------
    # proc_3 in VM_1
    #------------------------
    # STEP 1: DEFINE SOURCES
    # skip this step since proc_1 has no sources.

    # STEP 2: DEFINE ACTUATORS
    # # skip this step since proc_1 has no actuators.

    # STEP 3: DEFINE COMPUTE_FUNC
    def pr(in_streams, out_streams):
        def print_element(v): print 'stream element is ', v
        sink_element(
            func=print_element, in_stream=in_streams[0])

    # STEP 4: CREATE PROCESSES
    proc_3 = distributed_process(
        compute_func=pr,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[],
        connect_actuators=[],
        name='proc_3')

    # STEP 5: CREATE VM
    vm_1 = VM(
        processes=[proc_2, proc_3],
        connections=[(proc_2, 'out', proc_3, 'in')],
        subscribers=[(proc_2, 'in', 'sequence')])

    # STEP 6: START PROCESSES
    vm_0.start()
    vm_1.start()

    # STEP 7: JOIN PROCESSES
    vm_0.join()
    vm_1.join()

# ----------------------------------------------------------------
# ----------------------------------------------------------------
#             TESTS
# ----------------------------------------------------------------
# ----------------------------------------------------------------
def single_process_publication_example_1_test():
    print
    print 'Starting single_process_publication_example_1()'
    print 'Outputs: '
    print
    print 'stream element is i'
    print
    print ' for i in range(n) where n is currently set to 5.'
    print
    single_process_publication_example_1()
    print 'Finished single_process_publication_example_1()'
    print
    print '-----------------------------------------------------'
def two_process_publication_example_1_test():
    print
    print 'Starting two_process_publication_example_1()'
    print 'Outputs: '
    print
    print 'stream element is 20*i'
    print
    print ' for i in 1, 2, 3, 4.'
    print
    two_process_publication_example_1()
    print 'Finished two_process_publication_example_1()'
    print
    print '-----------------------------------------------------'
    
def test():
    single_process_publication_example_1_test()
    two_process_publication_example_1_test()

if __name__ == '__main__':
    test()
