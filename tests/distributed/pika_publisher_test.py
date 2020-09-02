import pika
import json
import time
import threading

import sys
sys.path.append("../")
from IoTPy.core.agent import Agent
from IoTPy.core.stream import Stream, StreamArray, _no_value, _multivalue, run
from IoTPy.agent_types.op import map_element
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.helper_functions.print_stream import print_stream
# multicore imports
from IoTPy.concurrency.multicore import get_processes, get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import get_proc_that_inputs_source
from IoTPy.concurrency.multicore import extend_stream
from IoTPy.concurrency.PikaPublisher import PikaPublisher


def test_pika_publisher():
    # Step 0: Define agent functions, source threads 
    # and actuator threads (if any).

    # Step 0.0: Define agent functions.

    # pika_publisher_agent is the agent for the processor
    # called 'pika_publisher_process'.
    def pika_publisher_agent(in_streams, out_streams):
        # publish in_streams[0] for the specified routing key, exchange, host.
        PikaPublisher(
            routing_key='temperature', exchange='publications',
            host='localhost').publish(in_streams[0])

    # Step 0.1: Define source thread targets (if any).
    # This is some arbitrary data merely for testing. In this example
    # the data is a list of lists.
    data = [list(range(5)), list(range(5, 10)), list(range(10, 20))]
    def thread_target_source(procs):
        for sublist in data:
            extend_stream(procs, data=sublist, stream_name='source')
            # Sleep to simulate an external data source.
            time.sleep(0.001)
        # Terminate stream because this stream will not be extended.
        terminate_stream(procs, stream_name='source')

    # Step 1: multicore_specification of streams and processes.
    # Specify Streams: list of pairs (stream_name, stream_type).
    # Specify Processes: name, agent function, 
    #       lists of inputs and outputs, additional arguments.
    multicore_specification = [
        # Streams
        [('source', 'x')],
        # Processes
        [{'name': 'pika_publisher_process', 'agent': pika_publisher_agent, 
          'inputs':['source'], 'sources': ['source']}]]

    # Step 2: Create processes.
    processes, procs = get_processes_and_procs(multicore_specification)

    # Step 3: Create threads (if any)
    thread_0 = threading.Thread(target=thread_target_source, args=(procs,))

    # Step 4: Specify which process each thread runs in.
    # thread_0 runs in the process called 'p1'
    procs['pika_publisher_process'].threads = [thread_0]

    # Step 5: Start, join and terminate processes.
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

def test():
    """
    A simpler test than test_pika_publisher. This simpler
    test uses 'run' rather than creating a process and thread.

    """
    publisher = PikaPublisher(
        routing_key='temperature',
        exchange='publications', host='localhost')
    x = Stream('x')
    y = Stream('y')
    map_element(lambda v: 10*v, x, y)
    publisher.publish(y)
    for i in range(3):
        x.extend(list(range(i*4, (i+1)*4)))
        run()
        time.sleep(0.001)

#--------------------------------------------
# TESTS
#--------------------------------------------
test()
test_pika_publisher()

