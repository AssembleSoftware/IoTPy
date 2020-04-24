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
# be shared across processes.
import threading
import time
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../concurrency"))

# sink, op are in the agent_types folder
from sink import stream_to_queue, sink_list, sink_element
from merge import zip_map
from op import map_element, map_list
# compute_engine, stream are in the core folder
from compute_engine import ComputeEngine
from stream import Stream
# basics is in the helper_functions folder
from basics import map_e, fmap_e, map_l, f_mul, sink_e, f_add, r_add
from print_stream import print_stream
# utils is in the current folder
from utils import check_processes_connections_format, check_connections_validity
from multicore import multicore, copy_data_to_stream, finished_source
from multicore import make_multicore_processes, run_single_process_single_source


def f(in_streams, out_streams, ADDEND):
    out_streams[0] = f_add(in_streams[0], ADDEND)

def g(in_streams, out_streams):
    s = f_add(in_streams[0], 100)
    print_stream(s, 's')

def h(in_streams, out_streams):
    pass


# Target of source thread.
def source_thread_target(proc, stream_name):
    num_steps, step_size = 3, 3
    for i in range(num_steps):
        data = list(range(i*step_size, (i+1)*step_size))
        copy_data_to_stream(data, proc, stream_name)
        time.sleep(0.001)

    finished_source(proc, stream_name)
            
def test_parameter(ADDEND_VALUE):
    #---------------------------------------------------------------------
    # Specify process_specs and connections.
    # This example has two processes:
    # (1) p0 and
    # (2) p1.
    
    # Specification of p0:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has a single output stream called 'out'
    # which is of type int ('i').
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function f.
    # (4) Keyword arguments: Function f has a keyword argument
    # called ADDEND.
    # (5) sources: This process has a single source called
    # 'acceleration'. The source thread target is specified by
    # the function source_thread_target. This function generates
    # int ('i').
    # (6) output_queues: This process has no output_queues.
    
    # Specification of p1:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has no outputs.
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function g.
    # (4) Keyword arguments: Function g has no keyword argument
    # (5) sources: This process has no sources
    # (6) output_queues: This process has no output_queues.

    # Connections between processes.
    # (1) Output 'out' of 'p0' is connected to input 'in' of p1.
    # (2) The source, 'acceleration', of 'p0' is connected to input
    #     'in' of 'p1'.
    
    process_specs = \
      {
        'p0':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'keyword_args' : {'ADDEND' :ADDEND_VALUE},
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': source_thread_target
                  },
               },
            'output_queues': []
           },
        'p1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
            'keyword_args' : {},
            'sources': {},
            'output_queues': []
           }
      }

    connect_streams = [['p0', 'out', 'p1', 'in'],
                       ['p0', 'acceleration', 'p0', 'in']]

    publishers=[('p0', 'out', 'publication')]

    # Create and run multiple processes in a multicore machine.
    multicore(process_specs, connect_streams)


def test_single_process_single_source():
    # Target of source thread.
    def source_func(proc, stream_name):
        num_steps, step_size = 3, 4
        for i in range(num_steps):
            data = list(range(i*step_size, (i+1)*step_size))
            copy_data_to_stream(data, proc, stream_name)
            time.sleep(0.001)
        finished_source(proc, stream_name)
    def compute_func(in_streams, out_streams):
        print_stream(in_streams[0], 'in_stream')

    run_single_process_single_source(source_func, compute_func)

