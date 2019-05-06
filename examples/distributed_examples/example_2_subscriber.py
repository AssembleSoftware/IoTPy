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

from distributed import distributed_process
from VM import VM
from sink import sink_element, stream_to_file
from op import map_element

def two_process_subscriber():
    def compute_2(in_streams, out_streams):
        map_element(
            func=lambda x: x*100,
            in_stream=in_streams[0], out_stream=out_streams[0])

    proc_2 = distributed_process(
        compute_func=compute_2,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='process_3')

    def compute_3(in_streams, out_streams):
        stream_to_file(
            in_streams[0], 'result.dat')
                    
    proc_3 = distributed_process(
        compute_func=compute_3,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[],
        name='process_1'
        )
    vm_1 = VM(
        processes=[proc_2, proc_3],
        connections=[(proc_2, 'out', proc_3, 'in')],
        subscribers=[(proc_2, 'in', 'publication')])
    vm_1.start()


# ----------------------------------------------------------------
# ----------------------------------------------------------------
#             TESTS
# ----------------------------------------------------------------
# ----------------------------------------------------------------

def two_process_subscriber_test():
    print
    print 'Starting two_process_publisher_test()'
    two_process_subscriber()
    print 'Finished two_process_publisher_test()'
    print

if __name__ == '__main__':
    two_process_subscriber_test()
