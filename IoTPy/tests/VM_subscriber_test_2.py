"""
This module is used with VM_publisher_test.py to test
APMQ/pika. Execute
   python VM_publisher_test.py
in one shell and
execute
   python VM_publisher_test.py
in another shell.

This application consists of a single publisher and a single
subscriber. The subscriber VM has two processes called proc_2 and
proc_3, see
vm_1 = VM(processes=[proc_2, proc_3],....)

proc_2 and proc_3 have no source threads and no actuator threads.
Both processes have a single input stream called 'in'. proc_2 has
a single output stream called 'out' and proc_3 has no output
streams.

The compute thread of proc_2 multiplies elements of its input stream
by 100 and puts the result on its output stream.
The compute thread of proc_3 puts elements of its input stream on a
file called 'result.dat'.

The ouput stream 'out' of proc_2 is connected to the input stream 'in'
of proc_3; see:
         connections=[(proc_2, 'out', proc_3, 'in')]
The input stream 'in' of proc_2 is fed elements of the published stream
called 'publication', see:
           subscribers=[(proc_2, 'in', 'publication')])
If publication consists of [10, 11, ..., 19] then when this VM
terminates, result.dat wil contain [1000, 1100, ..., 1900].

"""
import sys
import os
sys.path.append(os.path.abspath("../multiprocessing"))
sys.path.append(os.path.abspath("../agent_types"))

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