#-------------------------------------------------------------
def test_source_process(ADDEND_VALUE):
    """
    In this example, a process, called a 'source process' serves
    no function other than to serve as a source of data for a
    stream. This example illustrates integration of
    user (non-IoTPy) code with IoTPy code. The non-IoTPy code puts
    data into a stream in a process which serves as a 'source process.'
    The non-IoTPy code can put data continuously into the IoTPy
    processes.
    """

    #---------------------------------------------------------------------
    # Specify processes and connections.
    # This example has 3 processes called: 'p0', 'p1', 'p2'
    
    # Specification of p0:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has a single output stream called 'out'
    # which is of type int ('i').
    # (3) Computation: f ---It creates a network of agents that carries
    # out computation in the main thread by calling function f.
    # (4) Keyword arguments: Function f has a keyword argument
    # called ADDEND. This argument must be a constant.
    # (5) sources: This process no sources
    # (6) output_queues: This process has no output_queues.
    
    # Specification of p1:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has no outputs.
    # (3) Computation: g --- It creates a network of agents that carries
    # out computation in the main thread by calling function g.
    # (4) Keyword arguments: Function g has no keyword argument
    # (5) sources: This process has no sources
    # (6) output_queues: This process has no output_queues.
    
    # Specification of p2:
    # (1) Inputs: It no inputs.
    # (2) Outputs: It has no outputs.
    # (3) Computation: h --- This is a dummy function, pass.
    # (4) Keyword arguments: Function h has no keyword arguments.
    # (5) sources: This process has a single source called
    # 'acceleration'. This function generates int ('i').
    # The data for this source is provided by the external
    # (possibly non-IoTPy) code. So, the func for this source is None.
    # (6) output_queues: This process has no output_queues.

    # Connections between processes.
    # (1) Output 'out' of 'p0' is connected to input 'in' of p1.
    # (2) The source, 'acceleration', of 'p2' is connected to
    # input 'in' of 'p1'.
    
    process_specs = \
      {
        'p0':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'args' : [ADDEND_VALUE],
           },
        'p1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
           },
        'p2':
           {'in_stream_names_types': [],
            'out_stream_names_types': [],
            'compute_func': h,
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': None,
                  },
               },
           }
      }

    connect_streams = \
      [['p0', 'out', 'p1', 'in'],
       ['p2', 'acceleration', 'p0', 'in']
      ]

    #--------------------------------------------------------------------
    # Create and run multiple processes in a multicore machine.
    process_list, process_managers = make_multicore_processes(
        process_specs, connect_streams)

    # Start all processes (including possibly non-IoTPy
    # processes).
    for process in process_list: process.start()

    # This section of code is arbitrary non-IoTPy code.
    # This code puts data into streams in IoTPy code
    # executing in other processes.
    #
    # copy_data_to_stream puts the specified data,
    # list(range(10)), into the stream with
    # the specified stream_name ('acceleration')
    # in the process with the specified name ('p2').
    copy_data_to_stream(
        data=list(range(10)), proc=process_managers['p2'],
        stream_name='acceleration')

    # finished_source indicates that this source is finished.
    # No more data will be sent on the stream called stream_name
    # 'acceleration' in the process with the specified name 'p2'.
    finished_source(proc=process_managers['p2'], stream_name='acceleration')

    # Join and terminate processes.
    for process in process_list: process.join()
    for process in process_list: process.terminate()

