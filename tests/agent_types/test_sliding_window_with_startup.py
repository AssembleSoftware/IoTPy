import numpy as np
import sys
import unittest
# agent, stream, helper_control, check_agent_parameter_types
# are in ../core.
from IoTPy.core.agent import Agent, InList
from IoTPy.core.stream import Stream, StreamArray, run
from IoTPy.core.helper_control import _no_value, _multivalue
from IoTPy.agent_types.check_agent_parameter_types import *
from IoTPy.helper_functions.recent_values import recent_values
# iot, sliding_window_with_startup are in ../agent_types
from IoTPy.agent_types.iot import iot
from IoTPy.agent_types.sliding_window_with_startup import sliding_window_with_startup

class test_sliding_window_with_startup(unittest.TestCase):
    def test_sliding_window_with_startup(self):
        x = StreamArray(dtype=int)
        y = StreamArray(dtype=int)
        sw = sliding_window_with_startup(
            func=np.sum, in_stream=x, out_stream=y, window_size=10, step_size=3)
        # tests
        x.extend(np.arange(6, dtype=int))
        run()
        assert np.array_equal(recent_values(y), np.array([3, 15]))
        x.extend(np.arange(6, 9, dtype=int))
        run()
        assert np.array_equal(recent_values(y), np.array([3, 15, 36]))
        x.extend(np.arange(9, 15, dtype=int))
        run()
        assert np.array_equal(
            recent_values(y),
            np.array([3,  15,  36,  65,  95]))
        x.extend(np.arange(15, 30, dtype=int))
        run()
        assert np.array_equal(
            recent_values(y),
            np.array([3,  15,  36,  65,  95, 125, 155, 185, 215, 245]))


if __name__ == '__main__':
    unittest.main()