'''
This file sets the Pi up to listen for door-opening movements
Once detected, it trims the signal to the area of interest
And stores it
'''
import sys
import time
import threading
import numpy as np

from IoTPy.core.stream import Stream, StreamArray, run
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.agent_types.merge import merge_window
from IoTPy.agent_types.op import map_window
from IoTPy.agent_types.sink import sink_element

from IoTPy.concurrency.multicore import get_processes, get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import get_proc_that_inputs_source
from IoTPy.concurrency.multicore import extend_stream

import board
import adafruit_bitbangio as bitbangio
import adafruit_adxl34x

i2c1 = bitbangio.I2C(board.SCL, board.SDA)
i2c2 = bitbangio.I2C(board.D24, board.D23)

# 83 is default 0x53
# 0x1d for alt
accelerometer1 = adafruit_adxl34x.ADXL345(i2c1, address=0x53)
accelerometer2 = adafruit_adxl34x.ADXL345(i2c1, address=0x1d)
accelerometer3 = adafruit_adxl34x.ADXL345(i2c2, address=0x53)
accelerometer4 = adafruit_adxl34x.ADXL345(i2c2, address=0x1d)

# Amount of time to wait before readings
TIME_UNIT = 0.01
NUM_STEPS = 2000

'''
Function to calibrate sensors in the source thread before
sending any data to the processes
'''
def calibrate(accelerometer):
    num_timesteps_calib = 100
    a_avg = np.zeros(3)
    
    for i in range(num_timesteps_calib):
        a = np.array(accelerometer.acceleration)
        a_avg = a_avg + a
        time.sleep(TIME_UNIT)

    return a_avg / num_timesteps_calib

