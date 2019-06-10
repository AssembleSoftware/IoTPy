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
from scipy.signal import butter, filtfilt

#------------------------------------------------------------------
# See scipy for bandpass filters.
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

#-------------------------------------------------------------------------
# Filters using second order sections (sos). See scipy.
# sos filters give better response.
def butter_bandpass_sos(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = butter(order, [low, high], analog=False,
                 btype='band', output='sos')
    return sos
 
def butter_bandpass_filter_sos(
        in_stream, lowcut, highcut, fs, order=5):
    in_stream = np.array(in_stream)
    sos = butter_bandpass(lowcut, highcut, fs, order=order)
    y = sosfiltfilt(sos, in_stream)
    return y

#---------------------------------------------------------------
# Streaming filters on windows (i.e. arrays)
def bandpass_window_stream(
        filter, in_stream, out_stream, window_size,
        step_size, lowcut, highcut, fs, order=5):
    def f(data):
        y = filter(data, lowcut, highcut, fs, order)
        return y[:step_size]
    map_window_list(
        f, in_stream, out_stream,
        window_size=window_size, step_size=window_size)

# Filtering streams continuously (no windows).
def bandpass_filter_stream(in_stream, out_stream,
                         lowcut, highcut, fs, order=5):
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
    # Generate streams of waves with different frequencies,
    # amplitudes and phase shifts.
    wave_data_low_frequency = generate_sine_wave(
        frequency=0.25, max_amplitude=ma, phase_shift=ps,
        sample_rate=sr, time_duration=td)
    wave_data_medium_frequency = generate_sine_wave(
        frequency=2.5, max_amplitude=ma, phase_shift=ps,
        sample_rate=sr, time_duration=td)
    wave_data_high_frequency = generate_sine_wave(
        frequency=25.0, max_amplitude=ma, phase_shift=ps,
        sample_rate=sr, time_duration=td)
    # Generate wave that is the sum of pure-frequency
    # waves.
    wave_data_combined_frequencies = (
        wave_data_low_frequency +
        wave_data_medium_frequency +
        wave_data_high_frequency)


    x = StreamArray('x')
    y = StreamArray('y')
    # Create a bandpass filter that operates on an input
    # stream x to produce the output stream y.
    bandpass_filter_stream(
        in_stream=x, out_stream=y,
        lowcut=1.0, highcut=5.0, fs=sr, order=order)
    # Feed the input to the filter with combined frequencies.
    x.extend(wave_data_combined_frequencies)
    # Run a step and plot output.
    Stream.scheduler.step()
    print recent_values(y)[:20]
    print

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
    
    
    
