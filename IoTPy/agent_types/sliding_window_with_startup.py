import numpy as np
import sys
sys.path.append("../core")
sys.path.append("../agent_types")
# agent, stream, helper_control, check_agent_parameter_types
# are in ../core.
from agent import Agent, InList
from stream import Stream, StreamArray, run
from helper_control import _no_value, _multivalue
from check_agent_parameter_types import *
# iot is in ../agent_types
from iot import iot

class sliding_window_with_startup(object):
    def __init__(self, func, in_stream, out_stream, window_size, step_size):
        self.func = func
        self.in_stream = in_stream
        self.out_stream = out_stream
        self.window_size = window_size
        self.step_size = step_size
        self.starting = True
        self.start_ptr = 0
        self.end_ptr = 0
        iot(func=self.extend, in_stream=self.in_stream)
    def extend(self, A):
        if self.starting:
            while self.end_ptr < len(A):
                self.end_ptr = self.end_ptr + self.step_size
                if self.end_ptr > self.window_size:
                    self.start_ptr = self.end_ptr - self.window_size
                window = A[self.start_ptr : self.end_ptr]
                self.out_stream.append(self.func(window))
            if self.end_ptr > self.window_size:
                self.starting = False
                return self.start_ptr + self.step_size
            else:
                return 0
        else:
            self.start_ptr = 0
            while self.start_ptr + self.window_size <= len(A):
                window = A[self.start_ptr : self.start_ptr + self.window_size]
                self.out_stream.append(self.func(window))
                self.start_ptr += self.step_size
            return self.start_ptr

    
    
    
