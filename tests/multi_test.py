""" 
This module tests multi.py
"""

import unittest

from IoTPy.core.agent import Agent
from IoTPy.core.stream import Stream, StreamArray
from IoTPy.core.stream import _no_value, _multivalue
from IoTPy.agent_types.check_agent_parameter_types import *
from IoTPy.helper_functions.recent_values import *
from IoTPy.agent_types.sink import sink_list
from IoTPy.agent_types.op import *
from IoTPy.agent_types.split import split_list, split_list_f
from IoTPy.agent_types.merge import merge_list, merge_list_f
from IoTPy.agent_types.multi import multi_element, multi_list, multi_window
from IoTPy.agent_types.multi import multi_element_f


class test_multi(unittest.TestCase):
    def test_multi(self):
        scheduler = Stream.scheduler
        import numpy as np
        
        u = Stream('u')
        v = Stream('v')
        x = Stream('x')
        y = Stream('y')

        def f(a_list):
            return max(a_list), sum(a_list)

        multi_element(f, [u,v], [x,y])

        u.extend(list(range(8, 18, 2)))
        v.extend(list(range(10, 14, 1)))
        scheduler.step()
        assert recent_values(x) == [10, 11, 12, 14]
        assert recent_values(y) == [18, 21, 24, 27]

        
        u = Stream('u')
        v = Stream('v')

        def f(a_list):
            return max(a_list), sum(a_list)

        x, y = multi_element_f(f, [u,v], num_out_streams=2)

        u.extend(list(range(8, 18, 2)))
        v.extend(list(range(10, 14, 1)))
        scheduler.step()
        assert recent_values(x) == [10, 11, 12, 14]
        assert recent_values(y) == [18, 21, 24, 27]

        

        # test of single input and single output
        u = Stream('u')
        x = Stream('x')
        
        def f(lst):
            return [lst[0]*2]

        multi_element(f, [u], [x])
        
        u.extend(list(range(5)))
        scheduler.step()
        assert recent_values(x) == [0, 2, 4, 6, 8]

        # Test StreamArray
        u = StreamArray('u')
        v = StreamArray('v')
        x = StreamArray('x')
        y = StreamArray('y')
        z = StreamArray('z')

        def f(a_list):
            return max(a_list), np.mean(a_list), min(a_list)

        multi_element(f, [u,v], [x,y,z])

        u.extend(np.arange(5.0))
        v.extend(np.arange(10., 16., 1.))
        scheduler.step()
        assert np.array_equal(
            recent_values(u), np.array([0.0, 1.0, 2.0, 3.0, 4.0]))
        assert np.array_equal(
            recent_values(v), np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0]))
        assert np.array_equal(
            recent_values(x), np.array([10.0, 11.0, 12.0, 13.0, 14.0]))
        assert np.array_equal(
            recent_values(y), np.array([5.0, 6.0, 7.0, 8.0, 9.0]))
        assert np.array_equal(
            recent_values(z), np.array([0.0, 1.0, 2.0, 3.0, 4.0]))

        # Test StreamArray, dtype=int
        u = StreamArray('u', dtype=int)
        v = StreamArray('v', dtype=int)
        x = StreamArray('x', dtype=int)
        y = StreamArray('y', dtype=int)

        def f(a_list):
            return max(a_list), sum(a_list)+min(a_list)

        multi_element(f, [u,v], [x,y])

        u.extend(np.arange(5))
        v.extend(np.arange(10, 17, 1))
        scheduler.step()

        assert np.array_equal(
            recent_values(u), np.array([0, 1, 2, 3, 4]))
        assert np.array_equal(
            recent_values(v), np.array([10, 11, 12, 13, 14, 15, 16]))
        assert np.array_equal(
            recent_values(x), np.array([10, 11, 12, 13, 14]))
        assert np.array_equal(
            recent_values(y), np.array([10, 13, 16, 19, 22]))


        def f_multi_window(pair_of_windows):
            window_0, window_1 = pair_of_windows
            output_0 = sum(window_0) + sum(window_1)
            output_1 = max(window_0) + max(window_1)
            return (output_0, output_1)
        w = Stream('w')
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        multi_window(
            func=f_multi_window, in_streams=[w,x],
            out_streams=[y,z], window_size=2, step_size=2,
            state=None, name='multi_window_agent')
        
        w.extend(list(range(10)))
        x.extend(list(range(100, 120, 2)))
        
        scheduler.step()
        assert recent_values(y) == [203, 215, 227, 239, 251]
        assert recent_values(z) == [103, 109, 115, 121, 127]

        print ("TEST OF MULTI IS SUCCESSFUL")

if __name__ == '__main__':
    unittest.main()