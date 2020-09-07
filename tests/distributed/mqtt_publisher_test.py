import time
import json
import threading

import sys
sys.path.append("../")

from IoTPy.helper_functions.print_stream import print_stream
from IoTPy.core.stream import Stream, run
from IoTPy.concurrency.MQTT_Publisher import MQTT_Publisher
# multicore imports
from IoTPy.concurrency.multicore import get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import extend_stream

def mqtt_publisher_test(DATA_TO_PUBLISH):
    # Step 0: Define agent functions and source threads
    # Step 0.0: Define agent functions.
    # This is the agent for the process called mqtt_publish_process.
    def mqtt_publish_agent(in_streams, out_streams):
        MQTT_Publisher(topic='topic', host='localhost').publish(in_streams[0])

    # Step 0.1: Define source threads.
    # This thread puts the data into the stream called 'mqtt_publish_stream'
    # and then terminates the stream.
    def thread_target_source(procs):
        for sublist in DATA_TO_PUBLISH:
            extend_stream(procs, sublist, stream_name='mqtt_publish_stream')
            time.sleep(0.1)
        # Finished. So, put '_finished' in the source stream and terminate it.
        extend_stream(procs, data=['_finished'], stream_name='mqtt_publish_stream')
        terminate_stream(procs, stream_name='mqtt_publish_stream')

    # Step 1: multicore_specification of streams and processes.
    # Specify Streams: list of pairs (stream_name, stream_type).
    # Specify Processes: name, agent function, 
    #       lists of inputs and outputs and sources, and additional arguments.
    multicore_specification = [
        # Streams
        [('mqtt_publish_stream', 'x')],
        # Processes
        [{'name': 'mqtt_publish_process', 'agent': mqtt_publish_agent,
          'inputs':['mqtt_publish_stream'], 'sources': ['mqtt_publish_stream']}]]

    # Step 2: Create processes.
    processes, procs = get_processes_and_procs(multicore_specification)

    # Step 3: Create threads (if any)
    thread_0 = threading.Thread(target=thread_target_source, args=(procs,))

    # Step 4: Specify which process each thread runs in.
    # thread_0 runs in the process called 'p1'
    procs['mqtt_publish_process'].threads = [thread_0]

    # Step 5: Start, join and terminate processes.
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

def simple_test():
    """
    A simpler test than test_mqtt_publisher. This simpler
    test uses 'run' rather than creating a process and thread.

    """
    print ("STARTING")
    stream = Stream('stream')
    MQTT_Publisher(topic='topic', host='localhost').publish(stream)
    stream.append(['a', 'b'])
    stream.append([1, 2])
    stream.append(['x'])
    stream.append('_finished')
    run()

#--------------------------------------------
# TESTS
#--------------------------------------------
if __name__ == '__main__':
    DATA_TO_PUBLISH = [['a', 0], [['c', 'd'], {'e':0, 'f':1}], [list(range(4))]]
    mqtt_publisher_test(DATA_TO_PUBLISH)
    #simple_test()


