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

#--------------------------------------------------------------------
def test_1():
    # Functions wrapped by agents
    def f(in_streams, out_streams):
        double(in_stream=in_streams[0], out_stream=out_streams[0])

    def g(in_streams, out_streams):
        s = Stream(name='s')
        increment(in_stream=in_streams[0], out_stream=s)
        print_stream(s, name=s.name)

    # Specify processes and connections.
    processes = \
      {
        'get_source_data_and_compute_process':
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
          'get_source_data_and_compute_process' :
            {
                'out' : [('aggregate_and_output_process', 'in')],
                'acceleration' : [('get_source_data_and_compute_process', 'in')]
            },
           'aggregate_and_output_process':
            {}
      }

    multicore(processes, connections)



#--------------------------------------------------------------------
def test_2():
    
    # Functions wrapped by agents
    def f(in_streams, out_streams):
        multiply_and_add(in_stream=in_streams[0], out_stream=out_streams[0],
                         multiplicand=2, addend=1)

    def g(in_streams, out_streams):
        filter_then_square(in_stream=in_streams[0], out_stream=out_streams[0],
                           filter_threshold=20)

    def h(in_streams, out_streams):
        s = Stream('s')
        sum_window(in_stream=in_streams[0], out_stream=s, window_size=3, step_size=3)
        print_stream(s, name=s.name)
        

    # Specify processes and connections.
    processes = \
      {
        'get_source_data_and_compute_process':
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
          'get_source_data_and_compute_process' :
            {
                'out' : [('filter_and_square_process', 'in')],
                'acceleration' : [('get_source_data_and_compute_process', 'in')]
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
        multiply_and_add(in_stream=in_streams[0], out_stream=out_streams[0],
                         multiplicand=2, addend=1)

    def g(in_streams, out_streams):
        t = Stream('t')
        filter_then_square(in_stream=in_streams[0], out_stream=t,
                           filter_threshold=20)
        print_stream(t, name='p1')

    def sums(in_streams, out_streams):
        s = Stream('s')
        sum_window(in_stream=in_streams[0], out_stream=s, window_size=3, step_size=3)
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
        identical(in_stream=in_streams[0], out_stream=out_streams[0])

    def g(in_streams, out_streams):
        multiply(in_stream=in_streams[0], out_stream=out_streams[0],
                 multiplicand=2)

    def h(in_streams, out_streams):
        square(in_stream=in_streams[0], out_stream=out_streams[0])

    def m(in_streams, out_streams):
        s = Stream('s')
        sum_numbers(in_streams=in_streams, out_stream=s)
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


if __name__ == '__main__':
    print ('starting test_1')
    print ('s[j] = 2*j + 1')
    test_1()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')
    print ('starting test_2')
    print ('Output of get_source_data_and_compute_process is: ')
    print ('[1, 3, 5, 7, 9, 11, .... ,39 ]')
    print ('Output of filter_and_square_process is:')
    print ('[1, 9, 25, 49, 81, 121, 169, 225, 289, 361]')
    print('Output of aggregate_and_output_process is:')
    print('[1+9+25, 49+81+121, 169+225+289] which is:')
    print ('[35, 251, 683]')
    test_2()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')
    print ('starting test_3')
    test_3()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')
    print ('starting test_4')
    test_4()

    
