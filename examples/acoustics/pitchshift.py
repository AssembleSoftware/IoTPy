"""
This code is a streaming version of code written by Zulko who
created the 'pianoputer.' All the ideas are from Zulko's
version. All we do here is show how to convert code for an
array into code for a stream.

To play music, download sounddevice.

A problem encountered when switching from arrays to streams
is that code operating on an array can use metrics --- such as
maximum --- over the entire array, whereas code operating on
streams has to compute pitch shift based on the available
data up to that point. For the streaming version we assume
that the maximum over the entire array is 4096.0 (See the
last lines of stretch in which result is computed). A poor
assumption of the maximum may result in clipping or numerical
problems.

This code has both the original version (modified with max
assumed to be 4096) and the streaming version so that you
can see how one is converted into the other. speedx and
stretch are from the original version, while the method
Stretch.stretch is the streaming version.

The repository includes a short wav file called 'guitar.wav'
If you run test_pitchshift you will hear the sound shifted
to a lower pitch, then the original sound, and then the sound
shifted to a higher pitch. In each case you will first hear
the sound created by original version (modified by assuming
max is 4096) and the streaming version.

The streaming code was written by Deepak Narayanan and Mani
Chandy. The Stretch.stretch() function is based on Zulko's
code.

"""

#!/usr/bin/env python
import sys
import os
import numpy as np
from scipy.io import wavfile
from scipy.io.wavfile import read, write
import sounddevice as sd

sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

from stream import StreamArray
from run import run
from sink import sink_window

#---------------------------------------------------------------------
# CODE FROM ZULKO, PIANOPUTER. MERELY FOR REFERENCE.
#---------------------------------------------------------------------

def speedx(sound_array, factor):
    """
    Multiplies the sound's speed by factor
    Taken from Zulko, pianoputer

    Parameters
    ----------
    sound_array: np.array
      The array that is being stretched
    factor: positive number
      The sound is speeded up when factor > 1.

    """
    indices = np.round( np.arange(0, len(sound_array), factor) )
    indices = indices[indices < len(sound_array)].astype(int)
    return sound_array[ indices.astype(int) ]


def stretch(sound_array, f, window_size, h):
    """
    Stretches the sound by a factor f.
    Taken from Zulko, pianoputer

    Parameters
    ----------
    sound_array: np.array
      The array that is being stretched
    f: positive number
      The amount of stretch when f > 1 and contraction if f < 1.
    window_size: int or float
      The sound_array is inspected by subarrays each of which is of
      size window_size.
    h: int or float
      The overlap between successive windows.
    """
    window_size = int(window_size)
    phase  = np.zeros(window_size)
    hanning_window = np.hanning(window_size)
    result = np.zeros( int(len(sound_array) /f + window_size))

   
    for i in np.arange(0, len(sound_array)-(window_size+h), int(h*f)):

        # two potentially overlapping subarrays
        a1 = sound_array[i: i + int(window_size)]
        a2 = sound_array[i + h: i + int(window_size) + int(h)]

        # resynchronize the second array on the first
        s1 =  np.fft.fft(hanning_window * a1)
        s2 =  np.fft.fft(hanning_window * a2)
        phase = (phase + np.angle(s2/s1)) % 2*np.pi
        a2_rephased = np.fft.ifft(np.abs(s2)*np.exp(1j*phase))

        # add to result
        i2 = int(i/f)
        result[i2 : i2 + window_size] += np.real((hanning_window*a2_rephased))
        
    #result = ((2**(16-4)) * result/result.max()) # normalize
    # Assume result.max() is 2**(16-4)x
    return result.astype('int16')

def pitchshift(sound_array, n, window_size=2**13, h=2**11):
    """
    Changes the pitch of a sound by n semitones.
    Taken from Zulko, pianoputer
    """
    factor = 2**(1.0 * n / 12.0)
    stretched = stretch(sound_array, 1.0/factor, window_size, h)
    return speedx(stretched[window_size:], factor)

#---------------------------------------------------------------------
# END OF CODE FROM ZULKO, PIANOPUTER
#---------------------------------------------------------------------


