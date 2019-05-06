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

from multicore import shared_memory_process, Multiprocess
from distributed import distributed_process
from VM import VM
from op import map_element
from source import source_func_to_stream, source_list_to_stream

def two_process_publisher():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(source_list, out_stream)
    
    def compute_0(in_streams, out_streams):
        map_element(
            func=lambda x: x,
            in_stream=in_streams[0], out_stream=out_streams[0])

    proc_0 = distributed_process(
        compute_func=compute_0,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[('in', source)],
        name='process_0')

    def compute_1(in_streams, out_streams):
        map_element(
            func=lambda x: x+10,
            in_stream=in_streams[0], out_stream=out_streams[0])
                    
    proc_1 = distributed_process(
        compute_func=compute_1,
        in_stream_names=['in'],
        out_stream_names=['out'],
        connect_sources=[],
        name='process_1'
        )

    vm_0 = VM(
        processes=[proc_0, proc_1],
        connections=[(proc_0, 'out', proc_1, 'in')],
        publishers=[(proc_1, 'out', 'publication')])
    vm_0.start()


# ----------------------------------------------------------------
# ----------------------------------------------------------------
#             TESTS
# ----------------------------------------------------------------
# ----------------------------------------------------------------

def two_process_publisher_test():
    print
    print 'Starting two_process_publisher_test()'
    two_process_publisher()
    print 'Finished two_process_publisher_test()'
    print


if __name__ == '__main__':
    two_process_publisher_test()
