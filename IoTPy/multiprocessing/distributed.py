"""
This module defines a Class, DistributedProcess, for making a
multiprocess program that uses message-passing for communication. The
protocol used is AMQP implemented by RabbitMQ/pika.

"""
import multiprocessing
from collections import defaultdict

import sys
import os
import pika
import json
import threading
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
# sink is in the agent_types folder
# compute_engine, stream are in the core folder
from sink import sink_element, stream_to_file
from compute_engine import ComputeEngine
from stream import Stream
#multicore is in the multiprocessing folder.
from multicore import StreamProcess

class DistributedProcess(StreamProcess):
    """
    Class for creating and executing a process that communicates using
    message passing with the AMQP protocol implemented by RabbitMQ.

    Parameters
    ----------
       func: function
          The function that is encapsulated to create this process.
          func returns a 3-tuple: (1) list of sources, (2) list of
            input streams, and (3) list of output streams.
       name: str (optional)
          Name given to the process. The name helps with debugging.

    Attributes
    ----------
        out_to_remote: defaultdict(list)
           key: str
                Name of an out_stream
           value: stream_name_and_process_name_list
                  which is a list of pairs (2-tuples) where each
                  pair is (stream_name, process_name)
                  (1) stream_name: pickled object
                      stream_name is the name of the input stream
                      of a function in the receiver process. This
                      name may be different from the name of the 
                      stream in the sending process attached to it.
                      e.g. str: the name of the target stream, or
                      e.g. pair (str, int) where str is the name
                      of an array of target streams and int is an index
                      into the array. 
                  (2) process_name: str
                          The name of the receiver process.
        process: multiprocess.Process
           The process that communicates using AMQP.
           This process is created by calling the method
           connect_process() and is started by calling the method,
           start().

    """
    def __init__(self, func, name=None):
        super(DistributedProcess, self).__init__(func, name)
        self.out_to_remote = defaultdict(list)
        self.process = None

    def attach_remote_stream(
            self, sending_stream_name, receiving_process_name,
            receiving_stream_name):
        """
       Assign key = sender and value = receiver in
       out_to_remote dict.  

        """
        self.out_to_remote[sending_stream_name].append(
            (receiving_stream_name, receiving_process_name))

    def connect_processor(self, out_streams):
        """
        Create agents that send messages from each sending stream in
        out_streams to the receiving streams in the remote processes
        corresponding to that sending stream.
        The receiving streams and processes are specified in
        out_to_remote.

        Parameters
        ----------
            out_streams: list of Stream

        """
        super(DistributedProcess, self).connect_processor(out_streams)
        # name_to_stream is a dict: sending_stream_name -> sending_stream
        name_to_stream = {s.name: s for s in out_streams}
        for sending_stream_name, stream_procs in self.out_to_remote.items():
            sending_stream = name_to_stream[sending_stream_name]
            # stream_procs is a list of pairs, where each pair is:
            # (receiver stream name, receiver processor name)
            for receiver_stream_name, receiver_process_name in stream_procs:
                self.stream_to_AMQP_exchange(
                    sending_stream,
                    receiver_stream_name, receiver_process_name)
 
    def stream_to_AMQP_exchange(
            self, sending_stream, receiver_stream_name,
            receiver_process_name):
        """
        Makes an agent that connects sending_stream to the receiver
        with name receiver_stream_name in the remote process
        called receiver_process_name. The agent that is created is a
        sink_element. Each element of sending_stream is tagged with
        the receiver_stream_name, converted to JSON and sent using
        RabbitMQ basic_publish() protocol.

        """
        def f(element):
            msg = (receiver_stream_name, element)
            json_payload = json.dumps(msg)
            self.channel.basic_publish(
                exchange='remote_processes',
                routing_key=receiver_process_name,
                body=json_payload)
        sink_element(func=f, in_stream=sending_stream)


    def target_of_connect_process(self):
        """
        Returns
        -------
           None

        """
        # callback is a method in RabbitMQ/pika.
        # Lookup receive_logs_direct.py
        def callback(ch, method, properties, body):
            self.in_queue.put(json.loads(body))
        # Connection, channel, result, queue_name are part of
        # RabbitMQ. Look at receive_logs_direct.py
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost')) 
        self.channel = (self.connection).channel()
        self.channel.exchange_declare(
            exchange='remote_processes', exchange_type='direct')
        self.result = self.channel.queue_declare(exclusive=True)
        self.queue_name = self.result.method.queue
        self.channel.queue_bind(
                exchange='remote_processes',
                queue=self.queue_name,
                routing_key=self.name)
        self.channel.basic_consume(
            callback, queue=self.queue_name, no_ack=True)
        # Create a thread to receive messages on the channel.
        self.receive_remote_message_thread = threading.Thread(
            target=self.channel.start_consuming, args=())

        # Create a new Stream.scheduler and set its input
        # queue to in_queue so that streams from other
        # processes that are fed to in_queue are operated
        # on by the scheduler.
        Stream.scheduler = ComputeEngine(self.name)
        Stream.scheduler.input_queue = self.in_queue
        # Obtain the externalities of func, i.e. its
        # source threads, and input and output streams.
        sources, in_streams, out_streams = self.func()
        name_to_stream = {s.name: s for s in in_streams}
        # Tell the scheduler in which stream to append an element
        # that is tagged with a stream name.
        Stream.scheduler.name_to_stream = name_to_stream

        # Connect the output streams to other processes
        self.connect_processor(out_streams)
        # Start the source threads
        for ss in sources:
            ss_thread, ss_ready = ss
            ss_thread.start()
        # Wait for source threads to be ready to execute.
        for ss in sources:
            ss_thread, ss_ready = ss
            ss_ready.wait()
        # Start the thread that receives messages from RabbitMQ
        self.receive_remote_message_thread.start()
        # Start the scheduler for this process
        Stream.scheduler.start()
        # Join the source threads. The source threads may
        # execute for ever in which case this join() will not
        # terminate.
        for ss in sources:
            ss_thread, ss_ready = ss
            ss_thread.join()
        # Join the scheduler for this process. The scheduler
        # may execute for ever, and so this join() may not
        # terminate. You can set the scheduler to run for a
        # fixed number of steps during debugging.
        Stream.scheduler.join()

    def connect_process(self):
        """
        See target_of_connect_process()

        """
        self.process = multiprocessing.Process(
            target=self.target_of_connect_process) 

    def start(self):
        self.process.start()