#---------------------------------------------------------------------
# CODE TO CONVERT OPERATION ON AN ARRAY TO OPERATION ON A STREAM.
#---------------------------------------------------------------------
def pitchshift_stream(sound_array, n, window_size=2**13, h=2**11):
    """
    Changes the pitch of a sound by n semitones.

    Notes
    -----
    This application has 2 sink_window agents and 3 streams x, y, z.
    Stretch agent: The first agent gets input x and outputs y which
    stretches the data in stream x. The stretching code is from Zulko,
    pianoputer. 
    Speed up agent: The next agent gets input y and outputs z which
    speeds up y by the specified factor. This agent interpolates the
    data in y to the number of points determined by factor.

    """
    factor = 2**(1.0 * n / 12.0)
    f = 1.0/factor

    # Declare streams
    x = StreamArray('x', dtype=np.int16)
    y = StreamArray('y', dtype=np.int16)
    z = StreamArray('z', dtype=np.int16)

    # Define the stretch agent
    stretch_object = Stretch(
        in_stream=x, out_stream=y, factor=factor,
        window_size=window_size, h=h) 
    sink_window(
        func=stretch_object.stretch, in_stream=x,
        window_size=window_size+h, step_size=int(h*f))

    # Define the speedup agent.
    def f(window, out_stream):
        indices = np.arange(0, window_size, factor)
        out_stream.extend(
            np.int16(np.interp(
                indices, np.arange(window_size), window))) 
    sink_window(func=f, in_stream=y, window_size=window_size,
    step_size=window_size, out_stream=z)

    # Partition sound_array into sound bites. Extend the
    # input with a sequence of sound bites and run each
    # sound bite until the sound_array data is finished.
    sound_bite_size = 2**14
    for i in range(0, sound_array.size, sound_bite_size):
        # sound_bite = sound_array[i:i+sound_bite_size]
        x.extend(sound_array[i:i+sound_bite_size])
        run()
    # Process any data in sound_array that wasn't processed
    # in the for loop.
    x.extend(sound_array[i:])

    # Return the result.
    return z.recent[:z.stop]

class Stretch(object):
    """
    Parameters
    __________

    """
    def __init__(self, in_stream, out_stream, factor, window_size, h):
        self.in_stream = in_stream
        self.out_stream = out_stream
        self.factor = factor
        self.f = 1.0/factor
        self.window_size = window_size
        self.h = h
        self.phase = np.zeros(window_size)
        self.hanning_window = np.hanning(self.window_size)
        self.result = np.zeros(window_size+h)
    def stretch(self, window):
        # -----------------------------------------------------
        # From Zulko stretch()
        # a1 and a2 are two overlapping subarrays, each of size
        # window_size with an overlap of h.
        a1 = window[:self.window_size]
        a2 = window[int(self.h): self.window_size+int(self.h)]

        # resynchronize the second array on the first
        s1 = np.fft.fft(self.hanning_window * a1)
        s2 = np.fft.fft(self.hanning_window * a2)
        self.phase = (self.phase + np.angle(s2/s1)) % 2*np.pi
        a2_rephased = np.fft.ifft(np.abs(s2)*np.exp(1j*self.phase))

        # Add resynchronized second array to result, and output
        # on out_stream. Recall that the size of self.result is
        # self.window_size + self.h.
        self.result[: self.window_size] += np.real(
            (self.hanning_window*a2_rephased))
        current_output = (self.result[:self.h]).astype(np.int16)
        self.out_stream.extend(current_output)

        # Save self.result[self.h : ] for next window.
        self.result = np.roll(self.result, -self.h)
        self.result[self.window_size:] = 0.0

#---------------------------------------------------------------------
# TEST
#---------------------------------------------------------------------
def test_pitchshift():
    fps, sound_array = wavfile.read("./guitar.wav")
    tones = [-12, 0, 12]
    for tone in tones:
        print ('tone is ', tone)

        # Array code
        # transposed = pitchshift(sound_array, tone)
        # print ('Playing sound from array code')
        # sd.play(transposed, blocking=True)

        # Stream code
        transposed_stream = pitchshift_stream(sound_array, tone)
        print ('Playing sound from stream code')
        sd.play(transposed_stream, blocking=True)
        print ()
        
if __name__ == '__main__':
    test_pitchshift()
