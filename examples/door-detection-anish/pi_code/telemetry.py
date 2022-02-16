'''
This file sends telemetry data to azure for use with visualization client
'''
import os
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
import time
import board
import adafruit_adxl34x
import sys
import adafruit_bitbangio as bitbangio
from azure.iot.device import Message
import json
import numpy as np

# Amount of time to wait before readings
TIME_UNIT = 0.01

def read_accelerometers_raw():
    '''
    Returns raw values from accelerometers as 4 numpy arrays
    a1 = [a1_x, a1_y, a1_z] ...
    '''
    a1 = np.array(accelerometer1.acceleration)
    a2 = np.array(accelerometer2.acceleration)
    a3 = np.array(accelerometer3.acceleration)
    a4 = np.array(accelerometer4.acceleration)
    return a1,a2,a3,a4

def read_accelerometers_calibrated(a1_avg, a2_avg, a3_avg, a4_avg):
    '''
    Returns acceleromter readings as 4 numpy arrays
    a1 = [a1_x, a1_y, a1_z] ...
    calibrated by subtracting mean
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

def create_telemetry(telemetry_msg, component_name=None):
    """
    Function to create telemetry for a plug and play device. This function will take the raw telemetry message
    in the form of a dictionary from the user and then create a plug and play specific message.
    :param telemetry_msg: A dictionary of items to be sent as telemetry.
    :param component_name: The name of the device like "sensor"
    :return: The message.
    """
    msg = Message(json.dumps(telemetry_msg))
    msg.content_encoding = "utf-8"
    msg.content_type = "application/json"
    if component_name:
        msg.custom_properties["$.sub"] = component_name
    return msg

async def main():
    # Fetch the connection string from an enviornment variable
    conn_str = <INSERT CONNECTION STRING>
    
    # Create instance of the device client using the authentication provider
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)

    # Connect the device client.
    await device_client.connect()
    
    a1_avg, a2_avg, a3_avg, a4_avg = init()
    
    try:
        counter = 10
        while True:
            a1, a2, a3, a4 = read_accelerometers_calibrated(a1_avg, a2_avg, a3_avg, a4_avg)
            
            # As soon as we see a spike, send <counter> consecutive messages to azure
            if counter > 0 or np.sum(a1) > 1 or np.sum(a2) > 1 or np.sum(a3) > 1 \
               or np.linalg.norm(a4) > 0.1:
                if counter <= 0:
                    counter = 10
                    
                # Send a single message
                d = {'a1': a1.tolist(),
                     'a2': a2.tolist(),
                     'a3': a3.tolist(),
                     'a4': a4.tolist()}
            
                print("Sending message...")
                msg = create_telemetry(d)
                await device_client.send_message(msg)
                print("Message successfully sent!")
                counter = counter - 1
                
            time.sleep(TIME_UNIT)

    except KeyboardInterrupt:
        # finally, shut down the client
        print('Cleaning up')
        await device_client.shutdown()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == "__main__":
    i2c1 = bitbangio.I2C(board.SCL, board.SDA)
    i2c2 = bitbangio.I2C(board.D24, board.D23)

    # 83 is default 0x53
    # 0x1d for alt
    accelerometer1 = adafruit_adxl34x.ADXL345(i2c1, address=0x53)
    accelerometer2 = adafruit_adxl34x.ADXL345(i2c1, address=0x1d)
    accelerometer3 = adafruit_adxl34x.ADXL345(i2c2, address=0x53)
    accelerometer4 = adafruit_adxl34x.ADXL345(i2c2, address=0x1d)
    asyncio.run(main())