#-------------------------------------------------------------
def test_parameter_direct_source(ADDEND_VALUE):

    # Specify processes and connections.
    # This example has two processes:
    # (1) get_source_data_and_compute_process and
    # (2) aggregate_and_output_process.
    
    # Specification of get_source_data_and_compute_process:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has a single output stream called 'out'
    # which is of type int ('i').
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function f.
    # (4) Keyword arguments: Function f has a keyword argument
    # called ADDEND. This argument must be a constant.
    # (5) sources: This process has a single source called
    # 'acceleration'. The source thread target is specified by
    # the function source_thread_target. This function generates
    # int ('i').
    # (6) output_queues: This process has no output_queues.
    
    # Specification of aggregate_and_output_process:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has no outputs.
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function g.
    # (4) Keyword arguments: Function g has no keyword argument
    # (5) sources: This process has no sources
    # (6) output_queues: This process has no output_queues.

    # Connections between processes.
    # (1) Output 'out' of 'get_source_data_and_compute_process' is
    # connected to input 'in' of aggregate_and_output_process.
    # (2) The source, 'acceleration', of 'get_source_data_and_compute_process'
    # is connected to input 'in' of 'get_source_data_and_compute_process'.
    
    process_specs = \
      {
        'p0':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'keyword_args' : {'ADDEND' :ADDEND_VALUE},
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': None,
                  },
               },
           },
        'p1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
           }
      }

    connect_streams = \
      [['p0', 'out', 'p1', 'in'],
       ['p0', 'acceleration', 'p0', 'in']
      ]

    #--------------------------------------------------------------------
    # Create and run multiple processes in a multicore machine.
    process_list, process_managers = make_multicore_processes(process_specs, connect_streams)

    # Start all processes (including possibly non-IoTPy processes).
    for process in process_list: process.start()

    # This section of code is arbitrary non-IoTPy code.
    # This code puts data into streams in IoTPy code executing in other processes.
    #
    # copy_data_to_stream puts the specified data, list(range(10)), into the stream with
    # the specified stream_name ('acceleration') in the process with the specified name ('p2').
    copy_data_to_stream(
        data=list(range(10)), proc=process_managers['p0'], stream_name='acceleration')

    # finished_source indicates that this source is finished. No more data will be sent on the
    # stream called stream_name ('acceleration') in the process with the specified name ('p2').
    finished_source(proc=process_managers['p0'], stream_name='acceleration')

    # Join and terminate processes.
    for process in process_list: process.join()
    for process in process_list: process.terminate()

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
    def gg(v, sum, output_buffer, output_buffer_ptr):
        sum += v
        output_buffer[output_buffer_ptr.value] = sum
        output_buffer_ptr.value +=1
        return sum, sum

    def f(in_streams, out_streams, output_buffer, output_buffer_ptr):
        gg(in_streams[0], out_streams[0], state=0,
           output_buffer=output_buffer, output_buffer_ptr=output_buffer_ptr)
    

    #---------------------------------------------------------------------
    # Specify process_specs and connections.
    # This example has two processes called 'p0' and 'p1'
    
    # Specification of p0:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has a single output stream called 'out'
    # which is of type int ('i').
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function f.
    # (4) Keyword arguments: Function f has two keyword arguments
    # output_buffer and output_buffer_ptr.
    # (5) sources: This process has a single source called
    # 'acceleration'. This function generates int ('i'). The values
    # in the source are provided by code outside IoTPy. You put
    # values using copy_data_to_stream().
    # (6) output_queues: This process has no output_queues.
    
    # Specification of p1:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has no outputs.
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function g.
    # (4) Keyword arguments: Function g has no keyword argument
    # (5) sources: This process has a single source called
    # 'acceleration'. This function generates int ('i'). The values
    # in the source are provided by code outside IoTPy. You put
    # values using copy_data_to_stream().
    # (6) output_queues: This process has no output_queues.

    # Connections between processes.
    # (1) Output 'acceleration' (the source) of 'p0' is connected to input 'in'
    #     of 'p0' itself.
    # (2) Output 'out' of 'p0' is connected to input 'in' of p1.

    process_specs = \
      {
        'p0':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'keyword_args' : {'output_buffer' : output_buffer,
                              'output_buffer_ptr' : output_buffer_ptr},
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': None,
                  },
               },
           },
        'p1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
           }
      }

    connect_streams = \
      [['p0', 'out', 'p1', 'in'],
       ['p0', 'acceleration', 'p0', 'in']
      ]

    #--------------------------------------------------------------------
    # Create and run multiple processes in a multicore machine.
    process_list, process_managers = make_multicore_processes(process_specs, connect_streams)

    # Start all processes (including possibly non-IoTPy processes).
    for process in process_list: process.start()

    # This section of code is arbitrary non-IoTPy code.
    # This code puts data into streams in IoTPy code executing in other processes.
    #
    # copy_data_to_stream puts the specified data, list(range(10)), into the stream with
    # the specified stream_name ('acceleration') in the process with the specified name ('p2').
    copy_data_to_stream(
        data=list(range(10)), proc=process_managers['p0'], stream_name='acceleration')

    # finished_source indicates that this source is finished. No more data will be sent on the
    # stream called stream_name ('acceleration') in the process with the specified name ('p2').
    finished_source(process_managers['p0'], 'acceleration')

    # Join and terminate processes.
    for process in process_list: process.join()
    for process in process_list: process.terminate()

    # Verify that output_buffer can be read by the parent process.
    print ('output_buffer is ', output_buffer[:output_buffer_ptr.value])

