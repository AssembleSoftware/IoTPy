import numpy as np
import sys
import os
from scipy.io.wavfile import read, write


sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))


from stream import StreamArray, Stream
from op import map_window_list,map_list

class pitch(object):
    """ A Class that is used in performing Pitch Shifting.

    """
    def __init__(self, chunk_size, overlap, factor):

        self.chunk_size = chunk_size
        self.overlap = overlap 
        self.factor = factor
        self.phase = np.zeros(self.chunk_size)
        # Use a smoothing function over the chunk_size.
        # See np.hanning, np.hamming, np.kaiser, etc.
        self.smooth = np.hanning(self.chunk_size)
        self.result = None
        self.length = int(self.chunk_size/self.overlap)

    def stretch(self, window, num_semitones):
        """
        Parameters:
        window: np.ndarray
           1-D array, the sequence of values in a stream.
        num_semitones: int, positive
           The number of semitones that the pitch should be
           shifter. (12 semitones is an octave.)

        """
        no_overlap = np.fft.fft(self.smooth*(window[:self.chunk_size]))
        with_overlap = np.fft.fft(self.smooth(window[self.overlap:]))

        self.phase = (self.phase + np.angle(with_overlap/no_overlap))%2*np.pi
    
        a2_rephased = np.fft.ifft(np.abs(s2)*np.exp(1j*self.phase))
        a2_real = self.hanning*a2_rephased.real
        
        if self.result is None:
            self.result = a2_real
            result = self.result[:self.overlap]
            self.result[:(self.length-1)*self.overlap] = self.result[self.overlap:]
            self.result[(self.length-1)*self.overlap:] = np.zeros(self.overlap)
            return result
        
        else:
            self.result+=a2_real
            result = self.result[:self.overlap]
            self.result[:(self.length-1)*self.overlap] = self.result[self.overlap:]
            self.result[(self.length-1)*self.overlap:] = np.zeros(self.overlap)
            return result
         
    def int_convert(self, in_stream):
        new_arr = np.array(in_stream)
        result = ((2**(16-4)) * new_arr/new_arr.max())
        return result.astype('int16')   


    def tempo(self, in_stream):
        indices = np.round(np.arange(0, len(in_stream), self.factor))
        indices = indices[indices < len(in_stream)].astype(int)
        return in_stream[indices]


    

    
            
        


def pitch_shifting(pitch_object, in_stream, out_stream, number_of_semitones, hanning_window_size, overlap, fs):

    window_size = hanning_window_size + overlap
    factor = 2**(1.0*number_of_semitones/12.0)
    step = overlap*1.0/factor            
    stretched = StreamArray('Stretched')
    phase = np.zeros(hanning_window_size)
    print(step, window_size)

    map_window_list(func = pitch_object.stretch,
                    in_stream = in_stream,
                    out_stream = stretched,
                    window_size = window_size,
                    step_size = int(step),
                    number_of_semitones = number_of_semitones
                    )

    map_window_list(func = pitch_object.tempo,
                    in_stream = stretched,
                    out_stream = out_stream,
                    window_size = fs/10,
                    step_size = fs/10
                    )
