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
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../timing"))
from distributed import distributed_process
from VM import VM
from sink import sink_element, stream_to_file

def single_process_subscriber():

    def compute_func(in_streams, out_streams):
        stream_to_file(in_streams[0], 'result.dat')

    proc_1 = distributed_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[],
        connect_actuators=[],
        name='proc_1')

    vm_1 = VM(
        processes=[proc_1],
        connections=[],
        subscribers=[(proc_1, 'in', 'copy_of_source_list')])
    vm_1.start()

if __name__ == '__main__':
    single_process_subscriber()
