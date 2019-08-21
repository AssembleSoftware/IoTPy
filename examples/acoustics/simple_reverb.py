import sys
import os
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# multicore is in ../../IoTPy/multiprocessing
from multicore import shared_memory_process, Multiprocess
# sink, source  are in ../../IoTPy/agent_types
from sink import stream_to_file
from source import source_list_to_stream
# stream is in ../../IoTPy/core
from stream import Stream, StreamArray
# basics is in ../../IoTPy/helper_functions
from basics import r_mul

def make_echo(spoken, delay, attenuation):
    echo = Stream(name='echo', initial_value=[0]*delay)
    heard = spoken + echo
    r_mul(in_stream=heard, out_stream=echo, arg=attenuation)
    return heard

def simple_reverberation(original_sound_list, delay, attenuation):
    # Create sources
    def generate_spoken_sound(spoken_sound):
        return source_list_to_stream(
            in_list=original_sound_list, out_stream=spoken_sound,
            time_interval=0)

    # Define the computational function.
    def compute_func(in_streams, out_streams):
        out_streams[0] = make_echo(in_streams[0], delay, attenuation)
        # Agents that store sounds in files used for testing.
        stream_to_file(in_stream=out_streams[0], filename='heard.txt')
        stream_to_file(in_stream=in_streams[0], filename='spoken.txt')

    # Create processes
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'], out_stream_names=['out'],
        connect_sources=[('in', generate_spoken_sound)],
        name='proc')

    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()
    

#-----------------------------------------------------------------------
#            TESTS
#-----------------------------------------------------------------------
def test_simple_reverberation():
    original_sound_list = [0]*4 + [1]+[0]*16
    simple_reverberation(original_sound_list, delay=2, attenuation=0.8)

def test():
    # Plots
    test_simple_reverberation()
    # Plot files
    with open("spoken.txt") as original_sound_file:
        original_sound_floats = map(float, original_sound_file)
    with open("heard.txt") as heard_file:
        heard_sound_floats = map(float, heard_file)
    plt.figure(1)
    plt.subplot(311)
    plt.plot(original_sound_floats, label='spoken')
    plt.subplot(312)
    plt.plot(heard_sound_floats, label="heard")
    plt.show()

if __name__ == '__main__':
    test()
    
    
        
    
