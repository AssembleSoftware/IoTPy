"""
This code uses PyProbables:
https://pyprobables.readthedocs.io/en/latest/index.html
You will have to install PyProbables to use this code.

This code is a straightforward application of the
BloomFilter and CountMinSketch classes in PyProbables
to create an agent with a single input stream and a single
output stream. The input stream contains operations on an
object of one of the two classes and the output stream
contains results of the operations.
"""
import sys
import os

sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# stream is in ../../IoTPy/core
from stream import Stream
# op, source, sink are in ../../IoTPy/agent_types
from op import map_element
from source import source_file_to_stream
from sink import stream_to_file
# multicore is in ../../IoTPy/multiprocessing
from multicore import run_single_process_single_source
# helper_control is in ../../IoTPy/helper_functions
from helper_control import _no_value

import copy
from probables import (BloomFilter)
from probables import (CountMinSketch)
from probables.hashes import (default_sha256, default_md5)


def membership_in_stream(in_stream, out_stream, membership_object):
    """
    Parameters
    ----------
       in_stream: Stream
          The input stream of the agent.
          Each element of the input stream is a pair:
          (function_name, string) where function_name is
          a string which is one of 'add', 'check', 'remove'
          or other string associated with a method of
          membership_object.
       out_stream: Stream
          The output stream of the agent. The output stream
          contains results of executing the method specified
          by function name on membership_object.
       membership_object: Membership
          An instance of a Membership class such as BloomFilter
          or CountMinSketch from PyProbables.
          

    """
    def func(element):
        # Each element of the input stream is assumed to be a
        # pair: function_name and a value.
        function_name, value = element
        if function_name == 'add':
            membership_object.add(value)
            return _no_value
        elif function_name == 'remove':
            membership_object.remove(value)
            return _no_value
        elif function_name == 'check':
            return (value, membership_object.check(value))
        else:
            raise ValueError
        
    map_element(func, in_stream, out_stream)



def test_membership(
        in_filename, bloom_filter_filename, count_min_sketch_filename):
    """
    Parameters
    ----------
    in_filename: str
       name of the input file. This file contains two strings
       separated by blanks on each line. The strings are a
       function name and a value.
    bloom_filter_filename: str
       The output file which contains results of the operations
       specified by the input file on a membership object of
       type BloomFilter.
    count_min_sketch_filename: str
       The output file which contains results of the operations
       specified by the input file on a membership object of
       type CountMinSketch.

    Note
    ----
    This code creates a network with the following agents.
    A single source agent reads the specified input file and
    puts the contents of the file on a stream.
    Two agents read the source stream; one agent produces
    the bloom filter output and the other produces the count min
    sketch output stream.
    Agents copy the output streams to files

    """
    # bloom_filter and count_min_sketch are examples of
    # membership_object.
    bloom_filter = BloomFilter(
        est_elements=1000, false_positive_rate=0.05,
        hash_function=default_sha256)
    count_min_sketch = CountMinSketch(width=100000, depth=5)

    def compute_func(in_streams, out_streams):
        bloom_filter_out_stream = Stream('Bloom output stream')
        count_min_sketch_out_stream = Stream('CountMinSketch output stream')
        membership_in_stream(
            in_stream=in_streams[0],
            out_stream=bloom_filter_out_stream,
            membership_object=bloom_filter)
        membership_in_stream(
            in_stream=in_streams[0],
            out_stream=count_min_sketch_out_stream,
            membership_object=count_min_sketch)
        stream_to_file(
            in_stream=bloom_filter_out_stream,
            filename=bloom_filter_filename)
        stream_to_file(
            in_stream=count_min_sketch_out_stream,
            filename=count_min_sketch_filename)
    def source_func(out_stream):
        """
        Puts the input file on to a stream.

        """
        def g(element):
            function_name, obj = element.split()
            return (function_name, obj)
        return source_file_to_stream(
            func=g, out_stream=out_stream, filename=in_filename)

    # Execute a single process with the specified single source
    # and with the agents specified in compute_func.
    run_single_process_single_source(source_func, compute_func)


def test_count_min_sketch(in_filename, out_filename):
    
    membership_object = CountMinSketch(width=100000, depth=5)
    def compute_func(in_streams, out_streams):
        y = Stream('Bloom output stream')
        membership_in_stream(
            in_stream=in_streams[0], out_stream=y, membership_object=membership_object)
        stream_to_file(in_stream=y, filename=out_filename)
    def source_func(out_stream):
        def g(element):
            function_name, obj = element.split()
            return (function_name, obj)
        return source_file_to_stream(
            func=g, out_stream=out_stream, filename=in_filename)
    run_single_process_single_source(source_func, compute_func)


if __name__ == '__main__':
    ## test_bloom_filter(in_filename='input_bloom.txt',
    ##                   out_filename='output_bloom.txt')
    ## test_count_min_sketch(
    ##     in_filename='input_bloom.txt',
    ##     out_filename='output_count_min_sketch.txt')
    test_membership(
        in_filename='input_membership_test.txt',
        bloom_filter_filename='output_bloom_filter_filename.txt',
        count_min_sketch_filename='output_count_min_sketch_filename.txt')
    

    
    

