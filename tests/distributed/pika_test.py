"""
List of all Pika containing tests moved from multicore_test.py to this file
"""
# Check whether the Python version is 2.x or 3.x
# If it is 2.x import Queue. If 3.x then import queue.
import sys

is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue

import multiprocessing
# multiprocessing.Array provides shared memory that can
# be shared across processes in Python 2+.
import threading
import time
import json
import unittest

# stream is in core
from IoTPy.core.stream import Stream
# sink, op, basics are in the agent_types
from IoTPy.agent_types.sink import stream_to_queue, sink_list
from IoTPy.agent_types.merge import zip_map
from IoTPy.agent_types.op import map_element
from IoTPy.agent_types.iot import iot
from IoTPy.agent_types.basics import map_e, sink_e, f_add
from IoTPy.helper_functions.recent_values import recent_values
#from source import source_func
# from iot import iot
# multicore is in concurrency
from IoTPy.concurrency.multicore import copy_data_to_stream, finished_source
from IoTPy.concurrency.multicore import make_multicore_processes
from IoTPy.concurrency.multicore import get_processes
from IoTPy.concurrency.pika_publication_agent import PikaPublisher
from IoTPy.concurrency.pika_subscribe_agent import PikaSubscriber
# print_stream is in helper_functions
from IoTPy.helper_functions.print_stream import print_stream


class pika_test(unittest.TestCase):

	    #------------------------------------------------------------------
    def test_q_simple_1(self):
        """
        
        """
        # Agent function for process named 'p0'
        print ('starting test_q_simple')

        def f(in_streams, out_streams):
            publisher = PikaPublisher(
                routing_key='temperature',
                exchange='publications', host='localhost')
            sink_list(publisher.publish_list, in_streams[0])

        # Source thread target for source stream named 'x'.
        def h(proc):
            proc.copy_stream(data=list(range(5000, 10000, 1000)), stream_name='x')
            proc.finished_source(stream_name='x')

        # Specification
        multicore_specification = [
            # Streams
            [('x', 'i')],
            # Processes
            [
                # Process p0
                {'name': 'p0', 'agent': f, 'inputs': ['x'],
                 'sources': ['x'], 'source_functions':[h]
                }
            ]
           ]

        # Execute processes (after including your own non IoTPy processes)
        processes = get_processes(multicore_specification)
        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()
        print('')
        print ('--------------------------------------')

            
            #------------------------------------------------------------------
    def test_q_simple(self):
        """
        Illustrates the use of an output queue and use of a non-IoTPy
        thread.
        When the IoTPy processes terminate execution a special message
        '_finished' is put on each of the output queues.
        The non-IoTPy thread, my_thread, gets data from the output queue
        and prints it.

        """
        print ('starting test_q_simple')

        # An output queue of process 'p1'.
        q = multiprocessing.Queue()

        # Agent function for process named 'p0'
        def f(in_streams, out_streams):
            stream_to_queue(in_streams[0], q)

        # Source thread target for source stream named 'x'.
        def h(proc):
            proc.copy_stream(data=list(range(5)), stream_name='x')
            proc.finished_source(stream_name='x')

        # Output thread target
        def publish_data_from_queue(q):
            publisher = PikaPublisher(
                routing_key='temperature',
                exchange='publications', host='localhost')
            while True:
                v = q.get()
                if v == '_finished': break
                else: publisher.publish_list([v])
        # Output thread
        my_thread = threading.Thread(target=publish_data_from_queue, args=(q,))

        # Specification
        multicore_specification = [
            # Streams
            [('x', 'i')],
            # Processes
            [
                # Process p0
                {'name': 'p0', 'agent': f, 'inputs': ['x'],
                 'sources': ['x'], 'source_functions':[h], 'output_queues':[q],
                 'threads': [my_thread]
                }
            ]
           ]

        # Execute processes (after including your own non IoTPy processes)
        processes = get_processes(multicore_specification)
        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print('')
        print ('--------------------------------------')


        #------------------------------------------------------------------
    def test_1_q(self):
        """
        Illustrates the use of an output queue and use of a non-IoTPy
        thread.
        When the IoTPy processes terminate execution a special message
        '_finished' is put on each of the output queues.
        The non-IoTPy thread, my_thread, gets data from the output queue
        and prints it.

        """
        print ('starting test_1_q')

        # An output queue of process 'p1'.
        q = multiprocessing.Queue()

        # Agent function for process named 'p0'
        def f(in_streams, out_streams):
            map_element(lambda v: v+100, in_streams[0], out_streams[0])

        # Agent function for process named 'p1'
        # Puts stream into output queue, q.
        def g(in_streams, out_streams, q):
            s = Stream('s')
            map_element(lambda v: v*2, in_streams[0], s)
            stream_to_queue(s, q)

        # Source thread target for source stream named 'x'.
        def h(proc):
            for i in range(2):
                proc.copy_stream(data=list(range(i*3, (i+1)*3)),
                                 stream_name='x')
                time.sleep(0.001)
            proc.finished_source(stream_name='x')

        # Thread that gets data from the output queue
        # This thread is included in 'threads' in the specification.
        # Thread target
        def publish_data_from_queue(q):
            publisher = PikaPublisher(
                routing_key='temperature',
                exchange='publications', host='localhost')
            finished = False
            while not finished:
                list_to_be_published = []
                while not finished:
                    try:
                        v = q.get(timeout=0.1)
                        if v == '_finished':
                            finished = True
                            if list_to_be_published:
                                publisher.publish_list(list_to_be_published)
                        else:
                            list_to_be_published.append(v)
                    except:
                        print ('from queue: list_to_be_published is ', list_to_be_published)
                        if list_to_be_published:
                            publisher.publish_list(list_to_be_published)
                            list_to_be_published = []
        # Output thread
        my_thread = threading.Thread(target=publish_data_from_queue, args=(q,))

        # Specification
        # Agent function g of process p1 has a positional argument q becauses
        # 'args': [q] is in the specification for p1.
        # q is an output queue because 'output_queues': [q] appears in the spec.
        # When the IoTPy computation terminates, a special message '_finished' is
        # put on each output queue.
        multicore_specification = [
            # Streams
            [('x', 'i'), ('y', 'i')],
            # Processes
            [
                # Process p0
                {'name': 'p0', 'agent': f, 'inputs': ['x'], 'outputs': ['y'],
                 'sources': ['x'], 'source_functions':[h]
                },
                # Process p1
                {'name': 'p1', 'agent': g, 'inputs': ['y'], 'args': [q],
                 'output_queues': [q], 'threads': [my_thread] }
            ]
           ]

        # Execute processes (after including your own non IoTPy processes)
        processes = get_processes(multicore_specification)
        for process in processes: process.start()
        for process in processes: process.join()

        print('')
        print ('--------------------------------------')

if __name__=='__main__':
	unittest.main()
