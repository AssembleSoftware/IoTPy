'''
This file generates samples for determining whether the door is opening or not.
'''
import time
import numpy as np

from stream import Stream, StreamArray, run
from example_operators import subtract_mean_from_stream
from example_operators import join_synch, detect_anomaly

import board
import adafruit_bitbangio as bitbangio
import adafruit_adxl34x

accelerometer_names = ['i2c1_0x53', 'i2c1_0x1d', '12c2_0x53', 'i2c2_0x1d']
                      
NUM_ACCELEROMETERS = len(accelerometer_names)
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

acceleration_streams = [
    Stream(name=f'acceleration_streams '+str(i)) for i in range(NUM_ACCELEROMETERS * NUM_AXES)
    ]                                 

zero_mean_streams = [Stream(
    name='zero_mean_streams '+str(i))
    for i in range(NUM_ACCELEROMETERS * NUM_AXES)
    ]

joined_stream = StreamArray(
    name="joined_stream", dtype="float",
    dimension=(NUM_ACCELEROMETERS*NUM_AXES))

# Create agent to subtract mean from each acceleration_stream.
for i in range(NUM_ACCELEROMETERS*NUM_AXES):
    subtract_mean_from_stream(
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
detect_anomaly(in_stream=joined_stream, window_size=25, anomaly_size=2,
                   anomaly_factor=1.0, cloud_data_size=1,
                   cloud_func=cloud_func)


if __name__ == '__main__':
    i2c1 = bitbangio.I2C(board.SCL, board.SDA)
    i2c2 = bitbangio.I2C(board.D24, board.D23)

    # 0x53 for default
    # 0x1d for alt
    accelerometers = [
        adafruit_adxl34x.ADXL343(i2c1, address=0x53),
        adafruit_adxl34x.ADXL343(i2c1, address=0x1d),
        adafruit_adxl34x.ADXL343(i2c2, address=0x53),
        adafruit_adxl34x.ADXL343(i2c2, address=0x1d)
    ]
    assert len(accelerometer_names) == len(accelerometers)

    for i in range(100):
        # Time of measurment takes about 0.02s (without sleep)
        for j in range(NUM_ACCELEROMETERS):
            measurement = accelerometers[j].acceleration
            acceleration_streams[NUM_AXES*j + 0].append(measurement[0])
            acceleration_streams[NUM_AXES*j + 1].append(measurement[1])
            acceleration_streams[NUM_AXES*j + 2].append(measurement[2])
        
    run()

    # print()
    # print ("acceleration_streams")
    # for acceleration_stream in acceleration_streams:
    #     acceleration_stream.print_recent()

    # print()
    # print ("zero_mean_streams")
    # for zero_mean_stream in zero_mean_streams:
    #     zero_mean_stream.print_recent()

    # print()
    # print ("joined_stream")
    # joined_stream.print_recent()