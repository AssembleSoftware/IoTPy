import numpy as np

import sys
import os
sys.path.append("../helper_functions")
sys.path.append("../core")
sys.path.append("../agent_types")

# agent and stream are in ../core
from agent import Agent
from stream import Stream, StreamArray, _no_value, _multivalue, run
# recent_values and run are in ../helper_functions
from recent_values import recent_values
#from run import run
# op is in ../agent_types
from op import map_element, map_element_f
from op import filter_element, filter_element_f
from op import map_list, map_list_f
from op import timed_window
from basics import fmap_e, map_e

#                                     A SIMPLE EXAMPLE TEST
#------------------------------------------------------------------------------------------------
# This example is to illustrate the steps in the test.
# The later examples test several agents whereas this simple
# test only tests a single agent.
# The seven steps in this test may occur in different orders
# in the later tests.
def test_example_1():
    # Get scheduler
    scheduler = Stream.scheduler
    # Specify streams
    x = Stream('x')
    y = Stream('y')
    # Specify encapsulated functions (if any)
    def f(v): return 2*v
    # Specify agents.
    map_element(func=f, in_stream=x, out_stream=y)

    for i in range(8):
        x.extend(list(range(i*5, (i+1)*5)))
        run()
        #print ('y is ', y.recent[:y.stop])

if __name__ == '__main__':
    test_example_1()
    
