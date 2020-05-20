#!/usr/bin/env python
import pika
import sys
import json

sys.path.append('../core')
sys.path.append('../agent_types')
sys.path.append('../helper_functions')

# stream is in core
#from stream import Stream, run
# sink is in agent_types
from sink import sink_list
# print_stream is in helper_functions
#from print_stream import print_stream
#from recent_values import recent_values

class PikaPublisher(object):
    def __init__(self, routing_key, exchange='publications', host='localhost'):
        self.routing_key = routing_key
        self.exchange = exchange
        self.host = host
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.exchange, exchange_type='direct')
    def publish_list(self, stream_segment):
        self.channel.basic_publish(
            exchange=self.exchange, routing_key=self.routing_key,
            body=json.dumps(stream_segment))
    def close(self):
        self.connection.close()
    def publish(self, stream):
        sink_list(self.publish_list, stream)
