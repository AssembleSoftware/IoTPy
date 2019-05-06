"""
Compute the magnitude stream from streams of x and y
values.

"""
import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../subtract_mean"))

from stream import Stream
from merge import zip_map
import math

def magnitude_of_vector(coordinates):
    return math.sqrt(sum([v*v for v in coordinates]))


if __name__ == '__main__':
    from stream import Stream
    from sink import stream_to_file
    import numpy as np

    # DECLARE STREAMS
    # x_stream is data on the x axis
    x_stream = Stream('x')
    # y_stream is data on the y axis
    y_stream = Stream('y')
    # magnitude_stream is the stream of magnitudes.
    magnitude_stream = Stream('magnitudes')
    # input_stream is the same as raw_data_stream
    # except that it starts after window_size.
    # This allows for an appropriate comparison
    # with zero_mean_stream
    input_stream = Stream('input data')

    # CREATE AGENTS
    # Create x_stream
    stream_to_file(
        in_stream=x_stream,
        filename='x_data_file.txt')
    # Create y_stream
    stream_to_file(
        in_stream=y_stream,
        filename='y_data_file.txt')
    # Create magnitude_stream
    zip_map(
        func=magnitude_of_vector,
        in_streams=[x_stream, y_stream],
        out_stream=magnitude_stream
        )
    # Save magnitude_stream to file
    stream_to_file(
        in_stream=magnitude_stream,
        filename='magnitude_file.txt')
    # Put sin values into x_stream and
    # cosin values into y_stream
    t = np.arange(0.0, 8.0, 0.05)
    x_data = np.sin(2*np.pi*t)
    y_data = np.cos(2*np.pi*t)
    x_stream.extend(list(x_data))
    y_stream.extend(list(y_data))

    Stream.scheduler.step()
    # Use matplotlib to plot the data
