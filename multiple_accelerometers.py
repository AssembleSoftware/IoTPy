import numpy as np
import pickle
import threading
import time

from stream import Stream, StreamArray, run

def door_example():
    #from stream import Stream, StreamArray, run
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


#------------------------------------------------
# TEST BY PUTTING DATA INTO ACCELEROMETER STREAMS
#-------------------------------------------------
def put_data_into_accelerometer_0():
    pickled_data = pickle.dumps((
        'acceleration_streams[0]',
        np.array(
        [
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [3.0, 3.0, 3.0],
            [101.0, 121.0, 201.0]
        ])))
    Stream.scheduler.input_queue.put(
        pickled_data)

    # Sleep for some time
    time.sleep(2)

    pickled_data = pickle.dumps((
        'acceleration_streams[0]',
        np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [0.0, 0.0, 0.0],
            [2.0, 2.0, 2.0],
            [0.0, 0.0, 0.0],
            [3.0, 3.0, 3.0],
            [80.0, 80.0, 80.0]
        ])))
    Stream.scheduler.input_queue.put(
        pickled_data)

def put_data_into_accelerometer_1():
    pickled_data = pickle.dumps((
        'acceleration_streams[1]',
        np.array(
        [
            [1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [3.0, 3.0, 3.0],
            [201.0, 221.0, 301.0]
        ])))
    Stream.scheduler.input_queue.put(
        pickled_data)

    # Sleep for some time
    time.sleep(1)
    
    pickled_data = pickle.dumps((
        'acceleration_streams[1]',
        np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0],
            [0.0, 0.0, 0.0],
            [2.0, 2.0, 2.0],
            [0.0, 0.0, 0.0],
            [3.0, 3.0, 3.0],
            [90.0, 90.0, 90.0]
        ])))
    Stream.scheduler.input_queue.put(
        pickled_data)

    # Sleep and then shut down
    time.sleep(3)
    pickled_data = pickle.dumps((
        'scheduler', 'halt'))
    Stream.scheduler.input_queue.put(
        pickled_data)
    
    return


if __name__ == '__main__':
    # This is the compute thread that identifies
    # anomalies
    main_thread = threading.Thread(
        target=door_example, args=())

    # This thread puts data into accelerometer_0
    accelerometer_0_thread = threading.Thread(
        target=put_data_into_accelerometer_0, args=())

    # This thread puts data into accelerometer_1
    accelerometer_1_thread = threading.Thread(
        target=put_data_into_accelerometer_1, args=())

    # Start threads in any order
    accelerometer_0_thread.start()
    accelerometer_1_thread.start()
    main_thread.start()

    # Join threads.
    accelerometer_0_thread.join()
    accelerometer_1_thread.join()
    main_thread.join()
        
    
