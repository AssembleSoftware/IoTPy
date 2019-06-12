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
from scipy.signal import butter
import numpy as np


class BP_IIR(object):
    """
    Bandpass IIR Filter

    Parameters
    ----------
    a, b: list of float
      Parameters that define an IIR filter

    Attributes
    ----------
    x, y: array of float
      Local variables of IIR calculations.

    """
    def __init__(self, a, b):
        assert len(b) == len(a)
        self.b = np.array(b)
        self.a = np.array(a)
        self.N = len(a)
        self.x = np.zeros(self.N)
        self.y = np.zeros(self.N)

    def filter_sample(self, sample):
        """
        This is the standard IIR calculation.
        Parameters
        ----------
        sample: float or int
          The next element of the stream.
        """
        # Shift x and y to the right by 1
        self.x[1:] = self.x[:- 1]
        self.y[1:] = self.y[:-1]
        # Update x[0] and y[0]
        self.x[0] = sample
        self.y[0] = self.a[0] * self.x[0]
        self.y[0] += sum(self.a[1:]*self.x[1:] - self.b[1:]*self.y[1:])
        return self.y[0]

    def filter_stream(self, in_stream, out_stream):
        """
        Filters the input stream to get the output stream
        using filter_sample().

        """
        map_element(self.filter_sample, in_stream, out_stream)

#------------------------------------------------------------------
# See scipy for bandpass filters.
# This code is taken from scipy.signal
def butter_bandpass(lowcut, highcut, fs, order=2):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter_stream(in_stream, out_stream, lowcut, highcut, fs, order):
    """
    Parameters
    ----------
    in_stream, out_stream: Stream
       The input and output streams of the agent
    low_cut, highcut: int or float
       The lower and upper frequencies of the bandpass filter.
    fs: int or float
       The sample rate in numer per second.
    order: int, positive
        The order of the filter.

    """
    # butter_bandpass is imported from scipy.sigal
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    bp = BP_IIR(b, a)
    bp.filter_stream(in_stream, out_stream)

def test():
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
    # sr: sample rate
    sr = 50
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
        sample_rate=sr, time_duration=td)
    wave_data_medium_frequency = generate_sine_wave(
        frequency=2.5, max_amplitude=ma, phase_shift=ps,
        sample_rate=sr, time_duration=td)
    wave_data_high_frequency = generate_sine_wave(
        frequency=15.0, max_amplitude=ma, phase_shift=ps,
        sample_rate=sr, time_duration=td)
    # Generate a wave that is the sum of pure-frequency
    # waves.
    wave_data_combined_frequencies = (
        wave_data_low_frequency +
        wave_data_medium_frequency +
        wave_data_high_frequency)

    # BANDPASS FILTER
    x = StreamArray('x')
    y = StreamArray('y')
    # Create a bandpass filter that operates on an input
    # stream x to produce the output stream y.
    bandpass_filter_stream(x, y, lowcut, highcut, sr, order)

    # Put data into the input stream of the filter.
    x.extend(wave_data_combined_frequencies)
    # Run a step and plot output.
    Stream.scheduler.step()
    # We now have streams x and y.
    # Next plot the recent values of streams x, y

    # Plot data
    before_filtering_data = recent_values(x)
    after_filtering_data = recent_values(y)
    plt.figure(1)
    plt.subplot(211)
    plt.plot(before_filtering_data)
    plt.subplot(212)
    plt.plot(after_filtering_data)
    plt.show()

if __name__ == '__main__':
    test()
    
    
    
