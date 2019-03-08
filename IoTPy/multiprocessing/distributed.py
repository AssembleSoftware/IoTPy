"""
This module defines a Class, DistributedProcess, for making a multiprocess
program that runs on a multicore (shared-memory) computer and which
can publish and subscribe streams using AMQP. A virtual machine (VM)
is a set of DistributedProcess.

For distributed computing with multiple computers with different IP 
addresses, see the module DistributedComputing.py.

"""
import multiprocessing
from collections import defaultdict
import threading
import pika
import json
import Queue

import sys
import os
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
# sink is in the agent_types folder
# compute_engine, stream are in the core folder
from sink import stream_to_queue, sink_element
from compute_engine import ComputeEngine
from stream import Stream
#multicore is in the multiprocessing folder.
from multicore import SharedMemoryProcess
from multicore import shared_memory_process

#--------------------------------------------------------------
#           DistributedProcess
#--------------------------------------------------------------
class DistributedProcess(SharedMemoryProcess):
    """
    Class for creating and executing a process in a multicomputer
    which communicates with processes in other multicomputers using
    message passing implemented by the AMQP protocol, RabbitMQ/pika
    version.
    
    A virtual machine (VM) is a set of DistributedProcess.

    For a multicore application in which processes communicate only
    through shared memory, and not message passing, see multicore.py

    The DistributedProcess class has an attribute called 'process' of
    type multiprocessing.Process which is the process that executes code.

    Parameters
    ----------
       func: function
          The function that is encapsulated to create this process.
          This function is returned by make_process()
       in_stream_names: list
          Names of input streams of this process where a name is either a
          str or a pair (str, int). For example, the pairs ('velocity', 0),
          ('velocity', 1), ... refer to a list of 'velocity' in_streams. 
       out_stream_names: list
          Names of output streams of this process where a name is either a
          str or a pair (str, int).
       name: str (optional)
          Name given to the process. The name helps with debugging.

    Attributes
    ----------
        out_stream_name_to_publications: dict
           Identifies connections from an out_stream of this process
           to a publication. A publication is a str.
           key: str
              Name of an out_stream of this process
           value: str
              The publication into which data for this stream is
              placed. 
        subscription_to_in_stream_names: defaultdict(list)
           Identifies the names of the input streams of this process
           that get their data from this subscription. The
           subscription is a str.
           key: str
              Name of a subscription.
           value: list
              The names of the input streams that get data from this
              subscription. 

    
    Methods
    -------
    * attach_out_stream_name_to_publication: specifies that an
      out_stream (with the specified name) of this process is
      associated with a publication.
    * attach_in_stream_name_to_subscription: specifes that an
      in_stream (with the specified name) of this process gets its
      data from the specified subscription.
    * connect_publications: connects output streams of this process to
      publications specified by the dict
      out_stream_name_to_publication
    * create_agent_to_publish_out_stream: creates an agent that puts
      elements of the specified out_stream into a routing_key called
      publication by using APMQ channel.basic_publish.
    * connect_subscriptions: The queue in APMQ contains messages where
      each message is a pair (subscription, element of a stream). This
      function gets each pair and determines the names of in_streams
      associated with this subscription. It puts
      (in_stream_name, element) into the input queue of this
      process. It binds the subscriptions for this process to the APMQ
      queue of this process.
    * create_process: makes a multiprocessing.Process with the target:
      target_of_create_process(). Assigns self.process to this process.
    * target_of_create_process: Function defined inside create_process
      and is the target function for make_process(). This function
      calls self.connect_processes of SharedMemoryProcess which calls
      the encapsulated function func(), and starts source, actuator
      computation threads of the process. It also connect publications
      and subscriptions to APMQ and starts the thread to receive
      messages specified by its subscriptions.

    """
    def __init__(self, func, in_stream_names, out_stream_names,
                 host_name, name): 
        self.func = func
        self.in_stream_names = in_stream_names
        self.out_stream_names = out_stream_names
        self.host_name = host_name
        self.name = name
        super(DistributedProcess, self).__init__(
            func, in_stream_names, out_stream_names, name)
        self.out_stream_name_to_publication = dict()
        self.subscription_to_in_stream_names = defaultdict(list)

    def attach_out_stream_name_to_publication(
            self, out_stream_name, publication):  
        self.out_stream_name_to_publication[out_stream_name] = \
            publication

    def attach_in_stream_name_to_subscription(
            self, in_stream_name, subscription):
        self.subscription_to_in_stream_names[subscription].append(
            in_stream_name)

    def connect_publications(self, out_streams):
        """
        Create an agent for each out_stream in out_streams.
        This agent publishes the out_stream on APMQ to the publication
        specified in the dict out_stream_name_to_publication

        """
        for out_stream_name in \
          self.out_stream_name_to_publication.keys(): 
          assert (out_stream_name in
                  [out_stream.name for out_stream in out_streams])
        # name_to_stream is a dict: out_stream_name -> out_stream
        name_to_stream = {s.name: s for s in out_streams}
        # Create an agent to publish the out_stream for every
        # entry in out_stream_name_to_publication.
        for out_stream_name, publication in \
          self.out_stream_name_to_publication.items():
          # Get the out_stream from its name.
          out_stream = name_to_stream[out_stream_name]
          self.create_agent_to_publish_out_stream(
                out_stream, publication)
        return

    def create_agent_to_publish_out_stream(
            self, out_stream, publication):
        def f(element_of_stream):
            message = (publication, element_of_stream)
            json_payload = json.dumps(message)
            self.channel.basic_publish(
                exchange='the_exchange',
                routing_key=publication,
                body=json_payload)
        # Create the agent: A sink which executes f()
        # for each element of out_stream. The input
        # stream of the sink is an output stream of
        # the proces.  
        sink_element(func=f, in_stream=out_stream)
        return

    def connect_subscriptions(self, in_streams):
        # callback is a method in RabbitMQ/pika.
        # Lookup receive_logs_direct.py
        def callback(ch, method, properties, body):
            # Each message in an APMQ queue is a pair:
            # (subscrption, stream_element) which is
            # the same as (publication, stream_element).
            subscription, stream_element = json.loads(body)
            # Get the names of the input streams that subscribe to
            # this subscrption.
            in_stream_names = \
              self.subscription_to_in_stream_names[subscription]
            # Put the stream elements, with the stream name, into the
            # input queue for this process.
            for in_stream_name in in_stream_names:
                self.in_queue.put((in_stream_name, stream_element))
        # Connection, channel, result, queue_name are part of
        # RabbitMQ. Look at receive_logs_direct.py
        # The next four lines are standard from RabbitMQ/pika
        # for direct exchanges.
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        ## print 'self.host_name is ', self.host_name
        ## self.connection = pika.BlockingConnection(
        ##     pika.ConnectionParameters(host=self.host_name)) 
        self.channel = (self.connection).channel()
        self.channel.exchange_declare(
            exchange='the_exchange', exchange_type='direct')
        self.result = self.channel.queue_declare(exclusive=True)
        self.queue_name = self.result.method.queue
        # Bind the APMQ queue for this process to all the
        # subscriptions made by in_streams of this process.
        for subscription in \
          self.subscription_to_in_stream_names.keys(): 
            self.channel.queue_bind(
                    exchange='the_exchange',
                    queue=self.queue_name,
                    routing_key=subscription)
        self.channel.basic_consume(
            callback, queue=self.queue_name, no_ack=True)

    def create_process(self):
        """
        Create the multiprocessing.Process that is the core of this
        DistributedProcess. 

        """
        def target_of_create_process():
            """
            Returns
            -------
               None

            """
            # SETUP
            # Create a new Stream.scheduler and set its input
            # queue to in_queue so that streams from other
            # processes that are fed to in_queue are operated
            # on by the scheduler.
            Stream.scheduler = ComputeEngine(self.name)
            # input_queue is the queue into which all streams for this
            # process are routed.
            Stream.scheduler.input_queue = self.in_queue
            # Obtain the source threads, actuator threads,and input
            # and output streams from the value returned by func().
            # Put in_stream names in the dict name_to_stream
            source_threads, actuator_threads, in_streams, out_streams = \
              self.func()
            # The scheduler for a process uses a dict name_to_stream
            # stream name -> stream.
            name_to_stream = {s.name: s for s in in_streams}
            Stream.scheduler.name_to_stream = name_to_stream
            self.connect_publications(out_streams)
            self.connect_subscriptions(in_streams)
            # Connect the output streams to other processes in the
            # same VM. This connection uses shared memory in a
            # multicore. This connection does not use APMQ.
            # See SharedMemoryProces
            self.connect_processes(out_streams)

            # START THREADS AND THE SCHEDULER
            # Create a thread to receive messages on the channel in
            # APMQ. 
            self.receive_remote_message_thread = threading.Thread(
                target=self.channel.start_consuming, args=())
            # Start the source threads
            for ss in source_threads:
                #ss_thread, ss_ready = ss
                ss.start()
            # Start the actuator threads.
            for actuator_thread in actuator_threads:
                actuator_thread.start()
            # Wait for source threads to be ready to execute, and
            # then start executing them.
            ## for ss in source_threads:
            ##     ss_thread, ss_ready = ss
            ##     ss_ready.wait()
            # Start the thread that receives messages from RabbitMQ
            self.receive_remote_message_thread.start()
            # Start the scheduler for this process
            Stream.scheduler.start()

            # JOIN THREADS
            # Join the actuator threads.
            for actuator_thread in actuator_threads:
                actuator_thread.join()
            # Join the source threads. The source threads may
            # execute for ever in which case this join() will not
            # terminate.
            for ss in source_threads:
                #ss_thread, ss_ready = ss
                ss.join()
            # Join the scheduler for this process. The scheduler
            # may execute for ever, and so this join() may not
            # terminate. You can set the scheduler to run for a
            # fixed number of steps during debugging.
            Stream.scheduler.join()

        self.process = multiprocessing.Process(
            target=target_of_create_process)


