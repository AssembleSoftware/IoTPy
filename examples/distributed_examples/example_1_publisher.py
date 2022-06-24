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


sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../timing"))

from ../../../multicore import shared_memory_process
from distributed import distributed_process
from VM import VM
from op import map_element
from source import source_func_to_stream
from source import source_list_to_stream

def single_process_publisher():
    source_list = range(10)
    def source(out_stream):
        return source_list_to_stream(
            source_list, out_stream, time_interval=0.2)

    def compute_func(in_streams, out_streams):
        map_element(
            func=lambda x: x,
            in_stream=in_streams[0],
            out_stream=out_streams[0])

    proc_0 = distributed_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=['out'],
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
