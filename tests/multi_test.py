""" 
This module tests multi.py
"""

import sys
import os
sys.path.append(os.path.abspath("../"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../helper_functions"))


from agent import Agent
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import *
## from helper_functions.check_agent_parameter_types import *
## from helper_functions.recent_values import recent_values
from sink import sink_list
from op import *
from split import split_list, split_list_f
from merge import merge_list, merge_list_f
from multi import multi_element

def test_multi():
    scheduler = Stream.scheduler
    import numpy as np
    
    u = Stream('u')
    v = Stream('v')
    x = Stream('x')
    y = Stream('y')

    def f(a_list):
        return max(a_list), sum(a_list)

    multi_element(f, [u,v], [x,y])

    u.extend(range(8, 18, 2))
    v.extend(range(10, 14, 1))
    scheduler.step()
    assert recent_values(u) == [8, 10, 12, 14, 16]
    assert recent_values(v) == [10, 11, 12, 13]
    assert recent_values(x) == [10, 11, 12, 14]
    assert recent_values(y) == [18, 21, 24, 27]

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

    print "TEST OF MULTI IS SUCCESSFUL"

if __name__ == '__main__':
    test_multi()
