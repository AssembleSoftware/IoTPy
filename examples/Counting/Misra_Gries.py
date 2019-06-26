import sys
import os
import threading
import random
import numpy as np
import pickle as p

sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../timing"))

# multicore is in ../../IoTPy/multiprocessing
from multicore import SharedMemoryProcess
from multicore import shared_memory_process, Multiprocess
## from multicore import single_process_single_source
## from multicore import single_process_multiple_sources
from multicore import run_single_process_single_source
# stream is in ../../IoTPy/core
from stream import Stream, StreamArray
# op, sink, source, merge are in ../../IoTPy/agent_types
from op import map_element, map_window, filter_element, map_list, map_window_list
from merge import zip_stream, blend, zip_map, merge_window
from source import source_func_to_stream, source_function, source_list
from source import SourceList, source_list_to_stream, source_int_file
from sink import stream_to_file, sink_element
# timing is in examples.
from timing import offsets_from_ntp_server
from print_stream import print_stream
from helper_control import _stop_, _close, _no_value, _multivalue
from recent_values import recent_values


#------------------------------------------------------------------
#THE MISRA GRIES ALGORITHM
#------------------------------------------------------------------

def misra_gries_process_element(
        v, state, M):

    """
    This function updates the state for a new element
    in the input stream using the Misra-Gries
    algorithm. It outputs the candidates for
    heavy hitters after M elements arrive on the input
    stream. See
    http://www.cs.utexas.edu/users/misra/Notes.dir/HeavyHitters.pdf.

    Parameters
    ----------
    v: object
        An element of the stream
    state: list of 3 elements
        state[0]: is keys
          where keys is list of k items which are
          candidates for heavy hitters or may be None.
        state[1]: is counts
          where counts is a list of k non-negative
          integers which are the counts for the
          corresponding keys.
          counts[j] corresponds to keys[j], all j.
        state[2]: int, nonnegative
          The number of new elements that have
          arrived on the input stream since the
          last output.

    Returns
    -------
       output, next state
       output is the next output element which is the
          current value of (keys, counts) or,
          when the input stream is closed, this is
          followed by _close to close the output
          stream.
       next_state is the next state.

    """
    keys, counts, index = state

    # If the input stream is closed then output the
    # keys, counts and then close the output stream.
    # _multivalue is used to ouput multiple values
    # which are state and _close in this case.
    if v is _close:
        output = _multivalue(((keys, counts), _close))
        return output, state

    # A new element (other than _close command) arrived
    # on the input stream.
    # Increment index because a new input element arrived.
    index += 1
    # UPDATE keys and counts
    # If the input element is in keys then increment
    # its count.
    if v in keys:
        pos = keys.index(v)
        counts[pos] += 1
    # If the input element is not in keys and None
    # is in keys, then insert the input element into
    # keys with a count of 1.
    elif None in keys:
        pos = keys.index(None)
        counts[pos] += 1
        keys[pos]  = v
    # If the input element and None are not in keys
    # then decrement counts, and set keys[i] to
    # None for any zero count.
    else:
        for i in range(len(keys)):
            counts[i] -= 1
            if counts[i] == 0:
                keys[i] = None
    # FINISHED UPDATING keys and counts

    
    if index < M:
        # Not enough inputs for an output.
        # So, output _no_value.
        output = _no_value
    else:
        # Got M inputs; so output a value.
        # Reset index to 0 because we are outputting
        # an element.
        index = 0
        output = (keys, counts)
    next_state = (keys, counts, index)
    return output, next_state


def misra_gries(k, in_stream, out_stream, M):
    """
    This function creates an agent  which
    executes the misra-gries heavy hitters algorithm
    on the input in_stream to produce the output
    stream, out_stream.

    Parameters
    ----------
    k: int, positive
        Specifies the number of heavy hitter elements
        that the algorithm searches for.
    in_stream: Stream
        The input stream
    out_stream: Stream
        The output stream
    M: int, positive
       Outputs candidates for heavy hitters after every
       M new arrivals in in_stream.

    """

    # CREATE AGENT
    # Make the agent that reads the input stream and
    # produces the output stream.

    # Set up the initial state.
    keys = [None]*k
    counts = [0]*k
    index = 0
    initial_state = (keys, counts, index)
    # Create agent
    map_element(func=misra_gries_process_element,
                in_stream=in_stream,
                out_stream=out_stream,
                state=initial_state,
                M=M)

    

#-----------------------------------------------------------------------
#            TESTS
#-----------------------------------------------------------------------

def test_Misra_Gries(
        in_filename, out_filename, num_heavy_hitters,
        reporting_window_size):

    # s is an object where s.source_func(out_stream)
    # puts integer data from the source file into
    # the stream, out_stream.
    s = source_int_file(filename=in_filename)

    def compute_func(in_streams, out_streams):
        # Specify internal streams. This stream is output by
        # the misra_gries agent and input by the stream_to_file agent.
        misra_gries_output_stream = Stream('Misra Gries output')
        # Create the misra_gries agent.
        misra_gries(
            k=num_heavy_hitters,
            in_stream=in_streams[0], # input from source
            out_stream=misra_gries_output_stream, # Goes to printer
            M=reporting_window_size)
        # Create the stream_to_file agent.
        stream_to_file(
            in_stream=misra_gries_output_stream,
            filename=out_filename)

    # MAKE AND RUN THE SHARED MEMORY PROCESS
    run_single_process_single_source(
        source_func=s.source_func, compute_func=compute_func)

if __name__ == '__main__':
    test_Misra_Gries(
        in_filename='misra_gries_input.txt',
        out_filename='misra_gries_output.txt',
        num_heavy_hitters=2,
        reporting_window_size=1)








