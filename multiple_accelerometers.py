'''
This file generates samples for determining whether the door is opening or not.
'''
import time
import numpy as np
from datetime import datetime

from stream import Stream, StreamArray, run
from example_operators import subtract_mean_from_StreamArray
from example_operators import join_synch, detect_anomaly

"""
import board
import adafruit_bitbangio as bitbangio
import adafruit_adxl34x

i2c1 = bitbangio.I2C(board.SCL, board.SDA)
i2c2 = bitbangio.I2C(board.D24, board.D23)

# 83 is default 0x53
# 0x1d for alt

# Amount of time to wait before readings
TIME_UNIT = 0.01

accelerometers = [
    adafruit_adxl34x.ADXL345(i2c1, address=0x53),
    adafruit_adxl34x.ADXL345(i2c1, address=0x1d),
    adafruit_adxl34x.ADXL345(i2c2, address=0x53),
    adafruit_adxl34x.ADXL345(i2c2, address=0x1d)
    ]
"""
accelerometers = ['i2c1_0x53', 'i2c1_0x1d']
                      
NUM_ACCELEROMETERS = len(accelerometers)
NUM_AXES=3

DEMEAN_WINDOW_SIZE = 4


def append_item_to_stream(v, out_stream):
    out_stream.append(v)

def append_item_to_StreamArray(v, out_stream):
    out_stream.append(np.stack(v, axis=0))

def cloud_func(window, ):
    print ('')
    print ('anomaly!')
    print ('window ', window)

# Specify acceleration streams, one stream for
# each accelerometers.
# Each accel
acceleration_streams = [StreamArray(
    name='acceleration_streams '+str(i),
    dtype=float,
    dimension=NUM_AXES)
    for i in range(NUM_ACCELEROMETERS)
    ]
                                        

zero_mean_streams = [StreamArray(
    name='zero_mean_streams '+str(i),
    dtype=float,
    dimension=NUM_AXES)
    for i in range(NUM_ACCELEROMETERS)
    ]

joined_stream = StreamArray(
    name="joined_stream", dtype="float",
    dimension=(NUM_ACCELEROMETERS, NUM_AXES))

# Create agent to subtract mean from each acceleration_stream.
for i in range(NUM_ACCELEROMETERS):
    subtract_mean_from_StreamArray(
        in_stream=acceleration_streams[i],
        window_size=DEMEAN_WINDOW_SIZE,
        func=append_item_to_stream,
        out_stream=zero_mean_streams[i]
        )

    
# Join zero_mean_streams from all accelerometers
join_synch(in_streams=zero_mean_streams,
               out_stream=joined_stream,
               func=append_item_to_StreamArray)

# Detect anomaly in joined zero-mean streams, and upload to cloud.
detect_anomaly(in_stream=joined_stream, window_size=2, anomaly_size=1,
                   anomaly_factor=1.01, cloud_data_size=2,
                   cloud_func=cloud_func)




if __name__ == '__main__':
    acceleration_streams[0].extend(np.array(
        [
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [3.0, 3.0, 3.0],
            [101.0, 121.0, 201.0]
        ]
    ))
    acceleration_streams[1].extend(np.array(
        [
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [3.0, 3.0, 3.0],
            [201.0, 221.0, 301.0]
        ]
    ))

    run()

    print()
    print ("acceleration_streams")
    for acceleration_stream in acceleration_streams:
        acceleration_stream.print_recent()

    print()
    print ("zero_mean_streams")
    for zero_mean_stream in zero_mean_streams:
        zero_mean_stream.print_recent()

    print()
    print ("joined_stream")
    joined_stream.print_recent()
            
        
    
