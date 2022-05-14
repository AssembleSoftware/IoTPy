import numpy as np
import pickle
import multiprocessing
import time


#------------------------------------------------
# TEST BY PUTTING DATA INTO ACCELEROMETER STREAMS
#-------------------------------------------------
def put_data_into_accelerometer_0(q):
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
    q.put(pickled_data)
    
    time.sleep(0.1)

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
    q.put(pickled_data)
    
    time.sleep(0.1)

    return
