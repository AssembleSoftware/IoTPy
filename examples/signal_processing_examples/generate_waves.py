"""
Functions that return a NumPy array containing a wave such as
a sine wave or square wave.

Parameters
----------
  frequency: int or float
     wave frequency in Hertz (1/second)
  max_amplitude: float
     The maximum amplitude of the wave
  phase_shift: float
     Initial phase of the wave
  sample_rate: int or float
     Number of samples per second of the waveform
  time_duration: int or float
     The time, in seconds, of the output wave.

Variables
---------
    num_samples is the size of the output array
    time_sequence is an array [0, v, 2*v, .... num_samples*v] where
        (num_samples + 1)*v == time_duration.
"""
import numpy as np
import matplotlib.pyplot as plt

def generate_trignometric_wave(
        func, frequency, max_amplitude,
        phase_shift, sample_rate, time_duration):
    num_samples = int(time_duration * sample_rate)
    time_sequence = np.linspace(0, time_duration, num_samples, endpoint=False)
    return max_amplitude*func(2*np.pi*frequency*time_sequence + phase_shift)

def generate_sine_wave(
        frequency, max_amplitude, phase_shift,
        sample_rate, time_duration):
    return generate_trignometric_wave(
        np.sin, frequency, max_amplitude, phase_shift,
        sample_rate, time_duration)

def generate_cosine_wave(
        frequency, max_amplitude, phase_shift,
        sample_rate, time_duration):
    return generate_trignometric_wave(
        np.cos, frequency, max_amplitude, phase_shift,
        sample_rate, time_duration)

def generate_square_wave(
        frequency, max_amplitude,
        phase_shift, sample_rate, time_duration):
    num_samples = time_duration * sample_rate
    time_sequence = np.linspace(0, time_duration, num_samples, endpoint=False)
    def func(v):
        return - np.sign((v - v.astype(int)) - 0.45)
    return max_amplitude*func(frequency*time_sequence + phase_shift)


def plot_signal(signal, time_duration, sample_rate):
    plt.figure(1)
    plt.clf()
    num_samples = time_duration * sample_rate
    time_sequence = np.linspace(0, time_duration, num_samples, endpoint=False)
    plt.plot(time_sequence, signal)
    plt.show()
    return

# TESTS

def test():
    # Plot
    frequency = 1.0
    max_amplitude = 1.0
    phase_shift = 0.0
    sample_rate = 100
    time_duration = 2


    signal = generate_square_wave(frequency, max_amplitude, phase_shift, sample_rate, time_duration)
    plot_signal(signal, time_duration, sample_rate)

    phase_shift = np.pi/2.0 # 90 degrees 
    signal = generate_sine_wave(frequency, max_amplitude, phase_shift, sample_rate, time_duration)
    plot_signal(signal, time_duration, sample_rate)

    signal = generate_cosine_wave(frequency, max_amplitude, phase_shift, sample_rate, time_duration)
    plot_signal(signal, time_duration, sample_rate)

if __name__ == '__main__':
    test()
