"""
This module is used with VM_publisher_test.py to test
APMQ/pika. Execute
       python VM_publisher_test.py
in one shell and
execute
       python VM_subcriber_test.py
in another shell.

The publisher publishes p*1, p*2, p*3, ... , p*num_steps on a stream
with global name 'sequence'. Currently num_steps is set to 10 and p is
set to 7.

The subscriber subscribes to 'sequence' and prints the stream.

Start the subscriber an instant before starting the publisher. 

"""

import sys
import os
import random
sys.path.append(os.path.abspath("../multiprocessing"))
sys.path.append(os.path.abspath("../agent_types"))

from multicore import shared_memory_process
from distributed import distributed_process
from VM import VM
from op import map_element
from source import source_func_to_stream

def single_process_publication_producer():
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
    processes and run the application.

    """

    # STEP 1: DEFINE SOURCES
    def source(out_stream):
        """
        A simple source which outputs 1, 2, 3,... on
        out_stream.
        """
        def generate_sequence(state):
            return state+1, state+1

        # Return an agent which takes 10 steps, and
        # sleeps for 0.1 seconds between successive steps, and
        # puts the next element of the sequence in stream s,
        # and starts the sequence with value 0. The elements on
        # out_stream will be 1, 2, 3, ...
        return source_func_to_stream(
            func=generate_sequence, out_stream=out_stream,
            time_interval=0.1, num_steps=10, state=0)

    # STEP 2: DEFINE ACTUATORS
    # This example has no actuators
    
    # STEP 3: DEFINE COMPUTE_FUNC
    def f(in_streams, out_streams):
        map_element(
            func=lambda x: 7*x,
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

    # FINAL STEP: CREATE A VM AND START IT.
    # Since this application has a single process it has no
    # connections between processes. The process, proc_0, publishes
    # its output stream called 'out' to a stream called
    # 'sequence'. This process does not subscribe to streams. 
    vm_0 = VM(
        processes=[proc_0],
        connections=[],
        publishers=[(proc_0, 'out', 'sequence')])
    vm_0.start()


# ----------------------------------------------------------------
# ----------------------------------------------------------------
#             TESTS
# ----------------------------------------------------------------
# ----------------------------------------------------------------

def single_process_publication_producer_test():
    print
    print 'Starting single_process_publication_example_1()'
    single_process_publication_producer()
    print
    print '-----------------------------------------------------'

def test():
    single_process_publication_producer_test()

if __name__ == '__main__':
    test()
