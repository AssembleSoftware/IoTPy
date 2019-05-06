"""
Tests subtract_mean()

"""
import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))


def subtract_mean(window):
    return window[-1] - sum(window)/float(len(window))

if __name__ == '__main__':
    from stream import Stream
    from op import map_window
    from sink import stream_to_file
    import numpy as np

    # DECLARE STREAMS
    # raw_data_stream is the stream of raw data
    raw_data_stream = Stream('raw data')
    # zero_mean_stream is the stream of raw data
    # with the mean subtracted.
    zero_mean_stream = Stream('zero mean data')
    # input_stream is the same as raw_data_stream
    # except that it starts after window_size.
    # This allows for an appropriate comparison
    # with zero_mean_stream
    input_stream = Stream('input data')

    # CREATE AGENTS
    map_window(
        func=subtract_mean, 
        in_stream=raw_data_stream, 
        out_stream=zero_mean_stream,
        window_size=40, step_size=1)
    map_window(
        func=lambda window: window[-1],
        in_stream=raw_data_stream, 
        out_stream=input_stream,
        window_size=40, step_size=1)
    stream_to_file(
        in_stream=input_stream,
        filename='input.txt')
    stream_to_file(
        in_stream=zero_mean_stream,
        filename='zero_mean.txt')
    
    t = np.arange(0.0, 8.0, 0.05)
    s1 = 2 + np.sin(2*np.pi*t)
    raw_data_stream.extend(list(s1))

    Stream.scheduler.step()
    # Use matplotlib to plot the data in zero_mean.txt
    # and input.txt





    
    
