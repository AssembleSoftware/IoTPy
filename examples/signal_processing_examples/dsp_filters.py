import scipy.signal
import numpy as np
import sys
"""
This module shows how to use map_element in IoTPy
to build a library of classes for filtering streams
by encapsulating software from scipy.signal and
other software libraries.

The module consists of a base Filter class and
specific filters --- such as bandpass IIR filters ---
that are subclasses of Filter.

"""
import os
import matplotlib.pyplot as plt
from scipy.signal import butter, firwin
import numpy as np

sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
from generate_waves import generate_sine_wave, plot_signal
# stream is in core
from stream import Stream, StreamArray
# op is in agent_types
from op import map_window_list, map_element
from merge import merge_window
# recent_values is in helper_functions
from recent_values import recent_values
from window_dot_product import window_dot_product


def reverse_array(b):
    """
    Reverse array b. Same as numpy.flip
    Parameters
    ----------
       b: list or array
    Returns
    -------
       reverse_b: array
          flips b.
          If b is [0, 1, 2] then reverse_b is [2, 1, 0]

    """
    b = np.array(b)
    M = len(b)
    reverse_b = np.zeros(M)
    for i in range(M):
        reverse_b[i] = b[M - 1 - i]
    return reverse_b

def bandpass_FIR(in_stream, out_stream, b):
    """
    Creates an agent that executes a
    FIR (Finite Impulse Response) filter of
    in_stream to produce out_stream using
    filter parameter b.
    Parameters
    ----------
       in_stream: Stream
       out_stream: Stream
       b: array
    Note
    ----
    out_stream[n] = sum over k in [0, M] of b[k]*in_stream[n-k]
    Therefore, setting k to M-k:
    out_stream[n] = sum over k in [0, M] of b[M-k]*in_stream[n-M+k]
    So, out_stream[n] is the dot product of the reverse of b and
    the in_stream window consisting of: in_stream[n-M]... in_stream[M].

    """
    reverse_b = reverse_array(b)
    window_dot_product(
        in_stream, out_stream,
        multiplicand_vector=reverse_b)

def bandpass_IIR(in_stream, out_stream, b, a):
    """
    Creates an agent that executes a
    IIR (Infinite Impulse Response) filter of
    in_stream to produce out_stream using
    filter parameters b, a.
    Parameters
    ----------
       in_stream: Stream
       out_stream: Stream
       b: array
       a: array
    Note
    ----
       out_stream[n] = B - A where
       B is sum of k over [0, .., M] of b[k]*in_stream[n-k]
       A is sum of k over [1,..., M] of a[k]*out_stream[n-k]
       We convert these equations to equations over windows
       starting at the index n-M, by substituting M-k for k to get:
       B is sum of k over [0, .., M] of b[M-k]*in_stream[n-M+k]
       A is sum of k over [0,..., M-1] of a[M-k]*out_stream[n-M+k]
       The window operations in function f implement these
       equations.
       
    """
    def f(windows, b, a):
        x_window, y_window = windows
        return sum(b*x_window) - sum(a*y_window[1:])
    reverse_b = reverse_array(b)
    reverse_a = reverse_array(a[1:])
    M = len(b)
    # Initialize the streams so that windows of size M
    # can be merged.
    out_stream.extend(np.zeros(M))
    in_stream.extend(np.zeros(M))
    # Create the agent.
    # Note that the output stream of the
    # agent gets fed back as an input stream.
    merge_window(
        func=f, in_streams=[in_stream, out_stream],
        out_stream=out_stream,
        window_size=M, step_size=1, b=reverse_b, a=reverse_a)

