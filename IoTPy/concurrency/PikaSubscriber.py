#!/usr/bin/env python
import pika
import threading

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


