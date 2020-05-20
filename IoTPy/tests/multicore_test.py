"""
This module makes processes for a multicore application.
It uses multiprocessing.Array to enable multiple processes to
share access to streams efficiently.
"""
import sys
import os
# Check whether the Python version is 2.x or 3.x
# If it is 2.x import Queue. If 3.x then import queue.
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
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../concurrency"))

# stream is in core
from stream import Stream
# sink, op, basics are in the agent_types
from sink import stream_to_queue, sink_list
from merge import zip_map
from op import map_element
from iot import iot
from basics import map_e, sink_e, f_add
from recent_values import recent_values
#from source import source_func
from iot import iot
# multicore is in concurrency
from multicore import copy_data_to_stream, finished_source
from multicore import make_multicore_processes
from multicore import get_processes
from pika_publication_agent import PikaPublisher
from pika_subscribe_agent import PikaSubscriber
# print_stream is in helper_functions
from print_stream import print_stream

#------------------------------------------------------------------
def test_pika_subscriber():
    """
    Simple example

    """
    # Agent function for process named 'p0'
    def f(in_streams, out_streams):
        print_stream(in_streams[0], 'x')

    # Source thread target for source stream named 'x'.
    def h(proc):
        def callback(ch, method, properties, body):
            json_data = json.loads(body)
            proc.copy_stream(data=json_data, stream_name='x')
        pika_subscriber = PikaSubscriber(
            callback, routing_key='temperature',
            exchange='publications', host='localhost')
        pika_subscriber.start()


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


def test_0_0():
    """
    Simple example

    """
    # Agent function for process named 'p0'
    def f(in_streams, out_streams):
        map_element(lambda v: v+100, in_streams[0], out_streams[0])

    # Agent function for process named 'p1'
    def g(in_streams, out_streams):
        s = Stream('s')
        map_element(lambda v: v*2, in_streams[0], s)
        print_stream(s, 's')

    # Source thread target for source stream named 'x'.
    def h(proc):
        for i in range(2):
            proc.copy_stream(data=list(range(i*3, (i+1)*3)),
                             stream_name='x')
            time.sleep(0.001)
        proc.finished_source(stream_name='x')

    # The specification
    multicore_specification = [
        # Streams
        [('x', 'i'), ('y', 'i')],
        # Processes
        [
            # Process p0
            {'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y'], 'sources': ['x'],
             'source_functions':[h]},
            # Process p1
            {'name': 'p1', 'agent': g, 'inputs': ['y']}
        ]
       ]

    # Execute processes (after including your own non IoTPy processes)
    processes = get_processes(multicore_specification)
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

#------------------------------------------------------------------
def test_0_1():
    """
    Same as test_0_0 except that in this example the source is
    in process p1 and the source stream is read by process p0,
    whereas in test_0_0 the source is in process p0.

    """
    # Agent function for process named 'p0'
    def f(in_streams, out_streams):
        map_element(lambda v: v+100, in_streams[0], out_streams[0])

    # Agent function for process named 'p1'
    def g(in_streams, out_streams):
        s = Stream('s')
        map_element(lambda v: v*2, in_streams[0], s)
        print_stream(s, 's')

    # Source thread target for source stream named 'x'.
    def h(proc):
        for i in range(2):
            proc.copy_stream(data=list(range(i*3, (i+1)*3)),
                             stream_name='x')
            time.sleep(0.001)
        proc.finished_source(stream_name='x')

    # Specification
    multicore_specification = [
        # Streams
        [('x', 'i'), ('y', 'i')],
        # Processes
        [
            # Process p0
            {'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y']},
            # Process p1
            {'name': 'p1', 'agent': g, 'inputs': ['y'], 'sources': ['x'],
             'source_functions':[h]}
        ]
       ]

    # Execute processes (after including your own non IoTPy processes)
    processes = get_processes(multicore_specification)
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()


#------------------------------------------------------------------
def test_q_simple():
    """
    Illustrates the use of an output queue and use of a non-IoTPy
    thread.
    When the IoTPy processes terminate execution a special message
    '_finished' is put on each of the output queues.
    The non-IoTPy thread, my_thread, gets data from the output queue
    and prints it.

    """

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


#------------------------------------------------------------------
def test_q_simple_1():
    """

    """
    # Agent function for process named 'p0'
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

        

#------------------------------------------------------------------
def test_1_q():
    """
    Illustrates the use of an output queue and use of a non-IoTPy
    thread.
    When the IoTPy processes terminate execution a special message
    '_finished' is put on each of the output queues.
    The non-IoTPy thread, my_thread, gets data from the output queue
    and prints it.

    """

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

    

