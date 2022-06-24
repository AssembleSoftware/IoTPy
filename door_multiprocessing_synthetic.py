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

    accelerometers = ['i2c0_0x53', 'i2c0_0x1d', 'i2c1_0x53', 'i2c1_0x1d']
    NUM_ACCELEROMETERS = len(accelerometers)
    NUM_AXES=3

    DEMEAN_WINDOW_SIZE = 4

    def cloud_func(window):
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
    single_item(in_stream=acceleration_streams[1], func=print)

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
    
    single_item(in_stream=joined_stream, func=print)

    # Create an agent to input joined_stream and to detect anomalies
    # in the stream. Detected anomalies are passed to cloud_func which
    # prints the anomalies or puts them in the cloud.

    # window_size is size of entire window under consideration
    # The last anomaly_size elements are analyzed in relation to the REST 
    # of the window_size - anomaly_size elements.
    detect_anomaly(in_stream=joined_stream, window_size=50, anomaly_size=5,
                anomaly_factor=1.5, cloud_data_size=1,
                cloud_func=cloud_func)

    Stream.scheduler.start()

    return

def read_acceleromters_synthetic(q, i2c_num):
    NUM_AXES=3
    NUM_ACCELEROMETERS_PER_I2C = 2

    for i in range(10):
        for j in range(NUM_ACCELEROMETERS_PER_I2C):
            # Synthetic x,y,z measurement
            measurement_synthetic = [1.0, 2.0, 3.0]
            accelerometer_num = (NUM_ACCELEROMETERS_PER_I2C * i2c_num) + j

            # Data needs to be a list because streams are extended
            for k in range(NUM_AXES):
                pickled_data = pickle.dumps((
                f'acceleration_streams[{NUM_AXES*accelerometer_num + k}]',
                [measurement_synthetic[k]]))
                q.put(pickled_data)

    print('Done reading')
    pickled_data = pickle.dumps(('scheduler', 'halt'))
    q.put(pickled_data)
        
    return

if __name__ == '__main__':

    # This is the compute process that identifies anomalies
    main_process = mp.Process(
        target=door_example, args=())

    q = Stream.scheduler.input_queue

    # This process puts data into i2c0's accelerometers
    i2c0_process = mp.Process(
        target=read_acceleromters_synthetic, args=(q, 0))

    # This process puts data into i2c1's accelerometers
    i2c1_process = mp.Process(
        target=read_acceleromters_synthetic, args=(q, 1))

    i2c0_process.daemon = True
    i2c1_process.daemon = True

    # Start process in any order
    print ('starting processes')
    i2c0_process.start()
    print ('finished starting i2c0_process')
    i2c1_process.start()
    print ('finished starting i2c1_process')
    main_process.start()
    print ('finished starting main_process')

    # Join process.
    i2c0_process.join()
    i2c1_process.join()
    main_process.join()

    # Terminate process
    i2c0_process.terminate()
    i2c1_process.terminate()
    main_process.terminate()
        
    
