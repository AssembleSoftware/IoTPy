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

#from multicore import shared_memory_process
from distributed import distributed_process
from VM import VM
from op import map_element
#from source import source_func_to_stream
from source import source_list_to_stream

def single_process_publisher():
    # This VM has a single process called proc_0.
    # This process has a single input stream called
    # 'in' and a single output stream called 'out'. See
    # in_stream_names=['in'], out_stream_names=['out'].
    # It has a single source thread which puts elements
    # of source_list into the stream called 'in'. 
    # The process has no actuators, and so connect_actuators
    # is empty. See connect_sources=[('in', source)],
    # connect_actuators=[].
    # The computational thread of this process merely
    # copies its input stream to its output stream (see
    # compute_func.)
    # The process publishes its output stream with the
    # publication name 'copy_of_source_list'. See
    # publishers=[(proc_0, 'out', 'copy_of_source_list')]
    # This VM consists of a single process and so it has
    # no connections to other processes within the same
    # multicore machine; so, connections is the empty list.

    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(
            source_list, out_stream, time_interval=0.01)

    def compute_func(in_streams, out_streams):
        map_element(
            func=lambda x: x,
            in_stream=in_streams[0],
            out_stream=out_streams[0])

    proc_0 = distributed_process(
        compute_func=compute_func,
        in_stream_names=['in'], out_stream_names=['out'],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc_0')

    vm_0 = VM(
        processes=[proc_0],
        connections=[],
        publishers=[(proc_0, 'out', 'copy_of_source_list')])
    vm_0.start()

if __name__ == '__main__':
     single_process_publisher()
