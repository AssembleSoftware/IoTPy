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
from stream import Stream, StreamArray
from op import map_window_list
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
# Streaming filters on arrays
def bandpass_stream(
        filter, in_stream, out_stream, window_size,
        step_size, lowcut, highcut, fs, order=5):
    def f(data):
        y = filter(data, lowcut, highcut, fs, order)
        return y[:step_size]
    map_window_list(
        f, in_stream, out_stream,
        window_size=window_size, step_size=window_size)
        #lowcut=lowcut, highcut=highcut, fs=fs, order=order)

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
    sr = 10000
    # ma: maximum amplitude
    ma = 1
    # ps: phase shift
    ps = 0.0
    # td: time duration
    td = 0.2
    # or: order
    order = 6
    wave_data_low_frequency = generate_sine_wave(
        frequency=8, max_amplitude=ma, phase_shift=ps,
        sample_rate=sr, time_duration=td)
    wave_data_medium_frequency = generate_sine_wave(
        frequency=256, max_amplitude=ma, phase_shift=ps,
        sample_rate=sr, time_duration=td)
    wave_data_high_frequency = generate_sine_wave(
        frequency=2048, max_amplitude=ma, phase_shift=ps,
        sample_rate=sr, time_duration=td)
    wave_data_combined_frequencies = (
        wave_data_low_frequency +
        wave_data_medium_frequency +
        wave_data_high_frequency)
        
    x = StreamArray('x')
    y = StreamArray('y')
    bandpass_stream(
        filter=butter_bandpass_filter,
        in_stream=x, out_stream=y, window_size=1024, step_size=128,
        lowcut=64, highcut=512, fs=sr, order=order)
    x.extend(wave_data_combined_frequencies)
    Stream.scheduler.step()

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
    
    
    
