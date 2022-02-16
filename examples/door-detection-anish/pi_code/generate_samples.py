'''
This file generates samples for determining whether the door is opening or not.
'''
import time
import board
import adafruit_bitbangio as bitbangio
import adafruit_adxl34x
import numpy as np
from datetime import datetime

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

def read_accelerometers_raw():
    a1 = np.array(accelerometer1.acceleration)
    a2 = np.array(accelerometer2.acceleration)
    a3 = np.array(accelerometer3.acceleration)
    a4 = np.array(accelerometer4.acceleration)
    return a1,a2,a3,a4

def read_accelerometers_calibrated(a1_avg, a2_avg, a3_avg, a4_avg):
    '''
    Returns acceleromter readings as 4 numpy arrays
    a1 = [a1_x, a1_y, a1_z] ...
    '''
    a1,a2,a3,a4 = read_accelerometers_raw()
    
    a1 = (a1 - a1_avg)
    a2 = (a2 - a2_avg)
    a3 = (a3 - a3_avg)
    a4 = (a4 - a4_avg)
    
    return a1,a2,a3,a4

def init():
    '''
    Calibrates sensors to remove effects from positioning, gravity, etc.
    '''
    a1_avg = np.zeros(3)
    a2_avg = np.zeros(3)
    a3_avg = np.zeros(3)
    a4_avg = np.zeros(3)
    num_timesteps = 100
    
    for i in range(num_timesteps):
        a1,a2,a3,a4 = read_accelerometers_raw()
        
        a1_avg = a1_avg + a1
        a2_avg = a2_avg + a2
        a3_avg = a3_avg + a3
        a4_avg = a4_avg + a4
        
        time.sleep(TIME_UNIT)
    
    a1_avg = a1_avg / num_timesteps
    a2_avg = a2_avg / num_timesteps
    a3_avg = a3_avg / num_timesteps
    a4_avg = a4_avg / num_timesteps
    
    return a1_avg, a2_avg, a3_avg, a4_avg

def generate_sample(num_timesteps):
    print("Calibrating")
    a1_avg, a2_avg, a3_avg, a4_avg = init()
    
    # sensor data is in shape num_timesteps x num_sensors x num_axis
    data = np.zeros((num_timesteps, 4, 3))
    
    print("Collecting")
    for i in range(num_timesteps):
        a1,a2,a3,a4 = read_accelerometers_calibrated(a1_avg, a2_avg, a3_avg, a4_avg)
        data[i,0] = a1
        data[i,1] = a2
        data[i,2] = a3
        data[i,3] = a4
        time.sleep(TIME_UNIT)
    
    print("Saving")
        
    return data

def main():
    num_timesteps = 500
    while True:
        key = input("Will this be a door opening (1) or door closed (0)?")
        if (key == '1'): y = 1
        elif (key == '0'): y = 0
        else: return
        
        X = generate_sample(num_timesteps)
        
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        if y == 1:
            filename = "./samples/positive/" + current_time + "_1.npy"
        else:
            filename = "./samples/negative/" + current_time + "_0.npy"
        np.save(filename,X)
    
main()
    