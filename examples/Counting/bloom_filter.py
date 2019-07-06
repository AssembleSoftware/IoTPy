"""
This code uses PyProbables:
https://pyprobables.readthedocs.io/en/latest/index.html
You will have to install PyProbables to use this code.

This code is a straightforward application of the
HeavyHitters class in PyProbables to create an agent with a
single input stream and a single output stream. The
heavy hitters in the input stream are placed on the
output stream when ever the length of the input stream
is a multiple of window_size (a parameter).
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
from probables.hashes import (default_sha256, default_md5)


def bloom_filter_on_stream(in_stream, out_stream, blm):
    """
    Parameters
    ----------
       in_stream: Stream
          The input stream of the agent.
          Each element of the input stream is a pair:
          (function_name, string) where function_name is
          a string which is one of 'add', 'check', 'remove'
       out_stream: Stream
          The output stream of the agent. An element is
          added to the output stream when a 'check'
          function_name appears on the input stream.
          The output stream consists of pairs (string, boolean)
          where boolean is True if and only if string
          is in the input stream at this point.
       blm: BloomFilter
          An instance of BloomFilter.

    """
    def func(element):
        function_name, obj = element
        if function_name == 'add':
            blm.add(obj)
            return _no_value
        elif function_name == 'remove':
            blm.remove(obj)
            return _no_value
        elif function_name == 'check':
            obj_is_in_input_stream = blm.check(obj)
            # True if obj is in the input stream at this point.
            # False otherwise.
            return (obj, obj_is_in_input_stream)
        else:
            raise ValueError
        
    map_element(func, in_stream, out_stream)

def test_bloom_filter(in_filename, out_filename):
    from probables.hashes import (default_sha256, default_md5)
    
    blm = BloomFilter(est_elements=1000, false_positive_rate=0.05,
                      hash_function=default_sha256)
    def compute_func(in_streams, out_streams):
        y = Stream('Bloom output stream')
        bloom_filter_on_stream(
            in_stream=in_streams[0], out_stream=y, blm=blm)
        stream_to_file(in_stream=y, filename=out_filename)
    def source_func(out_stream):
        def g(element):
            function_name, obj = element.split()
            return (function_name, obj)
        return source_file_to_stream(
            func=g, out_stream=out_stream, filename=in_filename)
    run_single_process_single_source(source_func, compute_func)

if __name__ == '__main__':
    test_bloom_filter(in_filename='input_bloom.txt',
                      out_filename='output_bloom.txt')

    
    

