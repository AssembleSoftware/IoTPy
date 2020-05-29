"""
This module is used with VM_publisher_test.py to test
AMQP/pika. Execute
       python VM_publisher_test.py
in one shell and
execute
       python VM_subcriber_test.py
in another shell.

The publisher publishes source_list on a stream called
copy_of_source_list.

The subscriber subscribes to copy_of_source_list and prints
the stream it receives on a file called result.dat.

Start the subscriber an instant before starting the publisher.

For example if source_list is range(10) then the contents of
result.dat after the subscriber terminates will be 0, 1, ..., 9. 

"""

import sys
import os
sys.path.append(os.path.abspath("../multiprocessing"))
sys.path.append(os.path.abspath("../agent_types"))
# distributed and VM are in ../multiprocessing
from distributed import distributed_process
from VM import VM
# sink is in ../agent_types
from sink import stream_to_file

def single_process_subscriber():
    # This VM has a single process called proc_1.
    # This process has a single input stream that we
    # call 'in' and it has no output streams; so
    # out_stream_names is empty. Elements arriving on 
    # the input stream are copied to a file called
    # result.dat (See compute_func.)
    # This process has no source threads that
    # generate data. The input comes only from
    # subscribing to a stream. Because this process
    # has no source threads, connect_sources is
    # empty. Likewise, since it has no actuators,
    # connect_actuators is empty.
    def compute_func(in_streams, out_streams):
        stream_to_file(in_streams[0], 'result.dat')

    proc_1 = distributed_process(
        compute_func=compute_func,
        in_stream_names=['in'], out_stream_names=[],
        connect_sources=[], connect_actuators=[],
        name='proc_1')

    # This VM consists of a single process. So, it has
    # no connections to other processes within the same
    # shared-memory multicore machine.
    # It is a subscriber to a stream called
    #       copy_of_source_list
    # Elements received on this stream are passed to the
    # stream called 'in' inside the process called proc_1.
    vm_1 = VM(
        processes=[proc_1], connections=[],
        subscribers=[(proc_1, 'in', 'copy_of_source_list')])
    
    vm_1.start()

if __name__ == '__main__':
    single_process_subscriber()
