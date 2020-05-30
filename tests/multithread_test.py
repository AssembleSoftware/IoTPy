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
import ntplib
import logging

sys.path.append("../core")
sys.path.append("../agent_types")
sys.path.append("../helper_functions")
sys.path.append("../../examples/timing")
sys.path.append("../concurrency")

#from new import *
from multicore import *
from basics import map_e, map_l, map_w, merge_e,  merge_sink_e
from basics import f_mul, f_add
#from run import run
from stream import StreamArray, run
from multithread import thread_target_extending
from multithread import thread_target_appending
from recent_values import recent_values
from sink import stream_to_queue
from op import map_element
#from run import run

def output_thread_target(q_out, output, finished):
    while True:
        try:
            w = q_out.get()
            if w == finished: break
            else: output.append(w)
        except:
            time.sleep(0.0001)
    
def test_multithread_1_1():

    # Agent functions
    @merge_sink_e
    def f(list_of_elements, q_out):
            q_out.put(sum(list_of_elements))

    @map_e
    def h(a, q_out):
        q_out.put(a)
        return 2*a

    # Streams
    x = Stream('x')
    y = Stream('y')
    u = Stream('u')
    v = Stream('v')

    # Input and output queues
    q_in_1 = queue.Queue()
    q_in_2 = queue.Queue()
    q_out_1 = queue.Queue()
    q_out_2 = queue.Queue()

    # Create agents
    f([x,y], q_out=q_out_1)
    h(u, v, q_out=q_out_2)

    # finished is the message in an output queue that
    # indicates that the IoTPy thread has terminated.
    finished = '_finished'

    # IoTPy thread_1
    iot_thread_1 = threading.Thread(
        target=thread_target_extending,
        args=(q_in_1, [q_out_1], [x, y], finished))

    # IoTPy thread_2
    iot_thread_2 = threading.Thread(
        target=thread_target_extending,
        args=(q_in_2, [q_out_2], [u], finished))

    # Threads to read output queues of IoTPy threads.
    output_1 = []
    output_thread_1 = threading.Thread(
        target=output_thread_target,
        args=(q_out_1, output_1, finished))

    output_2 = []
    output_thread_2 = threading.Thread(
        target=output_thread_target,
        args=(q_out_2, output_2, finished))

    # Start threads
    iot_thread_1.start()
    iot_thread_2.start()
    output_thread_1.start()
    output_thread_2.start()

    # Put data into input queue, q_in_1, of thread_1
    # and input queue, q_in_2 of thread 2.
    x_data = list(range(5))
    y_data = list(range(0, 500, 100))
    q_in_1.put(['x', x_data])
    q_in_1.put(('y', y_data))
    u_data = list(range(1000, 1002))
    q_in_2.put(['u', u_data])

    # Signal input finished for threads
    q_in_1.put(finished)
    q_in_2.put(finished)

    # Join threads
    iot_thread_1.join()
    iot_thread_2.join()
    output_thread_1.join()
    output_thread_2.join()

    # Inspect output of queues and inspect
    # values of streams after thread termination.
    assert output_1 == [0, 101, 202, 303, 404]
    assert output_2 == [1000, 1001]
    assert recent_values(v) == [2000, 2002]


def test_multithread_1():
    @merge_sink_e
    def f(list_of_elements, q_out):
            q_out.put(sum(list_of_elements))

    # Input and output queues
    q_in = queue.Queue()
    q_out = queue.Queue()
    # Streams and agents
    x = Stream('x')
    y = Stream('y')
    in_streams = [x, y]
    f(in_streams, q_out=q_out)
    # Object that indicates stream is finished.
    finished = '_finished'
    output = []

    iot_thread = threading.Thread(
        target=thread_target_appending,
        args=(q_in, [q_out], in_streams))
    
    output_thread = threading.Thread(
        target=output_thread_target,
        args=(q_out, output, finished))

    # Start threads
    iot_thread.start()
    output_thread.start()

    # Put data into input queue
    for i in range(5):
        q_in.put(('x', i))
    for j in range(0, 500, 100):
        q_in.put(('y', j))
    
    q_in.put(finished)

    # Join threads
    output_thread.join()
    iot_thread.join()

    assert output == [0, 101, 202, 303, 404]

#----------------------------------------------------
#  TESTS
#----------------------------------------------------
def test():
    test_multithread_1_1()
    test_multithread_1()

if __name__ == '__main__':
    test()
    print ('Multithread test is successful.')
