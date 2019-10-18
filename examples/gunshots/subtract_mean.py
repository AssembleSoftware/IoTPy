"""
Tests subtract_mean()

"""
import numpy as np
import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
from run import run
from basics import map_w, iot_w
from stream import StreamArray
from recent_values import recent_values

@iot_w
def subtract_mean(window, y):
    y.append( window[-1] - np.mean(window))

def test_subtract_mean():
    x = StreamArray('x', dtype=float)
    y = StreamArray('x', dtype=float)
    subtract_mean(x, window_size=2, step_size=1, y=y)
    x.extend(np.arange(5, dtype=float))
    run()
    print (recent_values(y))
    

if __name__ == '__main__':
    test_subtract_mean()
