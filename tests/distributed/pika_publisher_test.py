import time
import threading

import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, run
from IoTPy.concurrency.PikaPublisher import PikaPublisher
# multicore imports
from IoTPy.concurrency.multicore import get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import extend_stream

def test_pika_publisher(routing_key, exchange, host, data):
    # Step 0: Define agent functions, source threads 
    # and actuator threads (if any).

    # Step 0.0: Define agent functions.

    # pika_publisher_agent is the agent for the processor
    # called 'pika_publisher_process'.
    def pika_publisher_agent(in_streams, out_streams):
        # publish in_streams[0] for the specified routing key, exchange, host.
        PikaPublisher(
            routing_key, exchange, host).publish(in_streams[0])

    # Step 0.1: Define source thread targets (if any).
    def thread_target_source(procs):
        for sublist in data:
            extend_stream(procs, sublist, stream_name='source')
            # Sleep to simulate an external data source.
            time.sleep(0.001)
        # Put '_finished' on the stream because the stream will not
        # be extended. This informs subscriber that stream is finished.
        extend_stream(procs, data=['_finished'], stream_name='source')
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


def simple_test():
    """
    A simpler test than test_pika_publisher. This simpler
    test uses 'run' rather than creating a process and thread.

    """
    stream = Stream('stream')
    PikaPublisher(
        routing_key='temperature',
        exchange='publications', host='localhost').publish(stream)
    stream.extend(['Please Vote!'])
    stream.append('_finished')

#--------------------------------------------
# TESTS
#--------------------------------------------
if __name__ == '__main__':
    # Run either the main test or simple_test (but not both).
    # This is some arbitrary data merely for testing.
    # Each sublist of data is published separately.
    data = [[0, 1], ['Hello', 'World'], ['THE', 'END', 'IS', 'NIGH!', '_finished']]
    test_pika_publisher(
        routing_key='temperature', exchange='publications', host='localhost', 
        data=data)
    #simple_test()