#--------------------------------------------------------------
#           make_distributed_process
#--------------------------------------------------------------
def make_distributed_process(
        compute_func, in_stream_names, out_stream_names,
        connect_sources=[], connect_actuators=[],
        publishers=[], subscribers=[],
        host_name='local_host',
        name='UnnamedDistributedProcess'):
    """
    Makes a process which computes the function compute_func
    on input streams arriving from:
     (0) other processes in the same SharedMemoryProcess and
     (1) sources in the same SharedMemoryProcess, and
     (2) subscriptions
    and outputs streams going to:
     (0) other processes in the same SharedMemoryProcess and
     (1) actuators, in the same SharedMemoryProcess, and
     (2) puts output streams on publications.

    Parameters
    ----------
    compute_func: function
       A function with parameters in_streams, out_streams.
       The lengths of in_stream_names and out_stream_names
       must equal the lengths of the parameters in_streams
       and out_streams, respectively.
    in_stream_names: list of str
    out_stream_names: list of str
    connect_sources: list of pairs
       pair is (in_stream_name, source_func)
       where in_stream_name is in in_stream_names and
       source_func is a function that generates a stream from
       a source. The function runs in its own thread.
    connect_actuators: list of pairs
       pair is (out_stream_name, actuator_func)
       where actuator_func is a function with a single argument
       which is a queue. The function gets an item from the queue
       and controls an actuator or other device. The function
       runs in its own thread.
    publishers: list of publisher
       where publisher is a triple:
       (process, out_stream_name, publication)
    subscribers: list of subcriber
       where subscriber is a triple:
       (subscriber, in_stream_name, subscription)
    
    """
    def check_parameter_types():
        assert isinstance(in_stream_names, list)
        assert isinstance(out_stream_names, list)
        assert isinstance(connect_sources, list)
        assert isinstance(connect_actuators, list)
        assert callable(compute_func)
        for in_stream_name in in_stream_names:
            assert (isinstance(in_stream_name, str) or
                    ((isinstance(in_stream_name, list) or
                    isinstance(in_stream_name, tuple))
                    and
                    (isinstance(in_stream_name[0], str) and
                     isinstance(in_stream_name[1], int)))
                     )
        for out_stream_name in out_stream_names:
            assert (isinstance(out_stream_name, str) or
                    ((isinstance(out_stream_name, list) or
                    isinstance(out_stream_name, tuple))
                    and
                    (isinstance(out_stream_name[0], str) and
                     isinstance(out_stream_name[1], int)))
                     )
        for connect_source in connect_sources:
            assert (isinstance(connect_source, tuple) or
                    isinstance(connect_source, list))
            assert connect_source[0] in in_stream_names
            assert callable(connect_source[1])
        for connect_actuator in connect_actuators:
            assert (isinstance(connect_actuator, tuple) or
                    isinstance(connect_actuator, list))
            assert connect_actuator[0] in out_stream_names
            assert callable(connect_actuator[1])
        assert isinstance(publishers, list)
        for publisher in publishers:
            assert (isinstance(publisher, list) or
                    instance(publisher, tuple))
            assert isinstance(publisher[0], DistributedProcess)
            assert isinstance(publisher[1], str)
            assert isinstance(publisher[2], str)
        assert isinstance(publishers, list)
        for subscriber in subscribers:
            assert (isinstance(subscriber, list) or
                    instance(subscriber, tuple))
            assert isinstance(subscriber[0], DistributedProcess)
            assert isinstance(subscriber[1], str)
            assert isinstance(subscriber[2], str)

    def make_process_f():
        # Step 1
        # Create in_streams and out_streams given their names.
        in_streams = [Stream(in_stream_name)
                      for in_stream_name in in_stream_names]
        out_streams = [Stream(out_stream_name)
                      for out_stream_name in out_stream_names]
        # Step 2
        # Enter key-value pairs in the dict
        # Stream.scheduler.name_to_stream  
        # The key is a stream name and the value is the stream with
        # that name. Do this for all the input and output streams.
        for in_stream in in_streams:
            Stream.scheduler.name_to_stream[in_stream.name] = \
              in_stream
        for out_stream in out_streams:
            Stream.scheduler.name_to_stream[out_stream.name] = \
              out_stream 

        # Step 3
        # Execute compute_func which sets up the agent
        # that ingests in_streams and writes out_streams.
        compute_func(in_streams, out_streams)

        # Step 4
        # Determine source_threads which is a list where an element of
        # the list is a source thread.
        # A source_thread is defined by:  source_func(source_stream).
        # This thread executes the source function and puts data from
        # the source on source_stream.
        source_threads = []
        for connect_source in connect_sources:
            source_stream_name, source_f = connect_source
            # Get the source stream from its name.
            source_stream = \
              Stream.scheduler.name_to_stream[source_stream_name]
            source_threads.append(source_f(source_stream))

        # Step 5
        # Compute actuator_threads which is a list, where an element
        # of the list is an actuator thread. An actuator thread is
        # defined by actuator_func(q) where q is a queue.
        # The queue is fed by the stream with the name specified by
        # connect_actuator. 
        actuator_threads = []
        for connect_actuator in connect_actuators:
            stream_name, actuator_func = connect_actuator
            # Get the stream from its name
            actuator_stream = \
              Stream.scheduler.name_to_stream[stream_name]
            # q is the queue into which this actuator stream's
            # elements are placed.
            q = Queue.Queue()
            # Create an agent that puts the stream in the queue.
            stream_to_queue(actuator_stream, q)
            actuator_thread =  threading.Thread(
                target=actuator_func,
                args=[q])
            actuator_threads.append(actuator_thread)
        return (source_threads, actuator_threads, in_streams,
                out_streams)  

    # make the process
    check_parameter_types()
    return DistributedProcess(
        make_process_f, in_stream_names, out_stream_names,
        host_name, name)