def main():
    
    # STEP 1: DEFINE SOURCES

    def source_accelerometer1(procs):
        # Calibrate sensor
        a1_avg = calibrate(accelerometer1)
        print("calibrated sensor 1")
        
        for i in range(NUM_STEPS):
            raw = np.array(accelerometer1.acceleration)
            denoised = raw - a1_avg
            extend_stream(procs, data=denoised,
                          stream_name='a1')
            time.sleep(TIME_UNIT)
        print("sensor 1 finished")
        terminate_stream(procs, stream_name='a1')
    
    def source_accelerometer2(procs):
        # Calibrate sensor
        a2_avg = calibrate(accelerometer2)
        print("calibrated sensor 2")
        
        for i in range(NUM_STEPS):
            raw = np.array(accelerometer2.acceleration)
            denoised = raw - a2_avg
            extend_stream(procs, data=denoised,
                          stream_name='a2')
            time.sleep(TIME_UNIT)
        terminate_stream(procs, stream_name='a2')
    
    def source_accelerometer3(procs):
        # Calibrate sensor
        a3_avg = calibrate(accelerometer3)
        print("calibrated sensor 3")
        
        for i in range(NUM_STEPS):
            raw = np.array(accelerometer3.acceleration)
            denoised = raw - a3_avg
            extend_stream(procs, data=denoised,
                          stream_name='a3')
            time.sleep(TIME_UNIT)
        terminate_stream(procs, stream_name='a3')
    
    def source_accelerometer4(procs):
        # Calibrate sensor
        a4_avg = calibrate(accelerometer4)
        print("calibrated sensor 4")
        
        for i in range(NUM_STEPS):
            raw = np.array(accelerometer4.acceleration)
            denoised = raw - a4_avg
            extend_stream(procs, data=denoised,
                          stream_name='a4')
            time.sleep(TIME_UNIT)
        terminate_stream(procs, stream_name='a4')
    
    # STEP 2: DEFINE THE COMPUTATIONAL NETWORK OF AGENTS

    def merge_sensors(in_streams, out_streams):
        '''
        Agent for process p0
        Takes in sensor data, merges it properly,
        and computes a stream of the average magnitude of all 4 sensors

        Parameters
        ----------
        in_streams:
            - 4 streams corresponding to 4 accelrometer source streams
        out_streams:
            - 2 streams: 
                avg_magnitude (average magnitude of all 4 sensors) int
                raw_merged (raw sensor data grouped accordingly) numpy 4x3 array
        '''

        def merge_and_avg(v):
            magnitude_avg = 0
            for sensor_reading in v:
                magnitude_avg += np.linalg.norm(sensor_reading)
            magnitude_avg /= len(v)
            return magnitude_avg
        
        # This stream outputs a stream of floats corresponding
        # to the avergae magnitude of the 4 sensors
        merge_window(merge_and_avg, window_size=3, step_size=3,
                     in_streams=in_streams, out_stream=out_streams[0])
        
        # This stream groups the xyz measurements of each sensor
        # This will be the raw data sent to the predictive algorithm
        merge_window(lambda x: x, window_size=3, step_size=3,
                     in_streams=in_streams, out_stream=out_streams[1])
        
        #stream_to_file(in_stream=t, filename='output.dat')
    
    def moving_avg_detector(in_streams, out_streams):
        '''
        Agent for process p1
        Takes in data from p0 and determines if signal needs to be stored

        Parameters
        ----------
        in_streams:
            - 2 streams: 
                avg_magnitude (average magnitude of all 4 sensors) int
                raw_merged (raw sensor data grouped accordingly) numpy 4x3 array
        out_streams:
            Empty List
        '''

        def moving_avg(v):
            '''
            Parameters
            ----------
            v is a 1x5 window of the avg_magnitude stream
            '''
            return np.mean(v)
        
        def door_detected(v, state):
            '''
            If the 5th element of the moving avg is > 0.1,
            then returns a 1200 (12 second) long window of the raw signal

            Parameters
            ----------
            v: 2x1200 window of the avg_magnitude stream and raw_data stream
            state: indicates if signal is currently being recorded
                if state > 0 then keep saving values until state = 1200
                if state = 0 and moving avg spikes, start recording and incrementing state
            '''
            if state > 1200:
                state = 0
                
            if state > 0:
                return None, state+1
            
            if v[0][5] > 0.1:
                #return v[1]
                return v[0], 1
            
            return None, state
        
        def sink_save_numpy(v, state):
            '''
            Saves signal as .npy file

            Parameters
            ----------
            v: 1x1200 array corresponding to signal to save
            state: counter of how many signals were saved before this
            '''
            np.save('output_' + str(state), v)
            #print('saved')
            return state+1
                
        # This stream holds the rolling avg of the average magnitude of the sensors
        rolling_avg = Stream()
        map_window(moving_avg, window_size=5, step_size=1,
                   in_stream=in_streams[0], out_stream=rolling_avg)
        
        # This stream will return 12 seconds of raw data
        # only if the rolling average detects a spike
        t = Stream()
        merge_window(door_detected, window_size=1200, step_size=1,
                     in_streams=[rolling_avg, in_streams[1]],
                     out_stream=t, state=0)
        
        sink_element(sink_save_numpy, in_stream=t, state=0)
        
    
    # STEP 3: MULTICORE SPECIFICATION
    multicore_specification = [
        # Streams
        [('a1', 'f'), ('a2', 'f'), ('a3', 'f'), ('a4', 'f'),
         ('avg_mag', 'f'), ('raw_merged', 'x')],
        # Processes
        [{'name': 'p0', 'agent':merge_sensors, 'inputs':['a1', 'a2', 'a3', 'a4'],
          'outputs': ['avg_mag', 'raw_merged'], 'sources': ['a1', 'a2', 'a3', 'a4']},
         {'name': 'p1', 'agent':moving_avg_detector, 'inputs':['avg_mag', 'raw_merged'],
          'outputs': [], 'sources': []}]]
    
    # STEP 4: Create processes
    processes, procs = get_processes_and_procs(multicore_specification)
    
    # STEP 5: Create threads
    thread_a1 = threading.Thread(target=source_accelerometer1, args=(procs,))
    thread_a2 = threading.Thread(target=source_accelerometer2, args=(procs,))
    thread_a3 = threading.Thread(target=source_accelerometer3, args=(procs,))
    thread_a4 = threading.Thread(target=source_accelerometer4, args=(procs,))
    
    # STEP 6: Specify which process each thread (if any) runs in.
    procs['p0'].threads = [thread_a1, thread_a2, thread_a3, thread_a4]
    
    # STEP 7: Start, join and terminate processes.
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()
    


main()
        
    
    