"""
This module contains tests:

* offset_estimation_test()
which tests code from multicore.py in multiprocessing.

"""

import sys
import os
import threading
import random
import multiprocessing
import numpy as np
sys.path.append(os.path.abspath("../multiprocessing"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../../examples/timing"))

"""
This module contains tests:

* offset_estimation_test()
which tests code from multicore.py in multiprocessing.

"""

import sys
import os
import threading
import random
import multiprocessing
import numpy as np
sys.path.append(os.path.abspath("../multiprocessing"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../../examples/timing"))

from multicore import *
from merge import zip_stream
from basics import map_e, map_l, map_w, merge_e
from run import run


@map_e
def double(v): return 2*v

@map_e
def increment(v): return v+1

@map_e
def square(v): return v**2

@map_e
def identical(v): return v

@map_e
def multiply(v, multiplicand): return v*multiplicand

@map_e
def add(v, addend): return v+addend

@map_e
def multiply_and_add(element, multiplicand, addend):
    return element*multiplicand + addend

@map_l
def filter_then_square(sequence, filter_threshold):
    return [element**2 for element in sequence
            if element < filter_threshold]

@map_w
def sum_window(window):
    return sum(window)

@merge_e
def sum_numbers(numbers):
    return sum(numbers)

# Target of source thread.
def source_thread_target(proc, stream_name):
    num_steps=5
    step_size=4
    for i in range(num_steps):
        data = list(range(i*step_size, (i+1)*step_size))
        copy_data_to_stream(data, proc, stream_name)
        time.sleep(0)
    return

def test_1_single_process():
    """
    test_1_single_process() and test_1() show how to convert a
    single thread application into a multicore application.
    
    This is a single process example which is converted into a
    multicore example in test_1(), see below. Read this function
    while you read function test_1().

    The partitioning to obtain multiple cores and threads is
    done as follows.

    (1) put_data_in_stream() is converted to a function which
    is the target of a thread. In test_1() this function is
    source_thread_target(proc, stream_name)

    (2) double(x,y) is put in a separate process. The compute
    function of this process is f(). Since the parameters
    of compute_func are in_streams and out_streams, we get
    f from double in the following way:
    
    def f(in_streams, out_streams):
        double(in_stream=in_streams[0], out_stream=out_streams[0])
    

    (3) increment() and print_stream() are in a separate process.
    The compute function of this process is g().

    Run both test_1_single_process() and test_1() and look at
    their identical outputs.

    """

    # ********************************************************
    # We will put this function in its own thread in test_1()
    def put_data_in_stream(stream):
        num_steps=5
        step_size=4
        for i in range(num_steps):
            data = list(range(i*step_size, (i+1)*step_size))
            stream.extend(data)
            run()
        return

    # ********************************************************
    # We will put these lines in a separate process in test_1()
    x = Stream('x')
    y = Stream('y')
    double(x, y)

    # *********************************************************
    # We will put these lines in a separate process in test_1().
    s = Stream(name='s')
    increment(y, s)
    print_stream(s, name=s.name)

    # *********************************************************
    # This function is executed in a separate thread in test_1().
    put_data_in_stream(x)
    
    
#--------------------------------------------------------------------
def test_1():
    # Functions wrapped by agents
    def f(in_streams, out_streams):
        double(in_streams[0], out_streams[0])

    def g(in_streams, out_streams):
        s = Stream(name='s')
        increment(in_streams[0], s)
        print_stream(s, name=s.name)

    # Specify processes and connections.
    processes = \
      {
        'source_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': source_thread_target
                  },
               },
            'actuators': {}
           },
        'aggregate_and_output_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
            'sources': {},
            'actuators': {}
           }
      }
    
    connections = \
      {
          'source_process' :
            {
                'out' : [('aggregate_and_output_process', 'in')],
                'acceleration' : [('source_process', 'in')]
            },
           'aggregate_and_output_process':
            {}
      }

    multicore(processes, connections)



#--------------------------------------------------------------------
def test_2():
    
    # Functions wrapped by agents
    def f(in_streams, out_streams):
        multiply_and_add(in_streams[0], out_streams[0],
                         multiplicand=2, addend=1)

    def g(in_streams, out_streams):
        filter_then_square(in_streams[0], out_streams[0],
                           filter_threshold=20)

    def h(in_streams, out_streams):
        s = Stream('s')
        sum_window(in_streams[0], s, window_size=3, step_size=3)
        print_stream(s, name=s.name)
        

    # Specify processes and connections.
    processes = \
      {
        'source_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': source_thread_target
                  },
               },
            'actuators': {}
           },
        'filter_and_square_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('filtered', 'i')],
            'compute_func': g,
            'sources': {},
            'actuators': {}
           },
        'aggregate_and_output_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': h,
            'sources': {},
            'actuators': {}
           }
      }
    
    connections = \
      {
          'source_process' :
            {
                'out' : [('filter_and_square_process', 'in')],
                'acceleration' : [('source_process', 'in')]
            },
           'filter_and_square_process' :
            {
                'filtered' : [('aggregate_and_output_process', 'in')],
            },
           'aggregate_and_output_process':
            {}
      }

    multicore(processes, connections)


