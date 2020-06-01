import threading
import random
import multiprocessing
import numpy as np

from IoTPy.concurrency.multicore import *
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.agent_types.basics import map_e, map_l, map_w, merge_e, sink_e



def test_0():
    NUM_STEPS=5
    STEP_SIZE=4
    DATA = list(range(NUM_STEPS * STEP_SIZE))

    @sink_e
    def f(v, state):
        # v is an incoming message
        # state is the index into DATA. It is initially
        # 0 because of the call f(in_streams[0], state=0).
        # state is incremented by each call to f because
        # next_state = state + 1, and f returns next_state.
        assert v == DATA[state]
        next_state = state + 1
        return next_state

    def compute_func(in_streams, out_streams):
        f(in_streams[0], state=0)

    # You can use any function for the generation of source data.
    # This function should sleep for an arbitrarily small positive
    # value so that the thread that generates the source yields to
    # the main compute_func thread.
    # The source generation function calls copy_data_to_source()
    # to pass data into the source.
    # The source generation function calls source_finished() to
    # indicate that the source generation has finished.
    def source_generator(source):
        for i in range(NUM_STEPS):
            data_segment = DATA[i*STEP_SIZE : (i+1)*STEP_SIZE]
            copy_data_to_source(data_segment, source)
            time.sleep(0.001)
        source_finished(source)
        return

    # Specify processes and connections.
    processes = \
      {
        'process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': compute_func,
            'sources':
              {'example_source':
                  {'type': 'i',
                   'func': source_generator
                  },
               }
           }
      }
    
    connections = \
      {
          'process' :
            {
                'example_source' : [('process', 'in')]
            }
      }

    MulticoreProcess(processes, connections)

def test_source():
    test_0()
    print ('TEST OF SOURCE IS SUCCESSFUL.')

if __name__ == '__main__':
    test_source()
