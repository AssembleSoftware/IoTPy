"""
This module contains two tests:
test_single_process_single_source()
and
test_single_process_multiple_sources()
which tests code from multicore.py in multiprocessing.

"""

import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))

from multicore import StreamProcess, single_process_single_source
from multicore import single_process_multiple_sources
from stream import Stream
from merge import zip_stream
from source import source_function

def test_single_process_single_source():
    """
    The single source generates 1, 2, 3, 4, .....
    The compute function multiplies this sequence by 10
    and puts the result in the file called test.dat
    num_steps is the number of values output by the source.
    For example, if num_steps is 4 and test.dat is empty before the
    function is called then, test.dat will contain 10, 20, 30, 40
    on separate lines.

    """

    def g(s):
        # A simple source which outputs 1, 2, 3,... on
        # stream s.
        def generate_sequence(state): return state+1, state+1

        # Return a thread object which takes 10 steps, and
        # sleeps for 0.1 seconds between successive steps, and
        # puts the next element of the sequence in stream s,
        # and starts the sequence with value 0.
        return source_function(
            func=generate_sequence, out_stream=s,
            time_interval=0.1, num_steps=4, state=0)

    def h(s):
        # A trivial example of a network of agents consisting
        # of two agents where the network has a single input
        # stream: s.
        # The first agent applies function f to each element 
        # of the input stream, s, and puts the result in its
        # output stream t.
        # The second agent puts values in its input stream t
        # on a file called test.dat.
        from op import map_element
        from sink import stream_to_file

        def f(x): return x*10
        t = Stream()
        map_element(
            func=f, in_stream=s, out_stream=t)
        stream_to_file(in_stream=t, filename='test.dat')

    # Create a process with two threads: a source thread and
    # a compute thread. The source thread executes the function
    # g, and the compute thread executes function h.
    single_process_single_source(source_func=g, compute_func=h)


def test_single_process_multiple_sources():
    """
    This example has two sources: g_0 generates 1, 2, 3, 4, ...
    and g_1 generates random numbers. The computation zips the two
    streams together and writes the result to a file called
    output.dat.
    num_steps is the number of values produced by the source. For
    example, if the smaller of the num_steps for each source is 10,
    then (1, r1), (2, r2), ..., (10, r10), ... will be appended to the
    file  output.dat where r1,..., r10 are random numbers. 

    """
    import random

    def g_0(s):
        # A simple source which outputs 1, 2, 3, 4, .... on
        # stream s.
        def generate_sequence(state):
            return state+1, state+1

        # Return a thread object which takes 10 steps, and
        # sleeps for 0.1 seconds between successive steps, and
        # puts the next element of the sequence in stream s,
        # and starts the sequence with value 0.
        
        return source_function(
            func=generate_sequence, out_stream=s,
            time_interval=0.1, num_steps=10, state=0)

    def g_1(s):
        # A simple source which outputs random numbers
        # stream s.

        # Return a thread object which takes 12 steps, and
        # sleeps for 0.05 seconds between successive steps, and
        # puts the next element of the sequence in stream s.
        return source_function(
            func=random.random, out_stream=s,
            time_interval=0.05, num_steps=12)

    def h(list_of_two_streams):
        # A trivial example of a network of agents consisting
        # of two agents where the network has a single input
        # stream: s.
        # The first agent zips the two input streams and puts
        # the result on stream t.
        # The second agent puts values in its input stream t
        # on a file called output.dat.
        from sink import stream_to_file
        t = Stream()
        zip_stream(in_streams=list_of_two_streams, out_stream=t)
        stream_to_file(in_stream=t, filename='output.dat')

    # Create a process with three threads: two source threads and
    # a compute thread. The source threads execute the functions
    # g_0 and g_1, and the compute thread executes function h.
    single_process_multiple_sources(list_source_func=[g_0, g_1], compute_func=h)

if __name__ == '__main__':
    print 'Starting testing single process with multiple sources'
    print 'Expect to see "input queue empty" a few times '
    print
    test_single_process_multiple_sources()
    print
    print 'Successfully finished testing single process with multiple sources'
    print 'Look at the file: output.dat'
    print
    print 'Starting testing single process with single source'
    print 'Expect to see "input queue empty" a few times '
    print
    test_single_process_single_source()
    print
    print 'Successfully finished testing single process with single source'
    print 'Look at the file: test.dat'