#------------------------------------------------------------------
def test_1():
    """
    Illustrates the use of an output queue and use of a non-IoTPy
    thread.
    When the IoTPy processes terminate execution a special message
    '_finished' is put on each of the output queues.
    The non-IoTPy thread, my_thread, gets data from the output queue
    and prints it.

    """
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
    def get_data_from_output_queue(q):
        while True:
            v = q.get()
            if v == '_finished':
                break
            print ('from queue: ', v)
    # Thread
    my_thread = threading.Thread(target=get_data_from_output_queue, args=(q,))

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
    for process in processes: process.terminate()

    
def test_parameter(ADDEND_VALUE):
    """
    Illustrates the use of args which is also illustrated in test_1.
    This example is a small modification of test_0_0.

    """
    # Agent function for process named 'p0'
    # ADDEND is a positional argument of f in the spec for p0.
    def f(in_streams, out_streams, ADDEND):
        map_element(lambda v: v+ADDEND, in_streams[0], out_streams[0])

    # Agent function for process named 'p1'
    def g(in_streams, out_streams):
        s = Stream('s')
        map_element(lambda v: v*2, in_streams[0], s)
        print_stream(s, 's')

    # Source thread target for source stream named 'x'.
    def h(proc):
        for i in range(2):
            proc.copy_stream(data=list(range(i*3, (i+1)*3)),
                             stream_name='x')
            time.sleep(0.001)
        proc.finished_source(stream_name='x')

    # Specification
    multicore_specification = [
        # Streams
        [('x', 'i'), ('y', 'i')],
        # Processes
        [
            # Process p0
            {'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y'],
             'args': [ADDEND_VALUE], 'sources': ['x'], 'source_functions':[h]},
            # Process p1
            {'name': 'p1', 'agent': g, 'inputs': ['y'], }
        ]
       ]

    # Execute processes (after including your own non IoTPy processes)
    processes = get_processes(multicore_specification)
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

#-------------------------------------------------------------
def test_parameter_result():
    """
    This example illustrates how you can get results from IoTPy processes when the
    processes terminate. The results are stored in a buffer (a multiprocessing.Array)
    which your non-IoTPy code can read. You can insert data into the IoTPy processes
    continuously or before the processes are started.

    In this example output_buffer[j] = 0 + 1 + 2 + ... + j

    """
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
        #print_stream(in_streams[0], 'gg_in_streams[0]')
        #print_stream(out_streams[0], 'gg_out_streams[0]')

    # Agent function for process named 'p1'
    def g(in_streams, out_streams):
        s = Stream('s')
        map_element(lambda v: v*2, in_streams[0], s)
        print_stream(s, 's')

    # Source thread target for source stream named 'x'.
    def h(proc):
        for i in range(2):
            proc.copy_stream(data=list(range(i*3, (i+1)*3)),
                             stream_name='x')
            time.sleep(0.001)
        proc.finished_source(stream_name='x')

    # Specification
    multicore_specification = [
        # Streams
        [('x', 'i'), ('y', 'i')],
        # Processes
        [  # Process p0
            {'name': 'p0', 'agent': f, 'inputs':['x'], 'outputs': ['y'],
            'keyword_args' : {'output_buffer' : output_buffer,
                              'output_buffer_ptr' : output_buffer_ptr},
             'sources': ['x'], 'source_functions':[h]},
            # Process p1
            {'name': 'p1', 'agent': g, 'inputs': ['y'], } ]]

    # Execute processes (after including your own non IoTPy processes)
    processes = get_processes(multicore_specification)
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

    # Verify that output_buffer can be read by the parent process.
    print ('output_buffer is ', output_buffer[:output_buffer_ptr.value])


