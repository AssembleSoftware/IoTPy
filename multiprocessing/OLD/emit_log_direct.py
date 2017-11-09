#!/usr/bin/env python
import pika
import sys
import json

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='direct_logs',
                         exchange_type='direct')

severity = sys.argv[1] if len(sys.argv) > 2 else 'info'
message = ' '.join(sys.argv[2:]) or 'Hello World!'
message_dict = {'severity' : severity, 'message': message}
json_payload = json.dumps(message_dict)
channel.basic_publish(exchange='direct_logs',
                      routing_key=severity,
                      body=json_payload)
print(" [x] Sent %r:%r" % (severity, message))
connection.close()
