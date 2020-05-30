#!/usr/bin/env python
import pika
import sys

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='publications', exchange_type='direct')

for i in range(3):
    publication_name = 's'
    message_body = 'hello ' + str(i)
    channel.basic_publish(
        exchange='publications', routing_key=publication_name, body=message_body)
    print(" [x] Sent %r:%r" % (publication_name, message_body))
connection.close()
