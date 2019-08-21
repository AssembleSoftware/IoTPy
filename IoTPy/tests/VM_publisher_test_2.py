"""
This module is used with VM_publisher_test.py to test
APMQ/pika. Execute
       python VM_publisher_test.py
in one shell and
execute
       python VM_subcriber_test.py
in another shell.
Start the subscriber an instant before starting the publisher.

This application consists of a single publisher and a single
subscriber. The publisher VM has two processes called proc_0 and
proc_1, see
vm_0 = VM(processes=[proc_0, proc_1],....)

proc_0 has a single source which copies source_list to its
single input stream 'in'. The compute thread of proc_0 merely
copies its single input stream 'in' to its single output stream
'out'. proc_0 has no actuators.

proc_1 has no sources or actuators. It has a single input and a
single output stream called 'in' and 'out'. Its compute thread
adds 10 to elements of its input stream and puts the results on
its output stream.

The VM connects the output stream 'out' of proc_o to the input
stream 'in' of proc_1. See:
      connections=[(proc_0, 'out', proc_1, 'in')],
The output stream 'out' of proc_0 is published as a publication
stream called 'publication', see:
      publishers=[(proc_1, 'out', 'publication')]

For example, if source_list is [0, 1,.., 9] then the publication
stream will be [10, 11, ..., 19].


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
