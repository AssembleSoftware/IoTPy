"""
This module contains tests:

* offset_estimation_test()
which tests code from multicore.py in multiprocessing.
This module contains tests:

* offset_estimation_test()
which tests code from multicore.py in multiprocessing.

"""

import sys
import threading
import random
import multiprocessing
import numpy as np
import time
import logging
import unittest
import queue
#from new import *
from IoTPy.concurrency.multicore import *
from IoTPy.agent_types.basics import map_e, map_l, map_w, merge_e,  merge_sink_e
from IoTPy.agent_types.basics import f_mul, f_add
#from run import run
from IoTPy.core.stream import StreamArray, run
from IoTPy.concurrency.multithread import thread_target_extending
from IoTPy.concurrency.multithread import thread_target_appending
from IoTPy.concurrency.multithread import iThread
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.agent_types.sink import stream_to_queue
from IoTPy.agent_types.op import map_element
from IoTPy.helper_functions.print_stream import print_stream
#from run import run

class test_multithread(unittest.TestCase):
    def output_thread_target(self, q_out, output):
        while True:
            try:
                w = q_out.get()
                if w == '_finished': break
                else: output.append(w)
            except:
                time.sleep(0.0001)
        
    ## def test_multithread_1_1(self):

    ##     # Agent functions
    ##     @merge_sink_e
    ##     def f(list_of_elements, q_out):
    ##             q_out.put(sum(list_of_elements))

    ##     @map_e
    ##     def h(a, q_out):
    ##         q_out.put(a)
    ##         return 2*a

    ##     # Streams
    ##     x = Stream('x')
    ##     y = Stream('y')
    ##     u = Stream('u')
    ##     v = Stream('v')

    ##     # Input and output queues
    ##     q_in_1 = queue.Queue()
    ##     q_in_2 = queue.Queue()
    ##     q_out_1 = queue.Queue()
    ##     q_out_2 = queue.Queue()

    ##     # Create agents
    ##     f([x,y], q_out=q_out_1)
    ##     h(u, v, q_out=q_out_2)

    ##     # finished is the message in an output queue that
    ##     # indicates that the IoTPy thread has terminated.
    ##     finished = '_finished'

    ##     # IoTPy thread_1
    ##     iot_thread_1 = threading.Thread(
    ##         target=thread_target_extending,
    ##         args=(q_in_1, [q_out_1], [x, y], finished))

    ##     # IoTPy thread_2
    ##     iot_thread_2 = threading.Thread(
    ##         target=thread_target_extending,
    ##         args=(q_in_2, [q_out_2], [u], finished))

    ##     # Threads to read output queues of IoTPy threads.
    ##     output_1 = []
    ##     output_thread_1 = threading.Thread(
    ##         target=self.output_thread_target,
    ##         args=(q_out_1, output_1, finished))

    ##     output_2 = []
    ##     output_thread_2 = threading.Thread(
    ##         target=self.output_thread_target,
    ##         args=(q_out_2, output_2, finished))

    ##     # Start threads
    ##     iot_thread_1.start()
    ##     iot_thread_2.start()
    ##     output_thread_1.start()
    ##     output_thread_2.start()

    ##     # Put data into input queue, q_in_1, of thread_1
    ##     # and input queue, q_in_2 of thread 2.
    ##     x_data = list(range(5))
    ##     y_data = list(range(0, 500, 100))
    ##     q_in_1.put(['x', x_data])
    ##     q_in_1.put(('y', y_data))
    ##     u_data = list(range(1000, 1002))
    ##     q_in_2.put(['u', u_data])

    ##     # Signal input finished for threads
    ##     q_in_1.put(finished)
    ##     q_in_2.put(finished)

    ##     # Join threads
    ##     iot_thread_1.join()
    ##     iot_thread_2.join()
    ##     output_thread_1.join()
    ##     output_thread_2.join()

    ##     # Inspect output of queues and inspect
    ##     # values of streams after thread termination.
    ##     assert output_1 == [0, 101, 202, 303, 404]
    ##     assert output_2 == [1000, 1001]
    ##     assert recent_values(v) == [2000, 2002]


    ## def test_multithread_1(self):
    ##     @merge_sink_e
    ##     def f(list_of_elements, q_out):
    ##             q_out.put(sum(list_of_elements))

    ##     # Input and output queues
    ##     q_in = queue.Queue()
    ##     q_out = queue.Queue()
    ##     # Streams and agents
    ##     x = Stream('x')
    ##     y = Stream('y')
    ##     in_streams = [x, y]
    ##     f(in_streams, q_out=q_out)
    ##     # Object that indicates stream is finished.
    ##     finished = '_finished'
    ##     output = []

    ##     iot_thread = threading.Thread(
    ##         target=thread_target_appending,
    ##         args=(q_in, [q_out], in_streams))
        
    ##     output_thread = threading.Thread(
    ##         target=self.output_thread_target,
    ##         args=(q_out, output, finished))

    ##     # Start threads
    ##     iot_thread.start()
    ##     output_thread.start()

    ##     # Put data into input queue
    ##     for i in range(5):
    ##         q_in.put(('x', i))
    ##     for j in range(0, 500, 100):
    ##         q_in.put(('y', j))
        
    ##     #iot_thread.finished()

    ##     # Join threads
    ##     output_thread.join()
    ##     iot_thread.join()

    ##     assert output == [0, 101, 202, 303, 404]

    def test_multithread_1(self):
        from IoTPy.agent_types.sink import sink_element, stream_to_queue

        # The thread target that reads output queues and puts the results
        # in a list.
        def output_thread_target(self, q_out, output):
            while True:
                try:
                    w = q_out.get()
                    if w == '_finished': break
                    else: output.append(w)
                except:
                    time.sleep(0.0001)

        # Declare output queues
        q_out = queue.Queue()

        # Create threads to read output queues of IoTPy thread.
        output_1 = []
        output_thread = threading.Thread(
            target=self.output_thread_target,
            args=(q_out, output_1))

        # Declare streams
        x = Stream('x')

        # Declare agents
        stream_to_queue(x, q_out)

        # Create thread
        ithread = iThread(in_streams=[x], output_queues=[q_out])

        # Start threads.
        ithread.thread.start()
        output_thread.start()

        # Put data into streams.
        ithread.extend(in_stream_name='x', list_of_elements=list(range(5)))

        # Indicate stream is finished
        ithread.finished()

        # Join threads
        ithread.thread.join()
        output_thread.join()

        # Check output
        assert output_1 == list(range(5))


    def test_multithread_2(self):
        from IoTPy.agent_types.sink import sink_element, stream_to_queue
        from IoTPy.agent_types.merge import zip_map, zip_stream
        from IoTPy.agent_types.op import map_element
        # The thread target that reads output queues and puts the results
        # in a list.
        def output_thread_target(self, q_out, output):
            while True:
                try:
                    w = q_out.get()
                    if w == '_finished': break
                    else: output.append(w)
                except:
                    time.sleep(0.0001)

        # Declare output queues
        q_out_1 = queue.Queue()
        q_out_2 = queue.Queue()

        # Create threads to read output queues of IoTPy thread.
        output_1 = []
        output_1_thread = threading.Thread(
            target=self.output_thread_target,
            args=(q_out_1, output_1))
        
        output_2 = []
        output_2_thread = threading.Thread(
            target=self.output_thread_target,
            args=(q_out_2, output_2))

        # Declare streams
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        a = Stream('a')
        b = Stream('b')

        # Declare agents
        zip_stream(in_streams=[x, y], out_stream=z)
        stream_to_queue(z, q_out_1)

        def g(v): return 2* v
        map_element(func=g, in_stream=a, out_stream=b)
        stream_to_queue(b, q_out_2)

        # Create threads
        ithread_1 = iThread(in_streams=[x,y], output_queues=[q_out_1])
        ithread_2 = iThread(in_streams=[a], output_queues=[q_out_2])
        
        # Start threads.
        ithread_1.start()
        ithread_2.start()
        output_1_thread.start()
        output_2_thread.start()

        # Put data into streams.
        x_data = list(range(5))
        y_data = list(range(100, 105))
        a_data = list(range(1000, 1008))
        ithread_1.extend(in_stream_name='x', list_of_elements=x_data)
        ithread_1.extend(in_stream_name='y', list_of_elements=y_data)
        ithread_2.extend(in_stream_name='a', list_of_elements=a_data)
        

        # Indicate stream is finished
        ithread_1.finished()
        ithread_2.finished()

        # Join threads
        ithread_1.join()
        ithread_2.join()
        output_1_thread.join()
        output_2_thread.join()

        # Check output
        assert output_1 == list(zip(x_data, y_data))
        assert output_2 == [g(v) for v in a_data]
        
        

#----------------------------------------------------
#  TESTS
#----------------------------------------------------
if __name__ == '__main__':
    unittest.main()
