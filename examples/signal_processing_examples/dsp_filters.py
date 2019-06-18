import scipy.signal
import numpy as np
import sys
import os
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath("../gunshots"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
from generate_waves import generate_sine_wave, plot_signal
from BP_IIR import BP_IIR
from stream import Stream, StreamArray
from op import map_window_list, map_element
from recent_values import recent_values
from scipy.signal import butter, firwin
import numpy as np

#---------------------------------------------------------------
# FILTER BASE CLASS
#---------------------------------------------------------------
class Filter(object):
    """
    The base class of filters that filter input streams to
    produc output streams.
    Uses a, b parameters from scipy.signal or other libraries.

    Parameters
    ----------
    a, b: list of float
      Parameters that define a filter.
      For a Finite Impulse Response filter, a is None.

    Attributes
    ----------
    N: int
      the length of b
    x: array of float
      The N most recent values of the input stream.
      Initialized to 0.
    y: array of float
      The N most recent values of the output stream.
      Initialized to 0.

    """
    def __init__(self, b, a=None):
        self.b = np.array(b)
        if a is not None:
            self.a = np.array(a)
        self.N = len(b)
        self.x = np.zeros(self.N)
        self.y = np.zeros(self.N)

    def filter_element(self, element):
        """
        This is the standard filter calculation.
        The formula depends on the type of filter.
        The formula must be entered for the derived class.

        Parameters
        ----------
        element: float or int
          The next element of the stream.
        """
        pass

    def filter_stream(self, in_stream, out_stream):
        """
        Filters the input stream to get the output stream using
        the function filter_element.

        """
        map_element(self.filter_element, in_stream, out_stream)

#---------------------------------------------------------------
# BANDPASS IIR FILTER
#---------------------------------------------------------------
class BP_IIR(Filter):
    """
    Bandpass IIR (Infinite Impulse Response) Filter.

    Parameters
    ----------
       a, b: float or int
          Filter parameters obtained from scipy.signal.butter
          or other sources.

    """
    def __init__(self, b, a):
        Filter.__init__(self, b, a)

    def filter_element(self, element):
        """
        Uses a standard formula for IIR filters.
        Shifts x, y to the right by 1 to accomodate
        new entry for input x, and then updates y[0].

        """
        # Accomodate new entry, element, in input
        # stream x.
        self.x[1:] = self.x[:- 1]
        self.x[0] = element
        # Save y[0,...,N-2] in y[1,...,N-1]
        self.y[1:] = self.y[:-1]
        # Update y[0]
        self.y[0] = self.b[0] * self.x[0]
        self.y[0] += sum(self.b[1:]*self.x[1:] -
                         self.a[1:]*self.y[1:])
        
        return self.y[0]


#---------------------------------------------------------------
# BANDPASS FIR FILTER
#---------------------------------------------------------------
class BP_FIR(Filter):
    """
    Bandpass FIR (Finite Impulse Response) Filter.

    Parameters
    ----------
       b: float or int
          Filter parameters obtained from scipy.signal.butter
          or other sources.

    """
    def __init__(self, b):
        Filter.__init__(self, b)

    def filter_element(self, element):
        """
        Uses a standard formula for FIR filters.
        Shifts x, y to the right by 1 to accomodate
        new entry for input x, and compute output.

        """
        # Accomodate new entry, element, in input
        # stream x.
        self.x[1:] = self.x[:- 1]
        self.x[0] = element
        return np.sum(self.b * self.x)

        
#---------------------------------------------------------------
#  GET FILTER PARAMETERS
#---------------------------------------------------------------
# See scipy.signal for a library of filters.
def butter_bandpass(lowcut, highcut, fs, order=2):
    """
    Butterworth IIR filter.
    butter() is from scipy.signal

    """
    lowcut, highcut = lowcut*2.0/fs, highcut*2.0/fs
    b, a = butter(order, [lowcut, highcut], btype='band')
    return b, a

def fir_bandpass(lowcut, highcut, fs):
    """
    FIR filter.
    firwin() is from scipy.signal

    """
    lowcut, highcut =lowcut*2.0/fs, highcut*2.0/fs
    b =  firwin(
        numtaps=201, cutoff = [lowcut, highcut],
        window='blackmanharris', pass_zero=False)
    return b 


#----------------------------------------------------------------
#       TESTS
#----------------------------------------------------------------
def generate_test_waves(
        low_frequency, medium_frequency, high_frequency,
        max_amplitude, phase_shift, sample_rate, time_duration):
    # Generate streams of waves with different frequencies,
    # amplitudes and phase shifts. Each wave is a pure
    # frequency. Return a wave that combines frequencies.
    wave_data_low_frequency = generate_sine_wave(
        low_frequency, max_amplitude, phase_shift,
        sample_rate, time_duration)
    wave_data_medium_frequency = generate_sine_wave(
        medium_frequency, max_amplitude, phase_shift,
        sample_rate, time_duration)
    wave_data_high_frequency = generate_sine_wave(
        high_frequency, max_amplitude, phase_shift,
        sample_rate, time_duration)
    # Generate a wave that is the sum of pure-frequency
    # waves.
    return (wave_data_low_frequency +
            wave_data_medium_frequency +
            wave_data_high_frequency)
    
def drive_input_and_plot_output(
        input_signal, x, y):
        # Put data into the input stream of the filter.
    x.extend(input_signal)
    # Run a step and plot output.
    Stream.scheduler.step()
    # We now have values in in_stream and out_stream.
    # Next plot the recent values of the streams

    # Get the most recent values of streams x, y.
    before_filtering_data = recent_values(x)
    after_filtering_data = recent_values(y)
    # Plot
    plt.figure(1)
    plt.subplot(211)
    plt.plot(before_filtering_data)
    plt.subplot(212)
    plt.plot(after_filtering_data)
    plt.show()
    
    
def setup_parameters():
    """
    This test generates waves with low, medium and high
    frequency, and sums these three waves to get a combined
    frequency wave. Then it puts the combined frequency
    wave through a bandpass filter which passes only the
    medium-frequency wave through.

    The output plot has the combined frequency wave in the
    first subplot and the filter output in the second subplot.

    """
    # SET PARAMETERS
    # fs: sample rate
    # order: order of the filter
    # lowcut, highcut: lower and upper thresholds of a bandpass
    # filter.
    fs, order, lowcut, highcut = 50.0, 2, 1.0, 5.0
    input_signal = generate_test_waves(
        low_frequency=0.25, medium_frequency=2.5, high_frequency=15.0,
        max_amplitude=1, phase_shift=0.0, sample_rate=fs,
        time_duration=10.0)

    return fs, order, lowcut, highcut, input_signal

def test_bandpass_IIR_filter():
    fs, order, lowcut, highcut, input_signal = setup_parameters()
    x = StreamArray('x')
    y = StreamArray('y')
    
    # Create a bandpass filter that operates on an input
    # stream x to produce the output stream y. This
    # filter uses butter() from scipy.
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    BP_IIR(b, a).filter_stream(in_stream=x, out_stream=y)

    drive_input_and_plot_output(input_signal, x, y)

def test_bandpass_FIR_filter():
    fs, order, lowcut, highcut, input_signal = setup_parameters()
    x = StreamArray('x')
    y = StreamArray('y')
    # Create a bandpass filter that operates on an input
    # stream x to produce the output stream y. This filter
    # uses firwin() from scipy.signal
    b = fir_bandpass(lowcut, highcut, fs)
    BP_FIR(b).filter_stream(in_stream=x, out_stream=y)

    drive_input_and_plot_output(input_signal, x, y)

if __name__ == '__main__':
    print 'TESTING BANDPASS IIR FILTER'
    test_bandpass_IIR_filter()
    print
    print 'TESTING BANDPASS FIR FILTER'
    test_bandpass_FIR_filter()
    
    
    
