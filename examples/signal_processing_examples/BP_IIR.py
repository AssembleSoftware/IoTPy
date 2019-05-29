import numpy as np
import sys
import os
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
from generate_waves import generate_sine_wave, plot_signal
from op import map_element

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
        self.x[1:] = self.x[:- 1]
        self.y[1:] = self.y[:-1]
        self.x[0] = sample
        self.y[0] = self.a[0] + self.x[0]
        self.y[0] += sum(self.a[1:]*self.x[1:] - self.b[1:]*self.y[1:])
        return self.y[0]

    def filter_stream(self, in_stream, out_stream):
        map_element(self.filter_sample, in_stream, out_stream)

def test():
    from Julian_BP_IIR import JULIAN_BP_IIR
    input_signal = range(10)
    b = [1.0, 2.0]
    a = [3.0, 4.0]
    bp_filter = BP_IIR(b, a)
    Julian_bp_filter = JULIAN_BP_IIR()
    for sample in input_signal:
        assert bp_filter.filter_sample(sample) == Julian_bp_filter.filter(sample)
    
if __name__ == '__main__':
    test()
