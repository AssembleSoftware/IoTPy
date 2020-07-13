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
import sys
import json
import threading

from IoTPy.core.agent import Agent
from IoTPy.core.stream import Stream, StreamArray, _no_value, _multivalue, run
from IoTPy.agent_types.sink import sink_list
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.helper_functions.print_stream import print_stream
# multicore imports
from IoTPy.concurrency.multicore import get_processes, get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import get_proc_that_inputs_source
from IoTPy.concurrency.multicore import extend_stream
from IoTPy.concurrency.PikaSubscriber import PikaSubscriber

def pika_subscriber_test():
    # Agent function for process named 'p0'
    def g(in_streams, out_streams):
        print_stream(in_streams[0], 'x')

    # Source thread target for source stream named 'x'.
    def source_thread_target(procs):
        def callback(ch, method, properties, body):
            extend_stream(procs, data=json.loads(body), stream_name='x')

        pika_subscriber = PikaSubscriber(
            callback, routing_key='temperature',
            exchange='publications', host='localhost')

        pika_subscriber.start()

    # The specification
    multicore_specification = [
        # Streams
        [('x', 'i')],
        # Processes
        [{'name': 'p0', 'agent': g, 'inputs':['x'], 'sources': ['x']}]]

    processes, procs = get_processes_and_procs(multicore_specification)
    thread_0 = threading.Thread(target=source_thread_target, args=(procs,))
    procs['p0'].threads = [thread_0]

    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

if __name__ == '__main__':
    pika_subscriber_test()
