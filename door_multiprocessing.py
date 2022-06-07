import numpy as np
import pickle
import time
import multiprocessing as mp

from requests import ReadTimeout
from stream import Stream, StreamArray, run

def door_example():
    from example_operators import subtract_mean_from_stream
    from example_operators import join_synch, detect_anomaly
    from example_operators import append_item_to_StreamArray, append_item_to_stream
    from example_operators import single_item
    import requests
    import json

    # Set this true if generating data for labeling
    # Otherwise, will be sent to cloud for inference
    LABELLING = False

    # Initialize Twilio SMS info
    from twilio.rest import Client
    account_sid = ''
    auth_token = ''
    from_number = ''
    to_number = ''
    client = Client(account_sid, auth_token)

    accelerometers = ['i2c0_0x53', 'i2c0_0x1d', 'i2c1_0x53', 'i2c1_0x1d']
    NUM_ACCELEROMETERS = len(accelerometers)
    NUM_AXES=3

    DEMEAN_WINDOW_SIZE = 4

    def cloud_func(window):
        curr_time = time.time()
        print ('')
        print ('anomaly!', curr_time)
        if LABELLING:
            filename = f'../data/{curr_time}.npy'
            np.save(filename, window)
            message = client.messages \
                    .create(
                        body=f"New Detection: {curr_time}",
                        from_=from_number,
                        to=to_number
                    )
        else:
            print("Uploading to Azure for inference...")
            uri = ""
            headers = {"Content-Type": "application/json"}
            data = json.dumps(window.tolist())
            try:
                response = requests.post(uri, data=data, headers=headers, timeout=5.0)
                ans = response.text
            except ReadTimeout:
                print('Inference request timed out')
                ans = '1'

            if ans == '1':
                prediction = 'Anish has entered the room at ' + str(curr_time)
            else:
                prediction = 'Kevin has entered the room at ' + str(curr_time)
            print(prediction)
            
            message = client.messages \
                    .create(
                        body=prediction,
                        from_=from_number,
                        to=to_number
                    )
            

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
    # single_item(in_stream=acceleration_streams[1], func=(lambda x: print('a')))

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
    
    # single_item(in_stream=joined_stream, func=print)

    # Create an agent to input joined_stream and to detect anomalies
    # in the stream. Detected anomalies are passed to cloud_func which
    # prints the anomalies or puts them in the cloud.

    # window_size is size of entire window under consideration
    # The last anomaly_size elements are analyzed in relation to the REST 
    # of the window_size - anomaly_size elements.
    detect_anomaly(in_stream=joined_stream, window_size=20, anomaly_size=2,
                anomaly_factor=1.75, cloud_data_size=500,
                cloud_func=cloud_func)

    Stream.scheduler.start()

    return

def read_acceleromters(q, accelerometers, i2c_num):
    import signal

    def handler(signum, frame):
        print("Ctrl-c was pressed.")
        print('Done reading')
        pickled_data = pickle.dumps(('scheduler', 'halt'))
        q.put(pickled_data)
        exit(0)

    signal.signal(signal.SIGINT, handler)

    NUM_AXES=3
    NUM_ACCELEROMETERS_PER_I2C = 2
    assert NUM_ACCELEROMETERS_PER_I2C == len(accelerometers)

    while True:
        for j, accelerometer in enumerate(accelerometers):
            accelerometer_num = (NUM_ACCELEROMETERS_PER_I2C * i2c_num) + j
            measurement_sucess = False
            while not measurement_sucess:
                try:
                    measurement = accelerometer.acceleration
                except:
                    measurement_sucess = False
                    print(f'Failed to get reading from accelerometer i2c{i2c_num}_{j}')
                    print('Trying Again')
                else:
                    measurement_sucess = True

            # Data needs to be a list because streams are extended
            for k in range(NUM_AXES):
                pickled_data = pickle.dumps((
                f'acceleration_streams[{NUM_AXES*accelerometer_num + k}]',
                [measurement[k]]))
                q.put(pickled_data)
        time.sleep(0.01)
        
    return

if __name__ == '__main__':
    import board
    import adafruit_bitbangio as bitbangio
    import adafruit_adxl34x

    i2c0 = bitbangio.I2C(board.SCL, board.SDA)
    i2c1 = bitbangio.I2C(board.D24, board.D23)

    accelerometers_i2c0 = [
        adafruit_adxl34x.ADXL343(i2c0, address=0x53),
        adafruit_adxl34x.ADXL343(i2c0, address=0x1d)
    ]

    accelerometers_i2c1 = [
        adafruit_adxl34x.ADXL343(i2c1, address=0x53),
        adafruit_adxl34x.ADXL343(i2c1, address=0x1d)
    ]

    print("Testing Accelerometers...")
    print(accelerometers_i2c0[0].acceleration)
    print(accelerometers_i2c0[1].acceleration)
    print(accelerometers_i2c1[0].acceleration)
    print(accelerometers_i2c1[1].acceleration)
    print()

    # This is the compute process that identifies anomalies
    main_process = mp.Process(
        target=door_example, args=())

    q = Stream.scheduler.input_queue

    # This process puts data into i2c0's accelerometers
    i2c0_process = mp.Process(
        target=read_acceleromters, args=(q, accelerometers_i2c0, 0))

    # This process puts data into i2c1's accelerometers
    i2c1_process = mp.Process(
        target=read_acceleromters, args=(q, accelerometers_i2c1, 1))

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