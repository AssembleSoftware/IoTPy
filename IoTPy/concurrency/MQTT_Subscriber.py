#!/usr/bin/env python
import json
import time
import paho.mqtt.client as mqtt
# For this program you have to install mqtt. See
# http://www.steves-internet-guide.com/into-mqtt-python-client/
#  You can:      pip install paho-mqtt

import sys
sys.path.append("../")
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import extend_stream

def on_connect(client, userdata, flags, rc):
    if rc==0: client.connected_flag=True
    else: print("Bad connection! Returned code = ", rc)
        
def start_callback_thread(procs, stream_name, topic, host, client_id=None):
    """
    This function starts a callback thread called by MQTT
    when a message arrives. The function puts the message
    into the stream called stream_name.

    Parameters
    ----------
    procs: list of process metadata obtained from
           get_processes_and_procs(multicore_specification)
           from IoTPy.concurrency.multicore
    stream_name: str
           The name of a stream which receives these MQTT
           messages.
    topic: str
           The topic to which this stream subscribes
    host: The ip address or 'localhost' of the host to which
          this stream subscribes.

    """
    def on_message(client, userdata, msg):
        data = json.loads(
            str(msg.payload.decode("utf-8","ignore")))
        if data == '_finished':
            # Received a '_finished' message indicating that the 
            # thread should terminate, and no further messages will
            # be arriving on this stream.
            terminate_stream(procs, stream_name)
            # Terminate the callback thread.
            sys.exit()
        else:
            extend_stream(procs, [data], stream_name)

    # Create the client
    client = mqtt.Client(client_id)
    client.connected_flag = False
    client.connect(host)
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_start()

    # Wait for the connection to succeed.
    N_MAX_TRIES = 10
    TIME_BETWEEN_TRIES = 0.5
    TIME_WAIT_FOR_PUBLISHER = 4

    # Wait for connection to succeed as indicated
    # by client.connected_flag
    n_tries = 0
    while not client.connected_flag:
        time.sleep(TIME_BETWEEN_TRIES)
        n_tries += 1
        if n_tries > N_MAX_TRIES:
            break

    if n_tries <= N_MAX_TRIES:
        # This client has connected successfully.
        # Subscribe to the topic
        client.subscribe(topic, qos=1)
        # Wait for the MQTT Publisher to start publishing.
        time.sleep(TIME_WAIT_FOR_PUBLISHER)
    else:
        # This client was unable to subscribe.
        # Log or print this information
        print ('Client unable to subscribe.')
    
