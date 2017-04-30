import pika
import jsonpickle


def source(exchange, name, dict_parts, host="localhost",
           user="guest", password="guest"):
    """ Listens on rabbitmq queue and adds values to streams

    Parameters
    ----------
    exchange : str
        Name of the exchange
    name : str
        Name of the part
    dict_parts : dict
        Dict containing values for fields
    host : str, optional
        Name of the server for rabbitmq (the default is localhost).
    user : str, optional
        Name of the user for rabbitmq (the default is guest)
    password : str, optional
        User password for rabbitmq (the default is guest)

    """

    connection = pika.BlockingConnection(pika.URLParameters(
        "amqp://{0}:{1}@{2}/%2f".format(user, password, host)))
    channel = connection.channel()

    result = channel.queue_declare(exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=exchange, queue=queue_name, routing_key=name)

    def callback(ch, method, properties, body):
        body = jsonpickle.decode(body)
        print "Received"
        print body
        print

        # No index
        if len(body) == 2:
            stream_name, stream_value = body
            dict_parts[stream_name].value.append(stream_value)
        else:
            stream_name, stream_index, stream_value = body

            dict_parts[stream_name][stream_index].value.append(stream_value)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(callback, queue=queue_name)
    channel.start_consuming()