#-------------------------------------------------------------
def test_parameter_queue():
    """
    This example illustrates how IoTPy processes can continuously put data into a queue
    that non-IoTPy code executing in another process can read.

    """
    q = multiprocessing.Queue()
    # If the input stream is x then this agent puts
    # x[0] + ... x[n] into the queue q, for n = 0, 1, 2, ..
    @map_e
    def gg(v, sum, q):
        sum += v
        q.put(sum)
        return sum, sum

    @map_e
    def increment(v): return v + 10

    # Functions wrapped by agents
    # Function f is used in p0
    # q is a keyword arg of f.
    # Note: q must be passed in the specification of
    # the process. See the line:
    # 'keyword_args' : {'q' : q},
    def f(in_streams, out_streams, q):
        gg(in_streams[0], out_streams[0], state=0, q=q)
    
    #---------------------------------------------------------------------
    # Specify process_specs and connections.
    # This example has two processes called 'p0' and 'p1'.
    
    # Specification of p0:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has a single output stream called 'out'
    # which is of type int ('i').
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function f.
    # (4) Keyword arguments: Function f has a keyword argument
    # called 'q'. q is the queue that non-IoTPy gets data from.
    # (5) sources: This process has a single source.
    # (6) output_queues: This process has no output_queues.
    
    # Specification of aggregate_and_output_process:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has no outputs.
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function g.
    # (4) Keyword arguments: Function g has no keyword argument
    # (5) sources: This process has no sources
    # (6) output_queues: This process has no output_queues.

    # Connections between processes.
    # (1) Output 'out' of 'get_source_data_and_compute_process' is
    # connected to input 'in' of aggregate_and_output_process.
    # (2) The source, 'acceleration', of 'get_source_data_and_compute_process'
    # is connected to input 'in' of 'get_source_data_and_compute_process'.
    

    process_specs = \
      {
        'p0':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'args' : [q],
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': None,
                  },
               },
           },
        'p1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
            'keyword_args' : {},
           }
      }

    connect_streams = \
      [['p0', 'out', 'p1', 'in'],
       ['p0', 'acceleration', 'p0', 'in']
      ]
    
        
    process_list, process_managers = make_multicore_processes(process_specs, connect_streams)

    # Start all processes (including possibly non-IoTPy processes).
    for process in process_list: process.start()
    # This section of code is arbitrary non-IoTPy code.
    # This code puts data into streams in IoTPy code executing in other processes.
    #
    # copy_data_to_stream puts the specified data, list(range(10)), into the stream with
    # the specified stream_name ('acceleration') in the process with the specified name ('p2').
    copy_data_to_stream(
        data=list(range(10)), proc=process_managers['p0'], stream_name='acceleration')

    # finished_source indicates that this source is finished. No more data will be sent on the
    # stream called stream_name ('acceleration') in the process with the specified name ('p2').
    finished_source(process_managers['p0'], 'acceleration')
    for process in process_list: process.join()
    for process in process_list: process.terminate()

    # Verify that the parent process can obtain data from q.
    print ('The elements of the queue are:')
    while not q.empty():
        print (q.get())

    print ('j-th get from queue is 0 + 1 + 2 + ... + j')
    print ('s[j] = 0 + 1 + 2 + ... + j + 100')

def test_echo():
    """
    This example illustrates a circular flow structure of
    streams between processes. Process p0 feeds process p1,
    and p1 feeds p0. This example shows a process (p0) with
    2 input streams.

    The example is from making an echo to a sound, and then
    generating the heard sound which is the made sound plus
    the echo. See IoTPy/examples/acoustics. The key point
    of the example is to show how processes are connected;
    the acoustics part is irrelevant.

    """
    # This is the delay from when the made sound hits a
    # reflecting surface.
    delay = 4
    # This is the attenuation of the reflected wave.
    attenuation = 0.5
    # The results are put in this queue.
    q = multiprocessing.Queue()

    def f(in_streams, out_streams, delay):
        in_streams[1].extend([0] * delay)
        zip_map(sum, in_streams, out_streams[0])

    def g(in_streams, out_streams, attenuation, q):
        def gg(v):
            q.put(v)
            return v*attenuation
        map_element(
            gg, in_streams[0], out_streams[0])

    process_specs = \
      {
        'p0':
           {'in_stream_names_types': [('sound', 'f'), ('echo', 'f')],
            'out_stream_names_types': [('sound_heard', 'f')],
            'compute_func': f,
            'keyword_args' : {'delay' : delay},
            'sources':
              {'sound_made':
                  {'type': 'f',
                   'func': None,
                  },
               },
           },
        'p1':
           {'in_stream_names_types': [('sound_heard', 'f')],
            'out_stream_names_types': [('echo', 'f')],
            'compute_func': g,
            'args': [attenuation, q],
           }
      }

    connect_streams = [
        ['p0', 'sound_made', 'p0', 'sound'],
        ['p0', 'sound_heard', 'p1', 'sound_heard'],
        ['p1', 'echo', 'p0', 'echo']]
        
    process_list, process_managers = make_multicore_processes(process_specs, connect_streams)

    # Start all processes (including possibly non-IoTPy processes).
    for process in process_list: process.start()
    # This section of code is arbitrary non-IoTPy code.
    # This code puts data into streams in IoTPy code executing in other processes.
    #
    # copy_data_to_stream puts the specified data, list(range(10)), into the stream with
    # the specified stream_name ('acceleration') in the process with the specified name ('p2').
    copy_data_to_stream(
        data=list(range(10)), proc=process_managers['p0'], stream_name='sound_made')
    copy_data_to_stream(
        data=([0]*10), proc=process_managers['p0'], stream_name='sound_made')

    # finished_source indicates that this source is finished. No more data will be sent on the
    # stream called stream_name ('acceleration') in the process with the specified name ('p2').
    finished_source(process_managers['p0'], 'sound_made')
    for process in process_list: process.join()
    for process in process_list: process.terminate()

    # Get the result from the queue.
    print ('The elements of the queue are:')
    while not q.empty():
        print (q.get())


