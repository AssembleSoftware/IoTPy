import pika, os

# Access the CLODUAMQP_URL environment variable and parse it (fallback to localhost)
# url = os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/%2f')
url = os.environ.get(
    'CLOUDAMQP_URL',
    'amqp://tpgaxkyl:i6kiH41Z3bMC75RLo0ALraXr6_IMNWkb@caterpillar.rmq.cloudamqp.com/tpgaxkyl')
params = pika.URLParameters(url)
connection = pika.BlockingConnection(params)
channel = connection.channel() # start a channel
channel.queue_declare(queue='hello') # Declare a queue
## channel.exchange_declare(exchange='amq.direct',
##                          exchange_type='direct')
print ('------------')
channel.basic_publish(exchange='amq.direct',
                  routing_key='h',
                  body='Hello Mani!')

print(" [x] Sent 'Hello Mani!'")

def callback(ch, method, properties, body):
  print(" [x] Received %r" % body)

## result = channel.queue_declare(exclusive=True)
## queue_name = result.method.queue
channel.queue_bind(exchange='amq.direct',
                   queue='hello',
                   routing_key='v')

channel.basic_consume(on_message_callback = callback,
                      queue='hello',
                      auto_ack=True)

print(' [*] Waiting for messages:')
channel.start_consuming()
connection.close()
