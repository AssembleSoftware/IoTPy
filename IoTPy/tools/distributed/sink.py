import IoTPy.tools.assemble
import pika
import jsonpickle


def addToQueue(value, exchange, channel, part_name, name, index=None):
    """ Adds a value to a queue for rabbitmq

    Parameters
    ----------
    value : object
        Value to send
    exchange : str
        Name of the exchange
    channel : pika channel
        Channel to send value
    part_name : str
        Name of the part to send to
    name : str
        Name of the parameter
    index : int, optional
        Index of the parameter (the default is None)

    """
    if index is None:
        print "Adding {0} to distributed queue for {1} for {2}".format(
            value, part_name, name)
        body = jsonpickle.encode([name, value])
        print "Exchange: " + exchange
        print "Routing key: " + part_name
        channel.basic_publish(
            exchange=exchange,
            routing_key=part_name,
            body=body)
    else:
        print "Adding {0} to distributed queue for {1} for {2},{3}".format(
            value, part_name, name, index)
        body = jsonpickle.encode([name, index, value])
        print "Exchange: " + exchange
        print "Routing key: " + part_name
        channel.basic_publish(
            exchange=exchange,
            routing_key=part_name,
            body=body)


def sink(exchange, fields, dict_parts, host="localhost",
         user="guest", password="guest"):
    """ Create sinks for each stream in fields

    Parameters
    ----------
    exchange : str
        Name of the exchange
    fields : list
        List of field names
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

    for field in fields:

        # Typed field
        if isinstance(field, list):
            field_type, field_name = field
            if field_type == "stream":

                # List of streams
                if isinstance(dict_parts[field_name], list):
                    for stream in dict_parts[field_name]:

                        # Iterate over stream destinations
                        for des in stream.dest:
                            parameters = [exchange, channel] + des.to_list()
                            args = {
                                "in": stream.value,
                                "function": addToQueue,
                                "parameters": parameters}

                            IoTPy.tools.assemble.assemble(
                                "sink", "sink", __name__, **args)
                else:
                    # Iterate over stream destinations
                    for des in dict_parts[field_name].dest:
                        parameters = [exchange, channel] + des.to_list()
                        args = {
                            "in": dict_parts[field_name].value,
                            "function": addToQueue,
                            "parameters": parameters}

                        IoTPy.tools.assemble.assemble(
                            "sink", "sink", __name__, **args)