def test_echo():
    """
    This example illustrates a circular flow structure of
    streams between processes. Process p0 feeds process p1,
    and p1 feeds p0. This example shows a process (p0) with
    2 input streams.

    The example also illustrates the use of args and keyword_args
    as well as output queues and threads, see q and my_thread.

    The example is from making an echo to a sound, and then
    generating the heard sound which is the made sound plus
    the echo. See IoTPy/examples/acoustics. The key point
    of the example is to show how processes are connected;
    the acoustics part is not important for this illustration
    of a multicore application.

    """
    # This is the delay from when the made sound hits a
    # reflecting surface.
    delay = 4
    # This is the attenuation of the reflected wave.
    attenuation = 0.5
    # The results are put in this queue.
    q = multiprocessing.Queue()

    # Agent function for process named 'p0'
    # This agent zips the sound made with the echo
    # to produce the sound heard.
    def f(in_streams, out_streams, delay):
        sound_made, echo = in_streams
        echo.extend([0] * delay)
        # The zip_map output is the sound heard which is
        # the sound heard plus the echo.
        zip_map(sum, [sound_made, echo], out_streams[0])

    # Agent function for process named 'p1'
    # This process puts the sound heard into the output queue
    #  and returns the echo as an output stream.
    def g(in_streams, out_streams, attenuation, q):
        def gg(v):
            # v is the sound heard
            q.put(v)
            # v*attenuation is the echo
            return v*attenuation
        map_element(
            gg, in_streams[0], out_streams[0])

    # Source thread target for source stream named 'sound_made'.
    # In this test sound made is [0, 1,..., 9, 0, 0, ...., 0]
    def h(proc):
        proc.copy_stream(data=list(range(10)), stream_name='sound_made')
        time.sleep(0.1)
        proc.copy_stream(data=([0]*10), stream_name='sound_made')
        proc.finished_source(stream_name='sound_made')
        return

    # Thread that gets data from the output queue
    # This thread is included in 'threads' in the specification.
    # Thread target
    def get_data_from_output_queue(q):
        finished_getting_output = False
        while not finished_getting_output:
            v = q.get()
            if v == '_finished':
                break
            print ('from queue: ', v)
    # Thread
    my_thread = threading.Thread(target=get_data_from_output_queue, args=(q,))

    multicore_specification = [
        # Streams
        [('sound_made', 'f'), ('echo', 'f'), ('sound_heard', 'f')],
        # Processes
        [# Process p0
         {'name': 'p0', 'agent': f, 'inputs': ['sound_made', 'echo'], 'outputs': ['sound_heard'],
          'keyword_args' : {'delay' : delay}, 'sources': ['sound_made'], 'source_functions':[h]},
         # Process p1
         {'name': 'p1', 'agent': g, 'inputs': ['sound_heard'], 'outputs': ['echo'],
          'args': [attenuation, q], 'output_queues': [q], 'threads': [my_thread] } ]]

    # Execute processes (after including your own non IoTPy processes)
    processes = get_processes(multicore_specification)
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()


def multicore_example_v1(DATA, ADDEND, MULTIPLICAND, EXPONENT):
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

    This example also illustrates an alternative way of specifying
    multicore applications using 'connect streams' to connect processes
    explicitly rather than by using stream names to implicitly connect
    processes.

    """
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
        #print_stream(out_streams[0], 'out_streams[0]')

    # The computational function for process p1
    def g(in_streams, out_streams, MULTIPLICAND, EXPONENT, q, buffer, ptr):
        @sink_e
        def h(v):
            q.put(v*MULTIPLICAND)
            buffer[ptr.value] = v**EXPONENT
            ptr.value += 1
        h(in_streams[0])

    # Source thread target for source stream named 'data'.
    def h(proc):
        proc.copy_stream(data=DATA, stream_name='data')
        proc.finished_source(stream_name='data')
        return

    def my_thread_target():
        # Example of a non-IoTPy thread that runs in the
        # same process.
        time.sleep(0.0001)
    # Thread
    my_thread = threading.Thread(target=my_thread_target, args=())
            

    multicore_specification = [
        # Streams
        [('data', 'f'), ('result', 'f')],
        # Processes
        [# Process p0
         {'name': 'p0', 'agent': f, 'inputs': ['data'], 'outputs': ['result'],
          'args' : [ADDEND], 'sources': ['data'], 'source_functions':[h]},
         # Process p1
         {'name': 'p1', 'agent': g, 'inputs': ['result'],
          'args': [MULTIPLICAND, EXPONENT, q, buffer, ptr],
         'output_queues': [q], 'threads': [my_thread] } ]]

    # Get list of processes and process managers

    # Execute processes (after including your own non IoTPy processes)
    processes = get_processes(multicore_specification)
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

    # finished_source indicates that this source is finished. No more data will be sent on the
    # stream called stream_name ('data') in the process with the specified name ('p0').
    queue_index = 0
    finished_getting_output = False
    while not finished_getting_output:
        element_from_queue = q.get()
        print ('queue[', queue_index, '] = ', element_from_queue)
        queue_index += 1
        if element_from_queue == '_finished':
            finished_getting_output = True

    # Get the results returned in the buffer.
    print ('buffer is ', buffer[:ptr.value])

def multicore_example_v2(DATA, ADDEND, MULTIPLICAND, EXPONENT):
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

    This example also illustrates an alternative way of specifying
    multicore applications using 'connect streams' to connect processes
    explicitly rather than by using stream names to implicitly connect
    processes.

    """
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
        #print_stream(out_streams[0], 'out_streams[0]')

    # The computational function for process p1
    def g(in_streams, out_streams, MULTIPLICAND, EXPONENT, q, buffer, ptr):
        @sink_e
        def h(v):
            q.put(v*MULTIPLICAND)
            buffer[ptr.value] = v**EXPONENT
            ptr.value += 1
        h(in_streams[0])

    def thread_target_f():
            time.sleep(0.0001)
            

    process_specs = \
      {
        'p0':
           {'inputs': [('in', 'f')],
            'outputs': [('out', 'f')],
            'agent': f,
            'args': [ADDEND],
            'sources': [('data', 'f')],
            'threads': [threading.Thread(target=thread_target_f)]
           },
        'p1':
           {'inputs': [('in', 'f')],
            'outputs': [],
            'agent': g,
            'args' : [MULTIPLICAND, EXPONENT,
                                 q, buffer, ptr],
            'output_queues' : [q]
           }
      }

    connect_streams = [
        ['p0', 'data', 'p0', 'in'],
        ['p0', 'out', 'p1', 'in']]

    # Get list of processes and process managers
    process_list, process_managers = make_multicore_processes(process_specs, connect_streams)

    # Start all processes (including possibly non-IoTPy processes).
    for process in process_list: process.start()
        
    # This section of code is arbitrary non-IoTPy code.
    # This code puts data into streams in IoTPy code executing in other processes.
    # copy_data_to_stream puts the specified data, DATA, into the stream with
    # the specified stream_name ('data') in the process with the specified name ('p0').
    copy_data_to_stream(
        DATA, proc=process_managers['p0'], stream_name='data')

    # finished_source indicates that this source is finished. No more data will be sent on the
    # stream called stream_name ('data') in the process with the specified name ('p0').
    finished_source(process_managers['p0'], 'data')

    queue_index = 0
    while True:
        element_from_queue = q.get()
        if element_from_queue == '_finished':
            break
        print ('queue[', queue_index, '] = ', element_from_queue)
        queue_index += 1

    # Join and terminate all processes that were created.
    for process in process_list: process.join()
    for process in process_list: process.terminate()

    # Get the results returned in the buffer.
    print ('buffer is ', buffer[:ptr.value])
        
