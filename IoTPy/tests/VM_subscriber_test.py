"""
This module is used with VM_publisher_test.py to test
APMQ/pika. Execute
   python VM_publisher_test.py
in one shell and
execute
   python VM_publisher_test.py
in another shell.

The publisher publishes p*1, p*2, p*3, ... , p*num_steps on a stream
with global name 'sequence'. Currently num_steps is set to 10 and p is
set to 7.

The subscriber subscribes to 'sequence' and prints the stream.

Start the subscriber an instant before starting the publisher. 

"""
import sys
import os
sys.path.append(os.path.abspath("../multiprocessing"))
sys.path.append(os.path.abspath("../agent_types"))

from distributed import distributed_process
from VM import VM
from sink import sink_element

def single_process_publication_subscriber():
    """
    The application in this example consists of single process.
    The process has no source and no actuator. It has a single
    in_stream called 'in'.

    This example creates a virtual machine (vm) which subscribes to
    a stream called 'sequence'.

    The steps for creating a process are:
    (1) Define the sources.
        In this example we have no sources.
    (2) Define the actuators.
        In this example we have no actuators.
    (3) Define compute_func. This process has a single input stream
        and no output stream.
    (4) Create the process by calling distributed_process()

    Final step
    After creating all processes, specify the connections between
    processes and run the virtual machine..

    """
    # SKIP STEPS 1, 2 BECAUSE NO SOURCES OR ACTUATORS.

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

    # FINAL STEP: CREATE A VM AND START IT.
    # Since this application has a single process it has no
    # connections between processes. The process, proc_1, subscribes
    # to a stream called 'sequence'. This process does not publish
    # streams. 
    vm_1 = VM(
        processes=[proc_1],
        connections=[],
        subscribers=[(proc_1, 'in', 'sequence')])
    vm_1.start()


# ----------------------------------------------------------------
# ----------------------------------------------------------------
#             TESTS
# ----------------------------------------------------------------
# ----------------------------------------------------------------

def single_process_publication_subscriber_test():
    print
    print 'Starting single_process_subscription_example_1()'
    single_process_publication_subscriber()
    print
    print '-----------------------------------------------------'

def test():
    single_process_publication_subscriber_test()

if __name__ == '__main__':
    test()
