import numpy as np
import sys
sys.path.append("../core")
sys.path.append("../helper_functions")
sys.path.append("../agent_types")
# agent, stream, helper_control, check_agent_parameter_types
# are in ../core.
from agent import Agent, InList
from stream import Stream, StreamArray, run
from helper_control import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
# iot, sliding_window_with_startup are in ../agent_types
from iot import iot
from sliding_window_with_startup import sliding_window_with_startup

def test_sliding_window_with_startup():
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
    test_sliding_window_with_startup()
