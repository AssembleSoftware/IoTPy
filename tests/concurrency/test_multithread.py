"""
This module contains tests:

* offset_estimation_test()
which tests code from multicore.py in multiprocessing.
This module contains tests:

* offset_estimation_test()
which tests code from multicore.py in multiprocessing.

"""

#import sys
import threading
import random
import multiprocessing
#import numpy as np
#import time
#import logging
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

class test_multithread(unittest.TestCase):
    def output_thread_target(self, q_out, output):
        while True:
            try:
                w = q_out.get()
                if w == '_finished': break
                else: output.append(w)
            except:
                time.sleep(0.0001)

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

        # Declare output queuesq
        x_q = queue.Queue()

        # Create threads to read output queues of IoTPy thread.
        x_output = []
        output_thread = threading.Thread(
            target=self.output_thread_target,
            args=(x_q, x_output))

        # Declare streams
        x = Stream('x')

        # Declare agents
        stream_to_queue(x, x_q)

        # Create thread
        ithread = iThread(in_streams=[x], output_queues=[x_q])

        # Start threads.
        ithread.start()
        output_thread.start()

        # Put data into streams.
        test_data = list(range(5))
        ithread.extend(in_stream_name='x', list_of_elements=test_data)

        # Indicate stream is finished
        ithread.finished()

        # Join threads
        ithread.thread.join()
        output_thread.join()

        # Check output
        assert x_output == test_data


    def test_multithread_2(self):
        from IoTPy.agent_types.sink import sink_element, stream_to_queue
        from IoTPy.agent_types.merge import zip_map, zip_stream
        from IoTPy.agent_types.op import map_element

        # Declare output queues
        z_q = queue.Queue()
        b_q = queue.Queue()

        # Create threads to read output queues of IoTPy thread.
        z_output = []
        z_output_thread = threading.Thread(
            target=self.output_thread_target,
            args=(z_q, z_output))
        
        b_output = []
        b_output_thread = threading.Thread(
            target=self.output_thread_target,
            args=(b_q, b_output))

        # Declare streams
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        a = Stream('a')
        b = Stream('b')

        # Declare agents
        zip_stream(in_streams=[x, y], out_stream=z)
        stream_to_queue(z, z_q)

        def g(v): return 2* v
        map_element(func=g, in_stream=a, out_stream=b)
        stream_to_queue(b, b_q)

        # Create threads
        ithread_1 = iThread(in_streams=[x,y], output_queues=[z_q])
        ithread_2 = iThread(in_streams=[a], output_queues=[b_q])
        
        # Start threads.
        ithread_1.start()
        ithread_2.start()
        z_output_thread.start()
        b_output_thread.start()

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
        z_output_thread.join()
        b_output_thread.join()

        # Check output
        assert z_output == list(zip(x_data, y_data))
        assert b_output == [g(v) for v in a_data]

if __name__ == '__main__':
    unittest.main()
