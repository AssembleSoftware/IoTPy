import numpy as np
import pickle
import time
import multiprocessing as mp
from stream import Stream, StreamArray, run

def door_example():
    from example_operators import subtract_mean_from_stream
    from example_operators import join_synch, detect_anomaly
    from example_operators import append_item_to_StreamArray, append_item_to_stream
    from example_operators import single_item

    accelerometers = ['i2c1_0x53', 'i2c1_0x1d']
    NUM_ACCELEROMETERS = len(accelerometers)
    NUM_AXES=3

    DEMEAN_WINDOW_SIZE = 4

    def cloud_func(window, ):
        print ('')
        print ('anomaly!')
        # print ('window ', window)

    #-------------------------------------------
    # SPECIFY STREAMS
    #-------------------------------------------
    
    # Specify acceleration streams, one stream for each dimension
    # of each accelerometer.
    acceleration_streams = [
        Stream(name=f'acceleration_streams['+str(i) + ']') for i in range(NUM_ACCELEROMETERS * NUM_AXES)
    ]
                                        
    # Specify zero_mean_streams streams, one stream for
    # each accelerometer. These are the acceleration
    # streams after subtracting the mean.
    zero_mean_streams = [Stream(
        name='zero_mean_streams '+str(i))
        for i in range(NUM_ACCELEROMETERS * NUM_AXES)
        ]

    # Specify joined_stream which is the stream after
    # joining the inputs from all accelerometers.
    joined_stream = StreamArray(
        name="joined_stream", dtype="float",
        dimension=(NUM_ACCELEROMETERS*NUM_AXES))
    
    #-------------------------------------------
    # SPECIFY AGENTS
    #-------------------------------------------

    # TEST: Should print out every time something is inserted
    single_item(in_stream=acceleration_streams[1], func=(lambda x: print('a')))

    # Create an agent to subtract mean from each acceleration_stream
    # and generate zero_mean_streams
    for i in range(NUM_ACCELEROMETERS*NUM_AXES):
        subtract_mean_from_stream(
            in_stream=acceleration_streams[i],
            window_size=DEMEAN_WINDOW_SIZE,
            func=append_item_to_stream,
            out_stream=zero_mean_streams[i]
            )

    # Create an agent to join zero_mean_streams from all
    # accelerometers and generate joined_stream
    join_synch(in_streams=zero_mean_streams,
                   out_stream=joined_stream,
                   func=append_item_to_StreamArray)

    # Create an agent to input joined_stream and to detect anomalies
    # in the stream. Detected anomalies are passed to cloud_func which
    # prints the anomalies or puts them in the cloud.
    detect_anomaly(in_stream=joined_stream, window_size=25, anomaly_size=2,
                anomaly_factor=1.0, cloud_data_size=50,
                cloud_func=cloud_func)

    Stream.scheduler.start()
    return

def read_acceleromter(q, accelerometer, index):
    NUM_AXES=3
    for i in range(10):
        # Time of measurment takes about 0.02s (without sleep)
        measurement = accelerometer.acceleration
        # print(measurement)

        pickled_data_0 = pickle.dumps((
        f'acceleration_streams[{NUM_AXES*index + 0}]',
        measurement[0]))
        pickled_data_1 = pickle.dumps((
        f'acceleration_streams[{NUM_AXES*index + 1}]',
        measurement[1])) 
        pickled_data_2 = pickle.dumps((
        f'acceleration_streams[{NUM_AXES*index + 2}]',
        measurement[2]))

        q.put(pickled_data_0)
        q.put(pickled_data_1)
        q.put(pickled_data_2)
        time.sleep(0.1)
        
    return

if __name__ == '__main__':
    import board
    import adafruit_bitbangio as bitbangio
    import adafruit_adxl34x

    i2c1 = bitbangio.I2C(board.SCL, board.SDA)
    i2c2 = bitbangio.I2C(board.D24, board.D23)

    accelerometers = [
        adafruit_adxl34x.ADXL343(i2c1, address=0x53),
        #adafruit_adxl34x.ADXL343(i2c1, address=0x1d)
        adafruit_adxl34x.ADXL343(i2c2, address=0x53)
        # adafruit_adxl34x.ADXL343(i2c2, address=0x1d)
    ]
    print(accelerometers[0].acceleration)
    print(accelerometers[1].acceleration)

    # This is the compute process that identifies anomalies
    main_process = mp.Process(
        target=door_example, args=())

    q = Stream.scheduler.input_queue

    # This process puts data into accelerometer_0
    accelerometer_0_process = mp.Process(
        target=read_acceleromter, args=(q, accelerometers[0], 0))

    # This process puts data into accelerometer_1
    accelerometer_1_process = mp.Process(
        target=read_acceleromter, args=(q, accelerometers[1], 1))

    accelerometer_0_process.daemon = True
    accelerometer_1_process.daemon = True

    # Start process in any order
    print ('starting processes')
    accelerometer_0_process.start()
    print ('finished starting accelerometer_0_process')
    accelerometer_1_process.start()
    print ('finished starting accelerometer_1_process')
    main_process.start()
    print ('finished starting main_process')

    # Join process.
    accelerometer_0_process.join()
    accelerometer_1_process.join()
    main_process.join()

    # Terminate process
    # accelerometer_0_process.terminate()
    # accelerometer_1_process.terminate()
    # main_process.terminate()
        
    
