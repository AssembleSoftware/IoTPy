import sys
import os
import threading
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../signal_processing_examples"))

# multicore is in ../../IoTPy/multiprocessing
from multicore import shared_memory_process, Multiprocess
# op, sink, source, merge are in ../../IoTPy/agent_types
from op import map_element
from sink import stream_to_file
from source import source_list_to_stream
from merge import zip_map, zip_map_f
# stream is in ../../IoTPy/core
from stream import Stream, StreamArray
# window_dot_product is in ../signal_processing_examples
from window_dot_product import window_dot_product

def concatenate(initial_value, x, y):
    map_element(lambda v: v, x, y)

def multiply(x, K):
    def f(v): return v*K
    y = Stream()
    map_element(f, x, y)
    return y


def simple_reverberation(original_sound_list, attenuation_vector, delay):
    # Create sources
    # Create agent that generates the original sound.
    # This agent runs in its own thread.
    def generate_original_sound(original_sound):
        return source_list_to_stream(
            in_list=original_sound_list,
            out_stream=original_sound,
            time_interval=0)

    # Create actuators
    # This example has no actuators

    # Define the computational function.
    def compute_func(in_streams, out_streams):
        # Name external streams for convenience
        original_sound = in_streams[0]
        heard_sound = out_streams[0]
        # Define internal streams
        echo = Stream(name='echo', initial_value=[0]*delay)
        
        # Create agents
        # Agent that creates heard sound from original sound and echo
        zip_map(func=sum,
                in_streams=[original_sound, echo],
                out_stream=heard_sound)
        # Agent that creates the echo from the heard sound.
        window_dot_product(
            in_stream=heard_sound, out_stream=echo,
            multiplicand_vector=attenuation_vector)
        # Agents that store sounds in files
        stream_to_file(in_stream=heard_sound, filename='heard.txt')
        stream_to_file(in_stream=echo, filename='echo.txt')
        stream_to_file(in_stream=original_sound, filename='original_sound.txt')

    # Create processes
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['original_sound'],
        out_stream_names=['heard_sound'],
        connect_sources=[('original_sound', generate_original_sound)],
        connect_actuators=[],
        name='proc')

    mp = Multiprocess(
        processes=[proc],
        connections=[])
    mp.run()
    

#-----------------------------------------------------------------------
#            TESTS
#-----------------------------------------------------------------------
def test_simple_reverberation():
    original_sound_list = [0]*32 + [1]+[0]*224
    #attenuation_vector=[0.05, 0.1, 0.5, 0.1, 0.05]
    attenuation_vector=[0.8]
    delay=16
    simple_reverberation(original_sound_list, attenuation_vector, delay)

def test():
    test_simple_reverberation()
    # Plot files
    with open("original_sound.txt") as original_sound_file:
        original_sound_floats = map(float, original_sound_file)
    with open("heard.txt") as heard_file:
        heard_sound_floats = map(float, heard_file)
    with open("echo.txt") as echo_file:
        echo_floats = map(float, echo_file)
    plt.figure(1)
    plt.subplot(311)
    plt.plot(original_sound_floats, label="original sound")
    plt.subplot(312)
    plt.plot(echo_floats)
    plt.subplot(313)
    plt.plot(heard_sound_floats, label="heard")
    plt.show()

def test_simple():

    delay = 10
    original_sound = Stream()
    echo = Stream()
    heard_sound = Stream()
    attenuated_sound = Stream()
    merge_e(sum, [original_sound, echo], heard_sound)
    map_e(lambda v: v *0.1, heard_sound, attenuated_sound)
    concatenate([]*delay, attenuated_sound, heard_sound)
    heard_sound = zip_map_f(func=sum,
            in_streams=[original_sound, concatenate([0]*delay, attenuate(heard_sound))])


    @map_e
    heard = spoken + echo
    concatenate(D, multiply(heard, A), echo)


    original_sound_list = [0]*32 + [1]+[0]*224
    Stream.scheduler.step()

if __name__ == '__main__':
    #test()
    test_simple()
    
    
        
    