def multicore_example(DATA, ADDEND, MULTIPLICAND, EXPONENT):
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
    # Values generated continuously by the IoTPy process are read by
    # the calling non-IoTPy process using this queue.
    q = multiprocessing.Queue()

    # The results of the parallel computation are stored in buffer.
    buffer = multiprocessing.Array('i', 10)
    # The results are in buffer[:ptr].
    # The values in buffer[ptr:] are arbitrary
    ptr = multiprocessing.Value('i', 0)

    # The computational function for process p0.
    # Arguments are: in_streams, out_streams, and additional
    # arguments. Here ADDEND is an additional argument.
    def f(in_streams, out_streams, ADDEND):
        map_element(lambda a: a+ADDEND, in_streams[0], out_streams[0])
        print_stream(out_streams[0], 'out_streams[0]')

    # The computational function for process p1
    def g(in_streams, out_streams, MULTIPLICAND, EXPONENT, q, buffer, ptr):
        @sink_e
        def h(v):
            q.put(v*MULTIPLICAND)
            buffer[ptr.value] = v**EXPONENT
            ptr.value += 1
        h(in_streams[0])

    process_specs = \
      {
        'p0':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'args': [ADDEND],
            'sources': {'data': {'type':'i',  'func':None} }
           },
        'p1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
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
    finished_getting_output = False
    while not finished_getting_output:
        element_from_queue = q.get()
        print ('element_from_queue ', element_from_queue)
        if element_from_queue == 'finis':
            finished_getting_output = True

    # Join and terminate all processes that were created.
    for process in process_list: process.join()
    for process in process_list: process.terminate()

    # Get the result from the queue.
    print ('The elements of the queue are:')
    while not q.empty():
        print (q.get())

    # Get the results returned in the buffer.
    print ('buffer is ', buffer[:ptr.value])
        
        
if __name__ == '__main__':
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
    print ('--------------------------------------')
    print ('starting test_source_process')
    print ('')
    print ('Output is values of stream s.')
    print ('s[j] = 600 + j')
    print ('because the ADDEND is 500 and ')
    print ('increment adds 1 + 100')
    print ('')
    test_source_process(ADDEND_VALUE=500)
    print('')
    print ('--------------------------------------')
    print ('starting test_single_process_single_source')
    print ('')
    print ('Output printed are values of in_stream ')
    print ('These values are range(3*4) because num_steps=3, step_size=4')
    print ('')
    test_single_process_single_source()
    print('')
    print ('--------------------------------------')
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
    print ('starting test_parameter_queue')
    print ('')
    print ('Output is values of stream s.')
    print ('And prints contents of queue')
    print ('')
    test_parameter_queue()
    print('')
    print('')
    print ('--------------------------------------')
    print ('starting test_parameter_direct_source')
    print ('')
    print ('Output is stream s.')
    print ('s[j] = 600 + j')
    print ('')
    test_parameter_direct_source(500)
    print('')
    print('')
    print ('--------------------------------------')
    print ('starting test_echo')
    print ('')
    print ('For j in 0, 1, 2, 3 : q[j] = j')
    print ('For 3 < j < 10: q[j] = j + q[j-4]*0.5')
    print ('For 10 <= j : q[j] = q[j-4]*0.5')
    print('')
    test_echo()
    print('')
    print ('--------------------------------------')
    print ('starting multicore_example')
    print ('')
    print ('q[j] = (j+ADDEND)*MULTIPLICAND')
    print ('buffer[j] = (j+ADDEND)**EXPONENT')
    print ('ADDEND=100, MULTIPLICAND=10, EXPONENT=2')
    print ('And prints contents of queue')
    print ('')
    multicore_example(DATA=list(range(3)), ADDEND=100, MULTIPLICAND=300, EXPONENT=2)
    
