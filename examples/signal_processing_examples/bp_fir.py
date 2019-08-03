import sys
import os
from scipy.signal import firwin, lfilter
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))


from generate_waves import generate_sine_wave
from op import map_element
from stream import Stream, StreamArray
from recent_values import recent_values

def bandpass_filter_stream(in_stream, out_stream,
                         lowcut, highcut, fs):

    fs = float(fs)
    low_cut = lowcut*2/fs              # Normalising the filter band values to values between 0 and 1
    high_cut = highcut*2/fs
    b =  firwin(1001, cutoff = [low_cut, high_cut], window='blackmanharris', pass_zero=False)
    print 'b is ', b
    bp = BP_FIR(b)
    bp.filter_stream(in_stream, out_stream)


def fir_bandpass_filter(lowcut, highcut, fs):

    fs = float(fs)
    low_cut = lowcut*2/fs              # Normalising the filter band values to values between 0 and 1
    high_cut = highcut*2/fs
    b =  firwin(1001, cutoff = [low_cut, high_cut], window='blackmanharris', pass_zero=False)
    return b 


class BP_FIR(object):
    """ 
    Bandpass FIR Filter
    
    Parameters
    ----------
    b: array_like, float
    This parameter defines the FIR Filter. We use 
    SciPy's firwin to compute this. 
    
    Attributes   
    ----------
    x, y: array of float
      Local variables of FIR calculations.
      
    References
    ----------
    [1]. https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.filtfilt.html
    [2]. https://github.com/gatitoneku/WAV-Audio-Bandpass-Filter-FIR-Windowing-Method-
    
    Notes
    -----
    1. Do note that there will be a difference in phase (or equivalently, a time delay, because the implementation is
       equivalent to SciPy's lfilter implementation. For a better implementation, we need
       to implement SciPy's filtfilt, on a streaming setting.

    """
    
    
    def __init__(self, b):
        self.b = b
        self.a = [1]
        self.x = []
        self.y = []
        self.M = len(b)
        
    def filter_sample(self, sample):
        """
        This method is equivalent to the lfilter from SciPy
        """

        self.x.append(sample)
        for n in range(len(self.x)-1, len(self.x)):
            temp=0
            for k in range(self.M):
                if n-k<0:
                    break
                else:
                    temp+=self.b[k]*self.x[n-k]
            self.y.append(temp)
        return self.y[-1]
    
    def filter_stream(self, in_stream, out_stream):
        """
        Filters the input stream to get the output stream
        using filter_sample().

        """
        map_element(self.filter_sample, in_stream, out_stream)
    

def test1():
    
    input_data = np.arange(10)+1
    b =np.array([2.0,5.0])

    for sample in input_data:

        bp_fir = BP_FIR(b)
        val_scipy = lfilter(b, [1], np.array([sample]))[0]
        val_manual = bp_fir.filter_sample(sample)
        
        try:
            assert val_scipy == val_manual

        except AssertionError:

            print("Manual is, ",val_manual)
            print("SciPy is", val_scipy)


def test2():# SET PARAMETERS
    # fs: sample rate
    fs = 50
    # ma: maximum amplitude
    ma = 1
    # ps: phase shift
    ps = 0.0
    # td: time duration
    td = 10.0
    # or: order
    order = 2
    lowcut = 1
    highcut = 5

    # GENERATE WAVES
    # Generate streams of waves with different frequencies,
    # amplitudes and phase shifts. Each wave is a pure
    # frequency.
    wave_data_low_frequency = generate_sine_wave(
        frequency=0.25, max_amplitude=ma, phase_shift=ps,
        sample_rate=fs, time_duration=td)
    wave_data_medium_frequency = generate_sine_wave(
        frequency=2.5, max_amplitude=ma, phase_shift=ps,
        sample_rate=fs, time_duration=td)
    wave_data_high_frequency = generate_sine_wave(
        frequency=15.0, max_amplitude=ma, phase_shift=ps,
        sample_rate=fs, time_duration=td)
    # Generate a wave that is the sum of pure-frequency
    # waves.
    wave_data_combined_frequencies = (
        wave_data_low_frequency +
        wave_data_medium_frequency +
        wave_data_high_frequency)

    # -----------------------------------------------------------
    # TEST BANDPASS FIR FILTER
    # -----------------------------------------------------------
    x = StreamArray('x')
    y = StreamArray('y')
    ## # Create a bandpass filter that operates on an input
    ## # stream x to produce the output stream y. This filter
    ## # uses firwin() from scipy.signal
    ## b = fir_bandpass(lowcut, highcut, fs)
    ## BP_FIR(b).filter_stream(in_stream=x, out_stream=y)

    # Create a bandpass filter that operates on an input
    # stream x to produce the output stream y.
    bandpass_filter_stream(x, y, lowcut, highcut, fs)

    # Feed the input to the filter with combined frequencies.
    x.extend(wave_data_combined_frequencies)
    # Run a step and plot output.
    Stream.scheduler.step()
    y.extend(wave_data_medium_frequency)
    before_filtering_data = recent_values(x)
    after_filtering_data = recent_values(y)

    # Plot data
    print 'PLOTTING FIR FILTER'
    before_filtering_data = recent_values(x)
    after_filtering_data = recent_values(y)
    plt.figure(1)
    plt.subplot(211)
    plt.plot(before_filtering_data)
    plt.subplot(212)
    plt.plot(after_filtering_data)
    plt.show()


if __name__=='__main__':
    ## print("First Test Now.. ")
    ## print("If assertion failed, then issue")
    ## test1()
    print("Test1 Done\n\n")
    print("Test2 Now ")
    test2()
    print("Test2 Done")
