#!/usr/bin/env python
import pika
import json

from ..agent_types.sink import sink_list 
# sink is in agent_types

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
