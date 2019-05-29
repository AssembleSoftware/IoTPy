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
from op import map_element, copy_stream
from sink import stream_to_file
from source import source_list_to_stream
from merge import zip_map
# stream is in ../../IoTPy/core
from stream import Stream, StreamArray
# window_dot_product is in ../signal_processing_examples
from window_dot_product import window_dot_product

#-------------------------------------------------------
# THE AGGREGATOR PROCESS
#-------------------------------------------------------
class make_aggregator(object):
    """
    The aggregator sums its input streams which are the
    original sound and the echoes. It also copies its
    original sound to the output.

    Attributes
    ----------
    original_sound_list: list of int or list of float
       The sound as a list of numbers
    output_file_name: str
       The name of the file in which the output sound is
       stored. The output sound is the original sound with
       echoes.
    echo_names: list of str
       The names of the echo streams produced by the
       echo-generator processes.

    """
    def __init__(
            self, original_sound_list,
            output_file_name, echo_names):
        self.original_sound_list = original_sound_list
        self.output_file_name = output_file_name
        self.echo_names = echo_names
    
    # CREATE SOURCE THREADS.
    # This thread generates the original sound from the
    # original sound list.
    def generate_sound_stream(self, original_sound_stream):
        return source_list_to_stream(
            in_list=self.original_sound_list,
            out_stream=original_sound_stream,
            time_interval=0)

    # CREATE ACTUATOR THREADS
    # This process has no actuators

    # DEFINE THE COMPUTATIONAL FUNCTION
    # Define the computational function for the aggregator
    def aggregate(self, in_streams, out_streams):
        # IDENTIFY INPUT AND OUTPUT STREAMS.
        #     original_sound = in_streams[0]
        #     echoes = in_streams[1:]
        #     original_stream_copy = out_streams[0]
        #     heard_sound = out_streams[1]

        # CREATE INTERNAL STREAMS.
        # This agent has no internal streams.

        # CREATE AGENTS
        # Create agent that creates heard sound by summing
        # original sound and and all echoes.
        zip_map(sum, in_streams, out_streams[1])
        # Copy original stream to an output stream.
        copy_stream(in_streams[0], out_streams[0])
        # Create agents that store sounds in files.
        stream_to_file(out_streams[1], self.output_file_name)
        stream_to_file(in_streams[0], 'original_sound.txt')

    # MAKE THE SHARED MEMORY PROCESS
    def make_process(self):
        return shared_memory_process(
            compute_func=self.aggregate,
            # inputs are the original sound and all the echoes.
            in_stream_names=['original_sound'] + self.echo_names,
            out_stream_names=['original_sound_copy', 'heard_sound'],
            connect_sources=[('original_sound', self.generate_sound_stream)],
            name='aggregator process')

#-------------------------------------------------------
# THE ECHO PROCESS
#-------------------------------------------------------
class make_echo(object):
    def __init__(self, delay, attenuation_vector, echo_name):
        self.delay = delay
        self.attenuation_vector = attenuation_vector
        self.echo_name = echo_name

    # CREATE SOURCE THREADS.
    # This process has no sources. Its inputs are from other
    # processes.

    # CREATE ACTUATOR THREADS
    # This process has no actuators

    # DEFINE THE COMPUTATIONAL FUNCTION
    # Define the computational function for the echo.
    def echo_func(self, in_streams, out_streams):
        # IDENTIFY INPUT AND OUTPUT STREAMS.
        # We give names for the input and output streams
        # so that the code is easier to read; this is
        # merely a convenience.
        # The input and output streams are:
        original_sound = in_streams[0]
        echo = out_streams[0]
        echo.extend([0]*self.delay)

        # CREATE INTERNAL STREAMS.
        original_sound_plus_echo = Stream(
            name='original sound plus echo')

        # CREATE AGENTS
        # Make the agent that sums the input
        # streams --- which are echo and original
        # sound --- to get the original sound plus the echo.
        zip_map(
            func=sum,
            in_streams=[original_sound, echo],
            out_stream=original_sound_plus_echo)
        # Make the agent that creates the echo by
        # echoing the original sound plus the echo.
        window_dot_product(
            in_stream=original_sound_plus_echo,
            out_stream=echo,
            multiplicand_vector=self.attenuation_vector)
        # Agents that store sounds in files
        stream_to_file(in_stream=echo,
                       filename=self.echo_name + '.txt')
        stream_to_file(in_stream=original_sound_plus_echo,
                       filename='original_sound_plus_' + self.echo_name + '.txt')

    # MAKE THE SHARED MEMORY PROCESS
    def make_process(self):
        # An echo process has no sources and no actuators.
        # It has a single input which is the original sound
        # (or a copy of the original sound).
        # It has a single output which is the echo.
        return shared_memory_process(
            compute_func=self.echo_func,
            in_stream_names=['original_sound'],
            out_stream_names=[self.echo_name],
            name='proc_' + self.echo_name)

    
def two_echo_reverberation(
        original_sound_list, delays_and_attenuations_dict,
        output_file_name):
    """
    Parameters
    ----------
       original_sound_list: list of numbers
          The original sound as a list of float or int
       delays_and_attenuations_dict: dict
          key: name of an echo
          value: pair (delay, attenuation_vector)
             where delay: int
                     delay in number of sample points.
                   attenuation_vector: list of floats
                     attenuation due to dispersion.
                     Often this vector consists of a
                     single element.
        output_file_name: str
           The name of the file on which the heard
           sound is stored.
        

    """
    echo_names = delays_and_attenuations_dict.keys()
    aggregator = make_aggregator(
        original_sound_list, output_file_name, echo_names)
    aggregator_process = aggregator.make_process()
    # processes will be a list consisting of the aggregator
    # process and all the echo processes.
    processes = [aggregator_process]
    connections = []
    for echo_name, delay_and_attenuation in delays_and_attenuations_dict.items():
        delay, attenuation_vector = delay_and_attenuation
        echo =  make_echo(
            delay, attenuation_vector, echo_name)
        echo_process = echo.make_process()
        processes.append(echo_process)
        # Create a connection from the aggregator's output,
        # called 'original_sound_copy', to the echo process'
        # input, called 'original_sound'.
        connections.append(
            (aggregator_process, 'original_sound_copy',
             echo_process, 'original_sound'))
        # Create a connection from the echo process' output,
        # called echo_name, to the aggregator's input also
        # called echo_name.
        connections.append(
            (echo_process, echo_name,
             aggregator_process, echo_name))

    mp = Multiprocess(processes, connections)
    mp.run()

#-----------------------------------------------------------------------
#            TESTS
#-----------------------------------------------------------------------
def test_reverberation():
    original_sound_list = [0]*4 + [1] + [0]*32
    delays_and_attenuations_dict = {
        'echo_1':(2,[0.8]),
        'echo_2':(3,[0.4])
        }
    output_file_name = 'heard_sound.txt'
    two_echo_reverberation(
        original_sound_list, delays_and_attenuations_dict,
        output_file_name)

def test():
    test_reverberation()

if __name__ == '__main__':
    test()
    
    
        
    
