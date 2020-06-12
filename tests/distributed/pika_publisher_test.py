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
import time
# stream is in core
from IoTPy.core.stream import Stream, run
# sink, op, basics are in the agent_types
# sink is in agent_types
from IoTPy.agent_types.sink import sink_list
from IoTPy.agent_types.op import map_element
from IoTPy.helper_functions.recent_values import recent_values
# multicore is in concurrency
from IoTPy.concurrency.multicore import copy_data_to_stream, finished_source
from IoTPy.concurrency.multicore import get_processes
#from pika_subscribe_agent import PikaSubscriber
from IoTPy.concurrency.pika_publication_agent import PikaPublisher
# print_stream is in helper_functions
from IoTPy.helper_functions.print_stream import print_stream

publisher = PikaPublisher(
    routing_key='temperature',
    exchange='publications', host='localhost')

def test():
    publisher = PikaPublisher(
        routing_key='temperature',
        exchange='publications', host='localhost')
    x = Stream('x')
    y = Stream('y')
    map_element(lambda v: 2*v, x, y)
    publisher.publish(y)
    for i in range(3):
        x.extend(list(range(i*4, (i+1)*4)))
        run()
        time.sleep(0.001)
    

def pika_publisher_test():
    """
    Simple example

    """
    publisher = PikaPublisher(
        routing_key='temperature',
        exchange='publications', host='localhost')

    # Agent function for process named 'p0'
    def f(in_streams, out_streams):
        print ('in f')
        print ('in_streams[0]')
        #print_stream(in_streams[0], 'x')
        publisher.publish(in_streams[0])
        #publisher.close()

    # Source thread target for source stream named 'x'.
    def h(proc):
        proc.copy_stream(data=list(range(10)), stream_name='x')
        proc.finished_source(stream_name='x')

    # The specification
    multicore_specification = [
        # Streams
        [('x', 'i')],
        # Processes
        [
            # Process p0
            {'name': 'p0', 'agent': f, 'inputs':['x'], 'sources': ['x'],
             'source_functions':[h]}
        ]
       ]

    # Execute processes (after including your own non IoTPy processes)
    processes = get_processes(multicore_specification)
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

if __name__ == '__main__':
    test()
    ## pika_publisher_test()
