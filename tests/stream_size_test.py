import numpy as np

import unittest
# agent and stream are in ../core
from IoTPy.core.agent import Agent
from IoTPy.core.stream import Stream, StreamArray, _no_value, _multivalue, run
# recent_values and run are in ../helper_functions
from IoTPy.helper_functions.recent_values import recent_values
#from run import run
# op is in ../agent_types
from IoTPy.agent_types.op import map_element, map_element_f
from IoTPy.agent_types.op import filter_element, filter_element_f
from IoTPy.agent_types.op import map_list, map_list_f
from IoTPy.agent_types.op import timed_window
from IoTPy.agent_types.basics import fmap_e, map_e

#                                     A SIMPLE EXAMPLE TEST
#------------------------------------------------------------------------------------------------
# This example is to illustrate the steps in the test.
# The later examples test several agents whereas this simple
# test only tests a single agent.
# The seven steps in this test may occur in different orders
# in the later tests.
class test_stream_size(unittest.TestCase):

    def test_example_1(self):
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
    unittest.main()
    