#--------------------------------------------------------------------
def test_3():

    # Functions wrapped by agents
    def f(in_streams, out_streams):
        multiply_and_add(in_streams[0], out_streams[0],
                         multiplicand=2, addend=1)

    def g(in_streams, out_streams):
        t = Stream('t')
        filter_then_square(in_streams[0], t,
                           filter_threshold=20)
        print_stream(t, name='p1')

    def sums(in_streams, out_streams):
        s = Stream('s')
        sum_window(in_streams[0], s, window_size=3, step_size=3)
        print_stream(s, name='           p2')

    processes = \
      {
        'source_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': source_thread_target
                  },
               }
           },
        'process_1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
            'sources': {}
           },
        'process_2':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': sums,
            'sources': {}
           }
      }
    
    connections = \
      {
          'source_process' :
            {
                'out' : [('process_1', 'in'), ('process_2', 'in')],
                'acceleration' : [('source_process', 'in')]
            },
          'process_1':
            {
            },
          'process_2':
            {
            }
      }

    multicore(processes, connections)


#--------------------------------------------------------------------
def test_4():

    # Functions wrapped by agents
    def f(in_streams, out_streams):
        identical(in_streams[0], out_streams[0])

    def g(in_streams, out_streams):
        multiply(in_streams[0], out_streams[0],
                 multiplicand=2)

    def h(in_streams, out_streams):
        square(in_streams[0], out_streams[0])

    def m(in_streams, out_streams):
        s = Stream('s')
        sum_numbers(in_streams, s)
        print_stream(s, name='s')

    processes = \
      {
        'source_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': source_thread_target
                  },
               }
           },
        'multiply_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': g,
            'sources': {}
           },
        'square_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': h,
            'sources': {}
           },
        'merge_process':
           {'in_stream_names_types': [('in_multiply', 'i'),
                                      ('in_square', 'i')],
            'out_stream_names_types': [],
            'compute_func': m,
            'sources': {}
           }
      }
    
    connections = \
      {
          'source_process' :
            {
                'out' : [('multiply_process', 'in'), ('square_process', 'in')],
                'acceleration' : [('source_process', 'in')]
            },
          'multiply_process':
            {
                'out' : [('merge_process', 'in_multiply')]
            },
          'square_process':
            {
                'out' : [('merge_process', 'in_square')]
            },
          'merge_process':
            {
            }
      }

    multicore(processes, connections)


#--------------------------------------------------------------------
def test_0():
    # Example with a source thread and a single process.
    def f(in_streams, out_streams):
        x = Stream('x')
        y = Stream('y')
        double(in_streams[0], x)
        increment(x, y)
        print_stream(y, name=y.name)

    # Specify processes and connections.
    processes = \
      {
        'process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': f,
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': source_thread_target
                  },
               },
            'actuators': {}
           }
      }
    
    connections = \
      {
          'process' :
            {
                'acceleration' : [('process', 'in')]
            }
      }

    multicore(processes, connections)



if __name__ == '__main__':
    print ('starting test_0')
    print ('example of a single process with a source thread')
    print ('s[j] = 2*j + 1')
    print ('')
    test_0()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')
    print ('starting test_1')
    print ('s[j] = 2*j + 1')
    print ('')
    test_1()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')
    print ('start test_1_single_process')
    print ('Output of test_1_single process() is identical:')
    print ('to output of test_1()')
    print ('[1, 3, 5, ..., 39]')
    print ('')
    test_1_single_process()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')
    print ('starting test_2')
    print ('Output of source_process is: ')
    print ('[1, 3, 5, 7, 9, 11, .... ,39 ]')
    print ('')
    print ('Output of filter_and_square_process is:')
    print ('[1, 9, 25, 49, 81, 121, 169, 225, 289, 361]')
    print ('')
    print('Output of aggregate_and_output_process is:')
    print('[1+9+25, 49+81+121, 169+225+289] which is:')
    print ('[35, 251, 683]')
    print ('')    
    test_2()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')
    print ('starting test_3')
    print ('')
    print ('p1 is [1, 3, 5,...., 39]')
    print ('')
    print ('p2 is [1+3+5, 7+9+11, 13+15+17, ..]')
    print ('')
    test_3()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')
    print ('starting test_4')
    print ('')
    print ('Output of source process is:')
    print ('[0, 1, 2, 3, ...., 19]')
    print ('')
    print ('Output of multiply process is source*2:')
    print ('[0, 2, 4, 6, .... 38]')
    print ('')
    print ('Output of square process is source**2:')
    print ('[0, 1, 4, 9, ... 361]')
    print ('')
    print ('Output of aggregate process is:')
    print ('[0+0, 2+1, 4+4, 6+9, ..., 38+361]')
    print ('')
    test_4()

    
