"""
This module makes processes for a multicore application.
It uses multiprocessing.Array to enable multiple processes to
share access to streams efficiently.
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
import numpy as np

import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, StreamArray, run, _no_value
from IoTPy.agent_types.op import map_element, map_list, map_window
from IoTPy.agent_types.merge import zip_map
from IoTPy.agent_types.sink import stream_to_queue
from IoTPy.agent_types.basics import map_e, sink_e
# helper_functions imports
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.helper_functions.print_stream import print_stream
from IoTPy.helper_functions.type import dtype_float
# multicore imports
from IoTPy.concurrency.multicore import get_processes, get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import get_proc_that_inputs_source
from IoTPy.concurrency.multicore import extend_stream


class test_multicore(unittest.TestCase):
    #------------------------------------------------------------------

    def test_simple_multicore(self):

        print (' ')
        print ('starting test_simple_multicore')
        print (' ')

        def f(in_streams, out_streams):
                map_element(lambda v: v+100, in_streams[0], out_streams[0])

        def g(in_streams, out_streams):
            s = Stream('s')
            map_element(lambda v: v*2, in_streams[0], s)
            print_stream(s, 's')

        def h(in_streams, out_streams):
            map_element(lambda v: v*2, in_streams[0], out_streams[0])

        def r(in_streams, out_streams):
            t = Stream('t')
            map_element(lambda v: v*3, in_streams[0], t)
            print_stream(t, 't')

        def source_thread_target(procs):
            for i in range(3):
                extend_stream(procs, data=list(range(i*2, (i+1)*2)), stream_name='x')
                time.sleep(0.001)
            terminate_stream(procs, stream_name='x')

        multicore_specification = [
        # Streams
        [('x', 'i'), ('y', 'i')],
        # Processes
        [{'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y'], 'sources':['x']},
         {'name': 'p1', 'agent': g, 'inputs': ['y']}]]

        processes, procs = get_processes_and_procs(multicore_specification)
        thread_0 = threading.Thread(target=source_thread_target, args=(procs,))
        procs['p1'].threads = [thread_0]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')
        print ('finished test_simple_multicore')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_simple_multicore_source_thread_switched(self):
        print(' ')
        print ('starting test_simple_multicore_source_thread_switched')
        print (' ')

        def f(in_streams, out_streams):
                map_element(lambda v: v+100, in_streams[0], out_streams[0])

        def g(in_streams, out_streams):
            s = Stream('s')
            map_element(lambda v: v*2, in_streams[0], s)
            print_stream(s, 's')

        def h(in_streams, out_streams):
            map_element(lambda v: v*2, in_streams[0], out_streams[0])

        def r(in_streams, out_streams):
            t = Stream('t')
            map_element(lambda v: v*3, in_streams[0], t)
            print_stream(t, 't')

        def source_thread_target(procs):
            for i in range(3):
                extend_stream(procs, data=list(range(i*2, (i+1)*2)), stream_name='x')
                time.sleep(0.001)
            terminate_stream(procs, stream_name='x')

        multicore_specification = [
        # Streams
        [('x', 'i'), ('y', 'i')],
        # Processes
        [{'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y']},
         {'name': 'p1', 'agent': g, 'inputs': ['y'], 'sources':['x']}]]

        processes, procs = get_processes_and_procs(multicore_specification)
        thread_0 = threading.Thread(target=source_thread_target, args=(procs,))
        procs['p1'].threads = [thread_0]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')

        print (' ')
        print ('finished test_simple_multicore_source_thread_switched')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_multicore_three_processes_in_a_row(self):
        print (' ')
        print ('starting test_multicore_three_processes_in_a_row')
        print (' ')

        def f(in_streams, out_streams):
                map_element(lambda v: v+100, in_streams[0], out_streams[0])

        def g(in_streams, out_streams):
            s = Stream('s')
            map_element(lambda v: v*2, in_streams[0], s)
            print_stream(s, 's')

        def h(in_streams, out_streams):
            map_element(lambda v: v*2, in_streams[0], out_streams[0])

        def r(in_streams, out_streams):
            t = Stream('t')
            map_element(lambda v: v*3, in_streams[0], t)
            print_stream(t, 't')

        def source_thread_target(procs):
            for i in range(3):
                extend_stream(procs, data=list(range(i*2, (i+1)*2)), stream_name='x')
                time.sleep(0.001)
            terminate_stream(procs, stream_name='x')

        multicore_specification = [
            # Streams
            [('x', 'i'), ('y', 'i'), ('z', 'i')],
            # Processes
            [{'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y']},
             {'name': 'p1', 'agent': h, 'inputs': ['y'], 'outputs': ['z'], 'sources': ['x']},
             {'name': 'p2', 'agent': r, 'inputs': ['z']}]
            ]

        processes, procs = get_processes_and_procs(multicore_specification)
        thread_0 = threading.Thread(target=source_thread_target, args=(procs,))
        procs['p1'].threads = [thread_0]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')
        print ('finished test_multicore_three_processes_in_a_row')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_multicore_with_arrays(self):

        print (' ')
        print ('starting test_multicore_with_arrays')
        print (' ')

        def f_numpy(in_streams, out_streams):
            map_window(np.mean, dtype_float(in_streams[0]), out_streams[0], window_size=2, step_size=2)

        def g_numpy(in_streams, out_streams):
            t = StreamArray('t')
            map_window(max, dtype_float(in_streams[0]), t, window_size=2, step_size=2)
            print_stream(t, 't')

        def thread_target_numpy(procs):
            for i in range(3):
                extend_stream(procs, data=list(range(i*10, (i+1)*10)), stream_name='x')
                time.sleep(0.001)
            terminate_stream(procs, stream_name='x')

        multicore_specification = [
            # Streams
            [('x', 'i'), ('y', 'f')],
            # Processes
            [{'name': 'p0', 'agent': f_numpy, 'inputs':['x'], 'outputs': ['y'], 'sources': ['x']},
             {'name': 'p1', 'agent': g_numpy, 'inputs': ['y']}]
        ]

        processes, procs = get_processes_and_procs(multicore_specification)
        thread_0 = threading.Thread(target=thread_target_numpy, args=(procs,))
        procs['p1'].threads = [thread_0]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')
        print ('finished test_multicore_with_arrays')
        print (' ')


#--------------------------------------------------------------------------------------------

    def test_example_merging_streams_from_multiple_processes(self):

        print (' ')
        print ('starting test_example_merging_streams_from_multiple_processes')
        print (' ')

        def sine(in_streams, out_streams):
            map_element(np.sin, dtype_float(in_streams[0]), out_streams[0], name='sine')

        def cosine(in_streams, out_streams):
            map_element(np.cos, dtype_float(in_streams[0]), out_streams[0], name='cosine')

        def tangent(in_streams, out_streams):
            map_element(np.tan, dtype_float(in_streams[0]), out_streams[0], name='tangent')

        def coordinate(in_streams, out_streams):
            x, sines, cosines, tangents = in_streams

            def f(lst): return lst[0]/lst[1]

            def g(lst):
                error_squared= (lst[0] - lst[1])**2
                return error_squared

            ratios = Stream('ratios')
            errors = Stream('errors')
            zip_map(f, [sines, cosines], ratios, name='sine / cosine')
            zip_map(g, [ratios, tangents], errors, name='compute error')
            print_stream(errors, 'error')

        # Source thread target.
        def source_thread_target(procs):
            extend_stream(procs, data = np.linspace(0.0, np.pi, 10), stream_name='x')
            terminate_stream(procs, stream_name='x')

        multicore_specification = [
            # Streams
            [('x', 'f'), ('sines', 'f'), ('cosines', 'f'), ('tangents', 'f')],
            # Processes
            [{'name': 'sine', 'agent': sine, 'inputs':['x'], 'outputs': ['sines']},
             {'name': 'cosine', 'agent': cosine, 'inputs':['x'], 'outputs': ['cosines']},
             {'name': 'tanget', 'agent': tangent, 'inputs':['x'], 'outputs': ['tangents']},
             {'name': 'coordinator', 'agent': coordinate, 'inputs':['x', 'sines', 'cosines', 'tangents'],
              'sources': ['x']}]
        ]

        processes, procs = get_processes_and_procs(multicore_specification)
        thread_0 = threading.Thread(target=source_thread_target, args=(procs,))
        procs['coordinator'].threads = [thread_0]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')
        print ('finished test_example_merging_streams_from_multiple_processes')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_example_passing_data_to_multicore(self):

        print (' ')
        print ('starting test_example_passing_data_to_multicore')
        print (' ')

        total = multiprocessing.Value('f')
        num = multiprocessing.Value('i')
        # Values computed from an earlier computation which is not shown.
        # total and num are passed to the multiprocessing block.
        total.value = 4.0e-13
        num.value = 25

        def sine(in_streams, out_streams):
            map_element(np.sin, dtype_float(in_streams[0]), out_streams[0], name='sine')

        def cosine(in_streams, out_streams):
            map_element(np.cos, dtype_float(in_streams[0]), out_streams[0], name='cosine')

        def tangent(in_streams, out_streams):
            map_element(np.tan, dtype_float(in_streams[0]), out_streams[0], name='tangent')

        def coordinate(in_streams, out_streams, total, num):
            x, sines, cosines, tangents = in_streams

            def f(lst): return lst[0]/lst[1]

            def g(lst):
                error_squared= (lst[0] - lst[1])**2
                return error_squared

            ratios = Stream('ratios')
            errors = Stream('errors')
            zip_map(f, [sines, cosines], ratios, name='sine / cosine')
            zip_map(g, [ratios, tangents], errors, name='compute error')
            print_stream(errors, 'error')

        # Source thread target.
        def source_thread_target(procs):
            extend_stream(procs, data=np.linspace(0.0, np.pi, 10), stream_name='x')
            terminate_stream(procs, stream_name='x')

        multicore_specification = [
            # Streams
            [('x', 'f'), ('sines', 'f'), ('cosines', 'f'), ('tangents', 'f')],
            # Processes
            [{'name': 'sine', 'agent': sine, 'inputs':['x'], 'outputs': ['sines']},
             {'name': 'cosine', 'agent': cosine, 'inputs':['x'], 'outputs': ['cosines']},
             {'name': 'tanget', 'agent': tangent, 'inputs':['x'], 'outputs': ['tangents']},
             {'name': 'coordinator', 'agent': coordinate, 'inputs':['x', 'sines', 'cosines', 'tangents'],
              'sources': ['x'], 'keyword_args' : {'total' : total, 'num' : num}}]
        ]

        processes, procs = get_processes_and_procs(multicore_specification)
        thread_0 = threading.Thread(target=source_thread_target, args=(procs,))
        procs['coordinator'].threads = [thread_0]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')
        print ('finished test_example_passing_data_to_multicore')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_example_output_thread_with_queue(self):

        print (' ')
        print ('starting test_example_output_thread_with_queue')
        print (' ')

        q = multiprocessing.Queue()

        def f(in_streams, out_streams):
                map_element(lambda v: v+100, in_streams[0], out_streams[0])

        def g(in_streams, out_streams, q):
            s = Stream('s')
            map_element(lambda v: v*2, in_streams[0], s)
            stream_to_queue(s, q, name='copy_stream_s_to_queue_q')

        def source_thread_target(procs):
            for i in range(3):
                extend_stream(procs, data=list(range(i*2, (i+1)*2)), stream_name='x')
                time.sleep(0.001)
            terminate_stream(procs, stream_name='x')

        def get_data_from_output_queue(q):
            while True:
                v = q.get()
                if v == '_finished': break
                else: print ('q.get() = ', v)

        multicore_specification = [
            # Streams
            [('x', 'i'), ('y', 'i')],
            # Processes
            [{'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y'], 'sources': ['x']},
             {'name': 'p1', 'agent': g, 'inputs': ['y'], 
              'args': [q], 'output_queues': [q]}]
        ]

        processes, procs = get_processes_and_procs(multicore_specification)
        source_thread = threading.Thread(target=source_thread_target, args=(procs,))
        output_thread = threading.Thread(target=get_data_from_output_queue, args=(q,))
        procs['p0'].threads = [source_thread, output_thread]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')
        print ('finished test_example_output_thread_with_queue')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_example_echo_two_cores(self):

        print (' ')
        print ('starting test_example_echo_two_cores')
        print (' ')

        # This is the delay from when the made sound hits a
        # reflecting surface.
        delay = 4

        # This is the attenuation of the reflected wave.
        attenuation = 0.5

        # The results are put in this queue. A thread reads this
        # queue and feeds a speaker or headphone.
        q = multiprocessing.Queue()

        # Agent function for process named 'p0'
        # echo is a delay of zeroes followed by attenuated heard sound.
        # out_streams[0], which is the same as sound_heard is
        # echo + sound_made
        def f_echo(in_streams, out_streams, delay):
            sound_made, attenuated = in_streams
            echo = Stream('echo')
            echo.extend([0] * delay)
            map_element(lambda v: v, attenuated, echo)
            # The zip_map output is the sound heard which is
            # the sound heard plus the echo.
            zip_map(sum, [sound_made, echo], out_streams[0])

        # Agent function for process named 'p1'
        # This process puts the sound heard into the output queue
        # and returns an attenuated version of the sound_heard as 
        # its output stream.
        def g_echo(in_streams, out_streams, attenuation, q):
            def gg(v):
                # v is the sound heard
                q.put(v)
                # v*attenuation is the echo
                return v*attenuation
            map_element(gg, in_streams[0], out_streams[0])

        def source_thread_target(procs):
            data=list(range(10))
            extend_stream(procs, data=list(range(10)), stream_name='sound_made')
            time.sleep(0.0001)
            extend_stream(procs, data=[0]*10, stream_name='sound_made')
            terminate_stream(procs, stream_name='sound_made')

        # Thread that gets data from the output queue
        # This thread is included in 'threads' in the specification.
        # Thread target
        def get_data_from_output_queue(q):
            finished_getting_output = False
            while not finished_getting_output:
                v = q.get()
                if v == '_finished': break
                print ('heard sound = spoken + echo: ', v)

        multicore_specification = [
            # Streams
            [('sound_made', 'f'), ('attenuated', 'f'), ('sound_heard', 'f')],
            # Processes
            [{'name': 'p0', 'agent': f_echo, 'inputs': ['sound_made', 'attenuated'], 
              'outputs': ['sound_heard'], 'keyword_args' : {'delay' : delay}, 'sources': ['sound_made']},
             {'name': 'p1', 'agent': g_echo, 'inputs': ['sound_heard'], 'outputs': ['attenuated'],
              'args': [attenuation, q], 'output_queues': [q] } ]]

        processes, procs = get_processes_and_procs(multicore_specification)

        source_thread = threading.Thread(target=source_thread_target, args=(procs,))
        output_thread = threading.Thread(target=get_data_from_output_queue, args=(q,))
        procs['p0'].threads = [source_thread, output_thread]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')
        print ('finished test_example_echo_two_cores')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_example_echo_single_core(self):

        print (' ')
        print ('starting test_example_echo_single_core')
        print (' ')

        # This is the delay from when the made sound hits a
        # reflecting surface.
        delay = 4

        # This is the attenuation of the reflected wave.
        attenuation = 0.5

        # The results are put in this queue. A thread reads this
        # queue and feeds a speaker or headphone.
        q = multiprocessing.Queue()

        # Agent function for process named 'p0'
        def f_echo(in_streams, out_streams, delay, attenuation, q):
            echo = StreamArray(
                'echo', initial_value=np.array([0.0]*delay, dtype='float'), dtype='float')
            #Note: sound_made = in_streams[0]
            sound_heard = in_streams[0] + echo
            map_element(lambda v: v*attenuation, sound_heard, echo)
            stream_to_queue(sound_heard, q)

        def source_thread_target(procs):
            extend_stream(procs, data=np.arange(10, dtype='float'), stream_name='sound_made')
            time.sleep(0.0001)
            extend_stream(procs=procs, data=np.zeros(10, dtype='float'), stream_name='sound_made')
            terminate_stream(procs, stream_name='sound_made')

        # Thread that gets data from the output queue
        # This thread is included in 'threads' in the specification.
        # Thread target
        def get_data_from_output_queue(q):
            finished_getting_output = False
            while not finished_getting_output:
                v = q.get()
                if v == '_finished': break
                print ('heard sound = spoken + echo: ', v)

        multicore_specification = [
            # Streams
            [('sound_made', 'f')],
            # Processes
            [{'name': 'p0', 'agent': f_echo, 'inputs': ['sound_made'],
              'args' : [delay, attenuation, q], 'sources': ['sound_made'],'output_queues': [q]}]]

        processes, procs = get_processes_and_procs(multicore_specification)

        source_thread = threading.Thread(target=source_thread_target, args=(procs,))
        output_thread = threading.Thread(target=get_data_from_output_queue, args=(q,))
        procs['p0'].threads = [source_thread, output_thread]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')
        print ('finished test_example_echo_single_core')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_simple_grid(self):

        print (' ')
        print ('starting test_simple_grid')
        print (' ')

        # N is the size of the grid
        N = 5
        # M is the number of steps of execution.
        M = 5
        # DELTA is the deviation from the final solution.
        DELTA = 0.01
        # even, odd are the grids that will be returned
        # by this computation
        even = multiprocessing.Array('f', N)
        odd = multiprocessing.Array('f', N)
        # Set up initial values of the grid.
        for i in range(1, N-1):
            even[i] = i + DELTA
        even[N-1] = N-1
        odd[N-1] = N-1

        def f(in_streams, out_streams, index, even, odd):
            def g(v):
                if (0 < index) and (index < N-1):
                    if v%2 == 0:
                        odd[index] = (even[index-1] + even[index] + even[index+1])/3.0
                    else:
                        even[index] = (odd[index-1] + odd[index] + odd[index+1])/3.0
                return v+1

            def r(lst, state):
                if state < M:
                    return lst[0], state+1
                else:
                    return _no_value, state
            for out_stream in out_streams: out_stream.extend([0])
            synch_stream = Stream('synch_stream')
            zip_map(r, in_streams, synch_stream, state=0, name='zip_map_'+str(index))
            map_element(g, synch_stream, out_streams[0], name='grid'+str(index))
            run()

        multicore_specification = [
            # Streams
            [('s_'+str(index), 'i') for index in range(1, N-1)],
            # Processes
            [{'name': 'grid_'+str(index), 'agent': f, 
              'inputs':['s_'+str(index+1), 's_'+str(index-1)], 
              'outputs':['s_'+str(index)], 
              'args': [index, even, odd]} for index in range(2, N-2)] + \
            [{'name': 'grid_'+str(1), 'agent': f, 
              'inputs':['s_'+str(2)], 'outputs':['s_'+str(1)], 
              'args': [1, even, odd]}] + \
            [{'name': 'grid_'+str(N-2), 'agent': f, 
              'inputs':['s_'+str(N-3)], 'outputs':['s_'+str(N-2)], 
              'args': [N-2, even, odd]}]
        ]

        # Execute processes (after including your own non IoTPy processes)
        processes = get_processes(multicore_specification)
        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print ('Grid after ', M, ' steps is: ')
        if M%2 == 0:
            print (even[:])
        else:
            print (odd[:])

            print (' ')
            print ('finished test_simple_grid')
            print (' ')

#--------------------------------------------------------------------------------------------

    def test_parameter(self, ADDEND_VALUE=500):
        """
        Illustrates the use of args which is also illustrated in test_1.
        This example is a small modification of test_0_0.

        """

        print (' ')
        print ('starting test_parameter')
        print (' ')
        # Agent function for process named 'p0'
        # ADDEND is a positional argument of f in the spec for p0.

        def f(in_streams, out_streams, ADDEND):
            map_element(lambda v: v+ADDEND, in_streams[0], out_streams[0])

        # Agent function for process named 'p1'
        def g(in_streams, out_streams):
            s = Stream('s')
            map_element(lambda v: v*2, in_streams[0], s)
            print_stream(s, 's')

        def source_thread_target(procs):
            for i in range(3):
                extend_stream(procs, data=list(range(i*2, (i+1)*2)), stream_name='x')
                time.sleep(0.001)
            terminate_stream(procs, stream_name='x')

        multicore_specification = [
            # Streams
            [('x', 'i'), ('y', 'i')],
            # Processes
            [{'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y'],
              'args': [ADDEND_VALUE], 'sources': ['x']},
            {'name': 'p1', 'agent': g, 'inputs': ['y'] }]]

        processes, procs = get_processes_and_procs(multicore_specification)
        source_thread = threading.Thread(target=source_thread_target, args=(procs,))
        procs['p0'].threads = [source_thread]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        print (' ')
        print ('finished test_parameter')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_parameter_result(self):
        """
        This example illustrates how you can get results from IoTPy processes when the
        processes terminate. The results are stored in a buffer (a multiprocessing.Array)
        which your non-IoTPy code can read. You can insert data into the IoTPy processes
        continuously or before the processes are started.

        In this example output_buffer[j] = 0 + 1 + 2 + ... + j

        """
        print ('starting test_parameter_result')
        print ('')
        print ('Output stream s and output_buffer.')
        print ('output_buffer is [0, 1, 3, 6, 10, .., 45]')
        print ('s[j] = output_buffer[j] + 100')
        print ('')

        # The results of the parallel computation are stored in output_buffer.
        output_buffer = multiprocessing.Array('i', 20)
        # The results are in output_buffer[:output_buffer_ptr]
        output_buffer_ptr = multiprocessing.Value('i', 0)

        # In this example v represents an element of an input stream.
        # sum is the sum of all the stream-element values received
        # by the agent. The state of the agent is sum.
        # output_buffer and output_buffer_ptr are keyword arguments.
        @map_e
        def ff(v, sum, output_buffer, output_buffer_ptr):
            sum += v
            output_buffer[output_buffer_ptr.value] = sum
            output_buffer_ptr.value +=1
            return sum, sum

        # Agent function for process named 'p0'
        def f(in_streams, out_streams, output_buffer, output_buffer_ptr):
            ff(in_streams[0], out_streams[0], state=0,
               output_buffer=output_buffer, output_buffer_ptr=output_buffer_ptr)

        # Agent function for process named 'p1'
        def g(in_streams, out_streams):
            s = Stream('s')
            map_element(lambda v: v*2, in_streams[0], s)
            print_stream(s, 's')

        # Source thread target for source stream named 'x'.

        def source_thread_target(procs):
            for i in range(3):
                extend_stream(procs, data=list(range(i*2, (i+1)*2)), stream_name='x')
                time.sleep(0.001)
            terminate_stream(procs, stream_name='x')

        # Specification
        multicore_specification = [
            # Streams
            [('x', 'i'), ('y', 'i')],
            # Processes
            [{'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y'],
              'keyword_args' : {'output_buffer' : output_buffer,
                                'output_buffer_ptr' : output_buffer_ptr}, 'sources': ['x'] },
            {'name': 'p1', 'agent': g, 'inputs': ['y'], } ]]

        # Execute processes (after including your own non IoTPy processes)

        processes, procs = get_processes_and_procs(multicore_specification)
        source_thread = threading.Thread(target=source_thread_target, args=(procs,))
        procs['p0'].threads = [source_thread]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()

        # Verify that output_buffer can be read by the parent process.
        print ('output_buffer is ', output_buffer[:output_buffer_ptr.value])
        print('')

        print (' ')
        print ('finished test_parameter_result')
        print (' ')

#--------------------------------------------------------------------------------------------

    def test_example_parameters_with_queue(
            self, DATA=list(range(4)), ADDEND=10, MULTIPLICAND=3, EXPONENT=2):
        """
        This example illustrates integrating processes running non-IoTPy
        code with processes running IoTPy. The example shows how
        results generated by IoTPy processes are obtained continuously
        by non-IoTPy processes through queues. The example also shows
        how results computed by IoTPy processes are returned to
        the non-IoTPy calling process when the IoTPy processes terminate

        In this simple example,
        (s[j]+ADDEND)*MULTIPLICAND is the j-th value put in the queue, and
        (s[j]+ADDEND)**EXPONENT is the j-th element of the buffer returned
        by the multiprocess computation.

        """

        print (' ')
        print ('starting test_example_parameters_with_queue')
        print (' ')
        # Values generated continuously by the IoTPy process are read by
        # the calling non-IoTPy process using this queue.
        q = multiprocessing.Queue()

        # The results of the parallel computation are stored in buffer.
        buffer = multiprocessing.Array('f', 10)
        # The results are in buffer[:ptr].
        # The values in buffer[ptr:] are arbitrary
        ptr = multiprocessing.Value('i', 0)

        # The computational function for process p0.
        # Arguments are: in_streams, out_streams, and additional
        # arguments. Here ADDEND is an additional argument.
        def f(in_streams, out_streams, ADDEND):
            map_element(lambda a: a+ADDEND, in_streams[0], out_streams[0])

        # The computational function for process p1
        def g(in_streams, out_streams, MULTIPLICAND, EXPONENT, q, buffer, ptr):
            @sink_e
            def h(v):
                q.put(v*MULTIPLICAND)
                buffer[ptr.value] = v**EXPONENT
                ptr.value += 1
            h(in_streams[0])

        def source_thread_target(procs):
            extend_stream(procs, data=DATA, stream_name='data')
            terminate_stream(procs, stream_name='data')

        multicore_specification = [
            # Streams
            [('data', 'f'), ('result', 'f')],
            # Processes
            [{'name': 'p0', 'agent': f, 'inputs': ['data'], 'outputs': ['result'],
              'args' : [ADDEND], 'sources': ['data']},
             {'name': 'p1', 'agent': g, 'inputs': ['result'],
              'args': [MULTIPLICAND, EXPONENT, q, buffer, ptr], 'output_queues': [q] } ]]

        processes, procs = get_processes_and_procs(multicore_specification)
        source_thread = threading.Thread(target=source_thread_target, args=(procs,))
        procs['p0'].threads = [source_thread]

        for process in processes: process.start()
        for process in processes: process.join()
        for process in processes: process.terminate()
        print ('TERMINATED')
        

        def get_data_from_output_queue(q):
            queue_index = 0
            while True:
                v = q.get()
                if v == '_finished': break
                else:
                    print ('q.get(', queue_index, ') = ', v)
                    queue_index += 1

        get_data_from_output_queue(q)
        # finished_source indicates that this source is finished. No more data will be sent on the
        # stream called stream_name ('data') in the process with the specified name ('p0').
        ## queue_index = 0
        ## finished_getting_output = False
        ## while not finished_getting_output:
        ##     element_from_queue = q.get()
        ##     print ('element_from_queue is ', element_from_queue)
        ##     print ('queue[', queue_index, '] = ', element_from_queue)
        ##     queue_index += 1
        ##     if element_from_queue == '_finished':
        ##         print ('element_from_queue is finished')
        ##         finished_getting_output = True
        ##         break

        # Get the results returned in the buffer.
        print ('buffer is ', buffer[:ptr.value])

        print (' ')
        print ('finished test_example_parameters_with_queue')
        print (' ')

if __name__ == '__main__':
    unittest.main()
