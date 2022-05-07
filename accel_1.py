import numpy as np
import pickle
import multiprocessing
import time



def put_data_into_accelerometer_1(q):
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
    q.put(pickled_data)
    print ('put accel_1 data into queue')
    print (Stream.scheduler.input_queue)

    time.sleep(1.0)
    
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
    q.put(pickled_data)

    time.sleep(3.0)

    pickled_data = pickle.dumps(
        ('scheduler', 'halt'))
    q.put(pickled_data)
    
        
    
    
    return


    
"""
    pickled_data = pickle.dumps((
        'acceleration_streams[0]',
        np.array([2.0, 2.0, 2.0])))
    Stream.scheduler.input_queue.put(
        pickled_data)
    pickled_data = pickle.dumps((
        'acceleration_streams[1]',
        np.array([2.0, 2.0, 2.0])))
    Stream.scheduler.input_queue.put(
        pickled_data)
    

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
    
    #-----------------------------------------
    # Continuous input stream.

    import random
    NUM_STEPS=2
    for _ in range(NUM_STEPS):
        acceleration_streams[0].extend(
            np.random.rand(6, 3))
        acceleration_streams[1].extend(
            np.random.rand(6, 3))
    run()


    
#------------------------------------------------
# PRINT STREAMS
#-------------------------------------------------
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
"""



if __name__ == '__main__':
    accelerometer_1_process = multiprocessing.Process(
        target=put_data_into_accelerometer_1, args=())

    accelerometer_1_process.start()

    accelerometer_1_process.join()
            
        
    
