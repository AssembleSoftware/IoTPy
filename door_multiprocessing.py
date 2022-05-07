import numpy as np
import pickle
import time
import multiprocessing as mp

def door_example():
    from stream import Stream, StreamArray, run
    from example_operators import subtract_mean_from_StreamArray
    from example_operators import join_synch, detect_anomaly
    from example_operators import append_item_to_StreamArray
    


    accelerometers = ['i2c1_0x53', 'i2c1_0x1d']
    NUM_ACCELEROMETERS = len(accelerometers)
    NUM_AXES=3

    DEMEAN_WINDOW_SIZE = 4


    def cloud_func(window, ):
        print ('')
        print ('anomaly!')
        print ('window ', window)

    #-------------------------------------------
    # SPECIFY STREAMS
    #-------------------------------------------
    
    # Specify acceleration streams, one stream for
    # each accelerometer.
    acceleration_streams = [StreamArray(
        name='acceleration_streams['+ str(i) + ']',
        dtype=float,
        dimension=NUM_AXES)
            for i in range(NUM_ACCELEROMETERS)
        ]
                                        
    # Specify zero_mean_streams streams, one stream for
    # each accelerometer. These are the acceleration
    # streams after subtracting the mean.
    zero_mean_streams = [StreamArray(
        name='zero_mean_streams '+str(i),
        dtype=float,
        dimension=NUM_AXES)
            for i in range(NUM_ACCELEROMETERS)
        ]

    # Specify joined_stream which is the stream after
    # joining the inputs from all accelerometers.
    joined_stream = StreamArray(
        name="joined_stream", dtype="float",
        dimension=(NUM_ACCELEROMETERS, NUM_AXES))

    
    #-------------------------------------------
    # SPECIFY AGENTS
    #-------------------------------------------

    # Create an agent to subtract mean from each acceleration_stream
    # and generate zero_mean_streams
    for i in range(NUM_ACCELEROMETERS):
        subtract_mean_from_StreamArray(
            in_stream=acceleration_streams[i],
            window_size=DEMEAN_WINDOW_SIZE,
            func=append_item_to_StreamArray,
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
    detect_anomaly(in_stream=joined_stream, window_size=2,
                       anomaly_size=1, anomaly_factor=1.01,
                       cloud_data_size=2, cloud_func=cloud_func)

    Stream.scheduler.start()
    return


if __name__ == '__main__':
    from accel_0 import put_data_into_accelerometer_0
    from accel_1 import put_data_into_accelerometer_1

    # This is the compute process that identifies
    # anomalies
    
    main_process = mp.Process(
        target=door_example, args=())

    q = Stream.scheduler.input_queue

    # This process puts data into accelerometer_0
    accelerometer_0_process = mp.Process(
        target=put_data_into_accelerometer_0, args=(q,))

    # This process puts data into accelerometer_1
    accelerometer_1_process = mp.Process(
        target=put_data_into_accelerometer_1, args=(q,))

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
        
    