#---------------------------------------------------------------
#---------------------------------------------------------------
#     EXAMPLES OF CLASS BASED FILTERS
#---------------------------------------------------------------
#---------------------------------------------------------------

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
      x[0] is the most recent value. For example if
      the current value of in_stream is:
      in_stream[j-N+1, ... j] then
      x[k] = in_stream[j - k]
      x is initialized to 0.
    y: array of float
      The N most recent values of the output stream.
      Initialized to 0.
      y and x have the same structure.

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
        The formula must be entered for the subclass
        derived from the base Filter class.

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
# CLASS BANDPASS IIR FILTER
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
        # Insert a new value -- element --- into x.
        # First shift x to the right by 1.
        self.x[1:] = self.x[:- 1]
        self.x[0] = element
        
        # Insert a new value into y.
        # First shift y to the right by 1.
        self.y[1:] = self.y[:-1]
        # Compute new value for y[0]
        self.y[0] = self.b[0] * self.x[0]
        self.y[0] += sum(self.b[1:]*self.x[1:] -
                         self.a[1:]*self.y[1:])
        return self.y[0]


#---------------------------------------------------------------
# CLASS BANDPASS FIR FILTER
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

def reverse_array(b):
    b = np.array(b)
    M = len(b)
    reverse_b = np.zeros(M)
    for i in range(M):
        reverse_b[i] = b[M - 1 - i]
    return reverse_b

def bandpass_FIR(in_stream, out_stream, b):
    reverse_b = reverse_array(b)
    window_dot_product(
        in_stream, out_stream,
        multiplicand_vector=reverse_b)

def bandpass_IIR(in_stream, out_stream, b, a):
    def f(windows, b, a):
        x_window, y_window = windows
        return sum(b*x_window) - sum(a*y_window[1:])
    reverse_b = reverse_array(b)
    reverse_a = reverse_array(a[1:])
    M = len(b)
    out_stream.extend(np.zeros(M))
    in_stream.extend(np.zeros(M))
    merge_window(
        func=f, in_streams=[in_stream, out_stream],
        out_stream=out_stream,
        window_size=M, step_size=1, b=reverse_b, a=reverse_a)

        
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
    # Set up parameters
    fs, order, lowcut, highcut, input_signal = setup_parameters()
    x = StreamArray('x')
    y = StreamArray('y')
    # Create bandpass filter 
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    BP_IIR(b, a).filter_stream(in_stream=x, out_stream=y)
    # Plot output
    drive_input_and_plot_output(input_signal, x, y)

def test_bandpass_FIR_filter():
    # Set up parameters
    fs, order, lowcut, highcut, input_signal = setup_parameters()
    x = StreamArray('x')
    y = StreamArray('y')
    # Create a bandpass filter.
    b = fir_bandpass(lowcut, highcut, fs)
    BP_FIR(b).filter_stream(in_stream=x, out_stream=y)
    # Plot output
    drive_input_and_plot_output(input_signal, x, y)
    
def test_bandpass_FIR_filter_simple():
    # Set up parameters
    fs, order, lowcut, highcut, input_signal = setup_parameters()
    x = StreamArray('x')
    y = StreamArray('y')
    # Create a bandpass filter.
    b = fir_bandpass(lowcut, highcut, fs)
    bandpass_FIR(in_stream=x, out_stream=y, b=b)
    # Plot output
    drive_input_and_plot_output(input_signal, x, y)

def test_bandpass_IIR_filter_simple():
    # Set up parameters
    fs, order, lowcut, highcut, input_signal = setup_parameters()
    x = StreamArray('x')
    y = StreamArray('y')
    # Create a bandpass filter.
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    bandpass_IIR(in_stream=x, out_stream=y, b=b, a=a)
    # Plot output
    drive_input_and_plot_output(input_signal, x, y)
    

#------------------------------------------------------------------
#  TESTS
#------------------------------------------------------------------
if __name__ == '__main__':
    print 'TESTING BANDPASS IIR FILTER'
    test_bandpass_IIR_filter()
    print
    print 'TESTING BANDPASS FIR FILTER'
    test_bandpass_FIR_filter()
    print
    print 'TESTING BANDPASS FIR FILTER SIMPLE'
    test_bandpass_FIR_filter_simple()
    print
    print 'TESTING BANDPASS IIR FILTER SIMPLE'
    test_bandpass_IIR_filter_simple()
    
    
    
