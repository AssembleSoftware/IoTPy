#!/usr/bin/env python
import pika
import json
import threading
import sys
sys.path.append("../")

# multicore imports
from IoTPy.concurrency.multicore import get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import extend_stream

class PikaSubscriber(object):
    def __init__(self, callback, routing_key,
                 exchange='publications', host='localhost'):
        self.callback = callback
        self.routing_key = routing_key
        self.exchange = exchange
        self.host = host
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange,
                                      exchange_type='direct')
        self.result = self.channel.queue_declare(queue='', exclusive=True)
        self.queue_name = self.result.method.queue
        self.channel.queue_bind(
            exchange=self.exchange, queue=self.queue_name,
            routing_key=self.routing_key)
        self.channel.basic_consume(
            queue=self.queue_name, on_message_callback=self.callback, auto_ack=True)
    def start(self):
        self.channel.start_consuming()


def pika_callback_thread_target(procs, stream_name, routing_key, exchange, host):
    def callback(ch, method, properties, body):
        data=json.loads(body)
        if data[-1] == '_finished':
            # Received a '_finished' message indicating that the 
            # thread should terminate, and no further messages will
            # be arriving on this stream.
            # Extend the stream with data excluding'_finished'
            extend_stream(procs, data[:-1], stream_name)
            terminate_stream(procs, stream_name)
            # Terminate the callback thread.
            sys.exit()
        else:
            extend_stream(procs, data, stream_name)
    # Declare and start the Pika subscriber
    pika_subscriber = PikaSubscriber(
        callback, routing_key, exchange, host).start()


