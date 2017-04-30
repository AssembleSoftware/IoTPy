import argparse
from multiprocessing import Process
import pika

import IoTPy.tools.component
from .source import source
from .sink import sink
from IoTPy.tools.db import get_template

import jsonpickle


def run(host="localhost", user="guest", password="guest"):
    """ Runs a listener to assemble templates

    This function assembles parts received from rabbitmq. Each part is run in
    a process.

    Parameters
    ----------
    host : str, optional
        Name of the server for rabbitmq (the default is localhost).
    user : str, optional
        Name of the user for rabbitmq (the default is guest)
    password : str, optional
        User password for rabbitmq (the default is guest)

    """

    print "Listening on " + host
    connection = pika.BlockingConnection(pika.URLParameters(
        "amqp://{0}:{1}@{2}/%2f".format(user, password, host)))
    print "Connected as " + user
    channel = connection.channel()

    channel.queue_declare(queue="assemble")

    def callback(ch, method, properties, body):

        p = Process(target=start, args=(body, host, user, password))
        p.start()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(callback, queue='assemble')
    channel.start_consuming()


def start(body, host, user, password):
    """ Assembles a template and starts sink and source

    Parameters
    ----------
    body : str
        String containing parameters for template
    host : str
        Name of the server for rabbitmq
    user : str
        Name of the user for rabbitmq
    password : str
        User password for rabbitmq

    """


    body = jsonpickle.decode(body)
    exchange, name, template_name, module_name, dict_parts = body

    print "Starting: " + name
    IoTPy.tools.component.Component(
        name, template_name, module_name, dict_parts)

    args_dict = get_template(template_name)
    sink(exchange, args_dict["outputs"], dict_parts, host, user, password)
    source(exchange, name, dict_parts, host, user, password)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        help="Hostname (default is localhost)",
        default="localhost")
    parser.add_argument(
        "--user",
        help="Username (default is guest)",
        default="guest")
    parser.add_argument(
        "--password",
        help="Password (default is guest)",
        default="guest")
    args = parser.parse_args()
    run(host=args.host, user=args.user, password=args.password)
