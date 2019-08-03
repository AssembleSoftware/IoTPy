import numpy as np
import sys
import os
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
from generate_waves import generate_sine_wave, plot_signal
from op import map_element
from stream import Stream

'''
Mani Chandy modified Julian Bunn's code to use numpy.

/**************************************************************
WinFilter version 0.8
http://www.winfilter.20m.com
akundert@hotmail.com

Filter type: Band Pass
Filter model: Butterworth
Filter order: 2
Sampling Frequency: 50 Hz
Fc1 and Fc2 Frequencies: 1.000000 Hz and 5.000000 Hz
Coefficents Quantization: float

Z domain Zeros
z = -1.000000 + j 0.000000
z = -1.000000 + j 0.000000
z = 1.000000 + j 0.000000
z = 1.000000 + j 0.000000

Z domain Poles
z = 0.664888 + j -0.356810
z = 0.664888 + j 0.356810
z = 0.922500 + j -0.112897
z = 0.922500 + j 0.112897
***************************************************************/
'''
import numpy as np
class BP_IIR(object):
    def __init__(self, b, a):
        assert len(b) == len(a)
        self.b = np.array(b)
        self.a = np.array(a)
        self.N = len(a)
        self.x = np.zeros(self.N)
        self.y = np.zeros(self.N)

    def filter_sample(self, sample):
        # Shift x and y to the right by 1
        self.x[1:] = self.x[:- 1]
        self.y[1:] = self.y[:-1]
        # Update x[0] and y[0]
        self.x[0] = sample
        self.y[0] = self.a[0] * self.x[0]
        self.y[0] += sum(self.a[1:]*self.x[1:] - self.b[1:]*self.y[1:])
        return self.y[0]

    def filter_stream(self, in_stream, out_stream):
        map_element(self.filter_sample, in_stream, out_stream)

def test():
    from Julian_BP_IIR import JULIAN_BP_IIR
    input_signal = range(10)
    ACoef = [
        0.05421678111120047800,
        0.00000000000000000000,
        -0.10843356222240096000,
        0.00000000000000000000,
        0.05421678111120047800
    ]

    BCoef = [
        1.00000000000000000000,
        -3.17477731945540590000,
        3.88658158501960840000,
        -2.19912328951123470000,
        0.49181223722250506000
    ]
    bp_filter = BP_IIR(b=BCoef, a=ACoef)
    x = Stream('x')
    y = Stream('y')
    bp_filter.filter_stream(in_stream=x, out_stream=y)
    x.extend()
    Stream.scheduler.step()
    
if __name__ == '__main__':
    test()
