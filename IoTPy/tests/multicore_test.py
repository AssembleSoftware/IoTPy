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
        
def test_1():
    def f(in_streams, out_streams):
        def ff(lst):
            return [2*v for v in lst]
        map_list(ff, in_streams[0], out_streams[0])
    def g(in_streams, out_streams):
        def gg(lst):
            for v in lst: print ('v is ', v)
        sink_list(gg, in_streams[0])
    def h(extend_stream_func, stream_name):
        def thread_target():
            num_steps=8
            step_size=4
            for i in range(num_steps):
                data = list(range(i*step_size, (i+1)*step_size))
                extend_stream_func(data, stream_name)
                time.sleep(0)
        return threading.Thread(
            target=thread_target,
            args=()
            )

    processes = \
      {
        'source_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': h
                  },
               }
           },
        'sink_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
            'sources': {}
           }
      }
    
    connections = \
      {
          'source_process' :
            {
                'out' : [('sink_process', 'in')],
                'acceleration' : [('source_process', 'in')]
            },
           'sink_process':
            {}
      }

    multicore(processes, connections)
    return

def test_2():
    def f(in_streams, out_streams):
        def ff(lst):
            return [2*v for v in lst]
        map_list(ff, in_streams[0], out_streams[0])
    def g1(in_streams, out_streams):
        def gg(lst):
            for v in lst: print ('v is ', v)
        sink_list(gg, in_streams[0])
    def g2(in_streams, out_streams):
        def gg(lst):
            for w in lst: print ('w is ', w)
        sink_list(gg, in_streams[0])
    def h(extend_stream_func, stream_name):
        def thread_target():
            num_steps=8
            step_size=4
            for i in range(num_steps):
                data = list(range(i*step_size, (i+1)*step_size))
                extend_stream_func(data, stream_name)
                time.sleep(0)
        return threading.Thread(
            target=thread_target,
            args=()
            )

    processes = \
      {
        'source_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': h
                  },
               }
           },
        'process_1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g1,
            'sources': {}
           },
        'process_2':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g2,
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

def test_3():
    def f(in_streams, out_streams):
        def ff(lst):
            return [2*v for v in lst]
        map_list(ff, in_streams[0], out_streams[0])
    def g1(in_streams, out_streams):
        def gg(lst): return lst
        map_list(gg, in_streams[0], out_streams[0])
    def g2(in_streams, out_streams):
        def gg(lst): return lst
        map_list(gg, in_streams[0], out_streams[0])
    def d(in_streams, out_streams):
        def d0(lst):
            for x in lst: print ('x is ', x)
        def d1(lst):
            for y in lst: print ('y is ', y)
        sink_list(d0, in_streams[0])
        sink_list(d1, in_streams[1])
    def h(extend_stream_func, stream_name):
        def thread_target():
            num_steps=8
            step_size=4
            for i in range(num_steps):
                data = list(range(i*step_size, (i+1)*step_size))
                extend_stream_func(data, stream_name)
                time.sleep(0)
        return threading.Thread(
            target=thread_target,
            args=()
            )

    processes = \
      {
        'source_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': h
                  },
               }
           },
        'process_1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': g1,
            'sources': {}
           },
        'process_2':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': g2,
            'sources': {}
           },
        'process_3':
           {'in_stream_names_types': [('in_1', 'i'), ('in_2', 'i')],
            'out_stream_names_types': [],
            'compute_func': d,
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
                'out' : [('process_3', 'in_1')]
            },
          'process_2':
            {
                'out' : [('process_3', 'in_2')]
            }, 
          'process_3':
            {
                'out' : [('process_4', 'in')]
            }
      }

    multicore(processes, connections)
    return
if __name__ == '__main__':
    test_1()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')   
    test_2()
    print ('')
    print ('')
    print ('--------------------------------')
    print ('')
    print ('')   
    test_3()
 

    