if __name__ == '__main__':
    print ('starting test_q_simple_1')
    test_q_simple_1()
    print('')
    print ('--------------------------------------')
    print ('starting test_q_simple')
    test_q_simple()
    print('')
    print ('--------------------------------------')
    print ('starting test_1_q')
    test_1_q()
    print ('')
    print ('starting test_0_0')
    test_0_0()
    print ('')
    print ('starting test_0_1')
    test_0_1()
    print ('')
    print ('starting test_1')
    test_1()
    print('')
    print ('--------------------------------------')
    print ('starting test_parameter')
    print ('')
    print ('Output printed are values of stream s. See function g')
    print ('s[j] = 500 + j + 100, because the ADDEND is 500 and')
    print ('increment adds 1 + 100')
    print ('')
    test_parameter(500)
    print('')
    print ('----------------------------')
    print('')
    print ('starting test_parameter_result')
    print ('')
    print ('Output stream s and output_buffer.')
    print ('output_buffer is [0, 1, 3, 6, 10, .., 45]')
    print ('s[j] = output_buffer[j] + 100')
    print ('')
    test_parameter_result()
    print('')
    print('')
    print('')
    print ('--------------------------------------')
    print ('starting test_echo')
    print ('delay = 4, attenuation = 0.5, spoken=[0,1,2,...,9]')
    print ('')
    print ('For 0 <= j < 4 : q[j] = j')
    print ('For 4 <= j < 10: q[j] = j + q[j-4]*0.5')
    print ('For 10 <=j : q[j] = q[j-4]*0.5')
    print('')
    test_echo()
    print('')
    print ('--------------------------------------')
    print ('starting multicore_example v1')
    print ('')
    print ('q[j] = (j+ADDEND)*MULTIPLICAND')
    print ('buffer[j] = (j+ADDEND)**EXPONENT')
    print ('ADDEND=100, MULTIPLICAND=300, EXPONENT=2')
    print ('')
    multicore_example_v1(DATA=list(range(3)), ADDEND=100, MULTIPLICAND=300, EXPONENT=2)
    print ('--------------------------------------')
    print ('starting multicore_example v2')
    print ('')
    print ('q[j] = (j+ADDEND)*MULTIPLICAND')
    print ('buffer[j] = (j+ADDEND)**EXPONENT')
    print ('ADDEND=100, MULTIPLICAND=300, EXPONENT=2')
    print ('')
    multicore_example_v2(DATA=list(range(3)), ADDEND=100, MULTIPLICAND=300, EXPONENT=2)
