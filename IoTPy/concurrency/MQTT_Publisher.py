#!/usr/bin/env python
import json
import time
import paho.mqtt.client as mqtt

import sys
sys.path.append("../")
from IoTPy.agent_types.sink import sink_element
from IoTPy.core.stream import Stream

def on_connect(client, userdata, flags, rc):
    if rc==0: client.connected_flag=True
    else: print("Bad connection! Returned code = ", rc)

class MQTT_Publisher(object):
    def __init__(self, client_id='test_client', topic='topic', host='localhost'):
        self.client_id = client_id
        self.topic = topic
        self.host = host
        self.client = mqtt.Client(client_id)
        self.client.connected_flag = False
        self.client.connect(host)
        self.time_waiting_for_connection = 1.0
        self.n_tries_for_connection = 5
        self.client.on_connect = on_connect
        self.client.loop_start()
        # Wait for the connection to succeed.
        n_tries = 0
        while not self.client.connected_flag:
            time.sleep(self.time_waiting_for_connection)
            n_tries += 1
            if n_tries > self.n_tries_for_connection:
                break
        if n_tries > self.n_tries_for_connection:
            print ('Unsuccessful connecting')
        print ('Publisher connected!')
    def close(self):
        self.client.loop_stop()
        self.client.disconnect()
    def publish(self, stream):
        def publish_element(element):
            # rc, mid are return code, message id.
            rc, mid = self.client.publish(self.topic, json.dumps(element), qos=1)
        sink_element(func=publish_element, in_stream=stream, name='MQTT Agent')

#---------------------------------------------------------
def test():
    mqtt_publisher = MQTT_Publisher(topic='topic', host='localhost')
    x = Stream('x')
    mqtt_publisher.publish(x)
    x.append('a')
    run()

if __name__ == '__main__':
    test()

