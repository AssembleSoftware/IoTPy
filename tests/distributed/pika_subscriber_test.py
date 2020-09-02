"""
You MUST test pika_subscriber_test.py and pika_publisher_test.py
before you use distributed computing with IoTPy.

When you execute:
                   pika_subscriber_test.py
in one terminal window, and execute
                   pika_publisher_test.py argument
in a different terminal window, you shoud see the argument echoed
in the subscriber window.

Look at:
 https://www.rabbitmq.com/tutorials/tutorial-one-python.html

"""
#!/usr/bin/env python
import pika
import json
import threading

import sys
sys.path.append("../")

from IoTPy.helper_functions.print_stream import print_stream

# multicore imports
from IoTPy.concurrency.multicore import get_processes, get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import get_proc_that_inputs_source
from IoTPy.concurrency.multicore import extend_stream
from IoTPy.concurrency.PikaSubscriber import PikaSubscriber

def pika_subscriber_test():
    """
    This function shows how to use Pika to receive a
    stream that was sent using PikaPublisher.

    The pika_receive_agent prints its single input stream.
    The pika_callback_thread receives JSON input (see 'body
    in callback) from Pika and puts the data into a stream
    called 'pika_receive_stream'.

    """
    # Step 0: Define agent functions, source threads 
    # and actuator threads (if any).

    # Step 0.0: Define agent functions.
    def pika_receive_agent(in_streams, out_streams):
        print_stream(in_streams[0], 'x')

    # Step 0.1: Define source thread targets (if any).
    def pika_callback_thread_target(procs):
        def callback(ch, method, properties, body):
            data=json.loads(body)
            print ('data[-1] is ', data[-1])
            if data[-1] == '_finished':
                print ('terminating')
                terminate_stream(procs, stream_name='pika_receive_stream')
                sys.exit()
            else:
                extend_stream(procs, data, stream_name='pika_receive_stream')
        # Declare the Pika subscriber
        pika_subscriber = PikaSubscriber(
            callback, routing_key='temperature',
            exchange='publications', host='localhost')
        pika_subscriber.start()

    # Step 1: multicore_specification of streams and processes.
    # Specify Streams: list of pairs (stream_name, stream_type).
    # Specify Processes: name, agent function, 
    #       lists of inputs and outputs, additional arguments.
    # The pika_receive_stream data type is 'x' for arbitrary.
    multicore_specification = [
        # Streams
        [('pika_receive_stream', 'x')],
        # Processes
        [{'name': 'pika_receive_process', 'agent': pika_receive_agent,
          'inputs':['pika_receive_stream'], 'sources': ['pika_receive_stream']}]]

    # Step 2: Create processes.
    processes, procs = get_processes_and_procs(multicore_specification)

    # Step 3: Create threads (if any)
    pika_callback_thread = threading.Thread(
        target=pika_callback_thread_target, args=(procs,))

    # Step 4: Specify which process each thread runs in.
    # pika_callback_thread runs in the process called 'pika_receive_process'
    procs['pika_receive_process'].threads = [pika_callback_thread]

    # Step 5: Start, join and terminate processes.
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

if __name__ == '__main__':
    pika_subscriber_test()
