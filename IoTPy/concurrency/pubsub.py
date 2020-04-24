"""
This module defines a Class, DistributedProcess, for making a multiprocess
program that runs on a multicore (shared-memory) computer and which
can publish and subscribe streams using AMQP. A virtual machine (VM)
is a set of DistributedProcess. A DistributedProcess is an extension of
Proc.

For distributed computing with multiple computers with different IP 
addresses, see the module DistributedComputing.py.

"""
import sys
#import os
is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue

import multiprocessing
from collections import defaultdict
import threading
import pika
import json
import time

sys.path.append("../agent_types")
sys.path.append("../core")

# stream, helper_control are in the core folder
from stream import Stream
from helper_control import _no_value
# sink is in the agent_types folder
from sink import stream_to_queue, sink_element
from op import map_element, map_list
from multicore import MulticoreProcess, multicore, copy_data_to_stream
from multicore import finished_source, make_connections_from_connect_streams
from print_stream import print_stream
from system_parameters import BUFFER_SIZE, MAX_NUM_SOURCES, MAX_NUM_PROCESSES
from utils import check_processes_connections_format, check_connections_validity
from compute_engine import ComputeEngine

#--------------------------------------------------------------
#           DistributedProcess
#--------------------------------------------------------------
class PubSub(MulticoreProcess):
    """
    Attributes
    ----------
        out_stream_name_to_publications: dict
           Identifies connections from an out_stream of this process
           to a publication. A publication is a str. The output of the
           specified stream is published to the specified publication.
           key: str
              Name of an out_stream of this process
           value: str
              The publication into which data for this stream is
              placed. 
        subscription_to_in_stream_names: defaultdict(list)
           Identifies the names of the input streams of this process
           that get their data from this subscription. The
           subscription is a str. The specified input streams subscribe
           to the publication with the specified name (the subscription).
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
    def __init__(self, spec, connect_streams, publishers, subscribers, host_name, name):
        self.host_name = host_name
        self.publishers = publishers
        self.subscribers = subscribers
        # Initiate MulticoreProcess(spec, connect_streams, name)
        super(PubSub, self).__init__(spec, connect_streams, name)
        self.out_stream_name_to_publication = dict()
        self.subscription_to_in_stream_names = defaultdict(list)
        self.attach_out_stream_names_to_publications()
        self.attach_in_stream_names_to_subscriptions()

    def attach_out_stream_names_to_publications(self):
        """
        Each out_stream is connected to at most one publication.

        """
        for three_tuple in self.publishers:
            process_name, out_stream_name, publication = three_tuple
            if process_name == self.name:
                self.out_stream_name_to_publication[out_stream_name] = \
                  publication
        ## print ('in attach_out_stream_names_to_publications')
        ## print ('process name is ', self.name)
        ## print ('out_stream_name_to_publication is ', self.out_stream_name_to_publication)

    def attach_in_stream_names_to_subscriptions(self):
        """
        Each subscription may be copied into an arbitrary number
        of in_streams.

        """
        for three_tuple in self.subscribers:
            process_name, in_stream_name, subscription = three_tuple
            if process_name == self.name:
                self.subscription_to_in_stream_names[subscription].append(
                    in_stream_name)
        ## print ('in attach_in_stream_names_to_subscriptions')
        ## print ('process name is ', self.name)
        ## print ('subscription_to_in_stream_names is ', self.subscription_to_in_stream_names)

    def connect_publications(self):
        """
        Create an agent for each out_stream in out_streams.
        This agent publishes the out_stream on APMQ to the publication
        specified in the dict out_stream_name_to_publication

        ## """
        ## print ('in connect_publications')
        ## print ('process name is ', self.name)
        ## print ('out_stream_name_to_publication ', self.out_stream_name_to_publication)
        for out_stream_name in \
          self.out_stream_name_to_publication.keys(): 
          assert (out_stream_name in
                  [out_stream.name for out_stream in self.out_streams]),\
                  " '{}' is not a name of an out_stream".format(out_stream_name)
        # name_to_out_stream is a dict: out_stream_name -> out_stream
        name_to_out_stream = {s.name: s for s in self.out_streams}
        # Create an agent to publish the out_stream for every
        # entry in out_stream_name_to_publication.
        for out_stream_name, publication in \
          self.out_stream_name_to_publication.items():
          ## print ('')
          ## print ('in connect_publications')
          ## print ('out_stream_name is ', out_stream_name)
          ## print ('publication is ', publication)
          ## print ('')
          # Get the out_stream from its name.
          out_stream = name_to_out_stream[out_stream_name]
          self.create_agent_to_publish_out_stream(
                out_stream, publication)
        return

    def create_agent_to_publish_out_stream(
            self, out_stream, publication):
        self.publisher_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        self.publisher_channel = self.publisher_connection.channel()
        self.publisher_channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

        def f(element_of_stream):
            ## print ('in create_agent_to_publish_out_stream')
            ## print ('element_of_stream is ', element_of_stream)
            # Don't publish _no_value elements
            if element_of_stream is _no_value:
                return element_of_stream
            # Publish elements that are not _no_value
            #message = (publication, element_of_stream)
            message = element_of_stream
            ## print  ('in create_agent_to_publish_out_stream')
            ## print ('message is ', message)
            json_payload = json.dumps(message)
            ## print ('json_payload is ', json_payload)
            self.publisher_channel.basic_publish(
                exchange='the_exchange',
                routing_key=publication,
                body=json_payload)
            ## print ('in create_agent_to_publish_out_stream')
            ## print ('body of message is ', json_payload)
            ## print ('')
        # Create the agent: A sink which executes f()
        # for each element of out_stream. The input
        # stream of the sink is an output stream of
        # the proces.  
        sink_element(func=f, in_stream=out_stream)
        return

    def connect_subscriptions(self):
        # callback is a method in RabbitMQ/pika.
        # Lookup receive_logs_direct.py
        def callback(ch, method, properties, body):
            # Each message in an APMQ queue is a pair:
            # (subscrption, stream_element) which is
            # the same as (publication, stream_element).
            # subscription, stream_element = json.loads(body)
            ## print ('in callback in connect_subscriptions')
            stream_element = json.loads(body)
            ## print ('stream_element is ', stream_element)
            # The names of the input streams that subscribe to
            # this subscrption are subscription_to_in_stream_names[subscription].
            # Put the stream element obtained from the subscription
            # into the input queue for this process tagged with the
            # name of the subscribing stream.
            for in_stream_name in self.subscription_to_in_stream_names[subscription]:
                self.in_queue.put((in_stream_name, stream_element))
            return

        #----------------------------------------------------------
        # APMQ connection, channel, binding, ......
        # Connection, channel, result, queue_name are part of
        # RabbitMQ. Look at receive_logs_direct.py
        # The next four lines are standard from RabbitMQ/pika
        # for direct exchanges.
        self.subscriber_connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host_name)) 
        self.subscriber_channel = self.subscriber_connection.channel()
        self.subscriber_channel.exchange_declare(
            exchange='the_exchange', exchange_type='direct')
        self.subscriber_result = self.subscriber_channel.queue_declare(queue='', exclusive=True)
        self.subscriber_queue_name = self.subscriber_result.method.queue
        # Bind the APMQ queue for this process to all the
        # subscriptions made by in_streams of this process.
        for subscription in \
          self.subscription_to_in_stream_names.keys(): 
            self.subscriber_channel.queue_bind(
                    exchange='the_exchange',
                    queue=self.subscriber_queue_name,
                    routing_key=subscription)
        self.subscriber_channel.basic_consume(
            queue=self.subscriber_queue_name, on_message_callback=callback, auto_ack=True)

    def make_process(self):
        """
        Create the multiprocessing.Process that is the core of this
        DistributedProcess. 

        """
        def target():
            """
            Returns
            -------
               None

            """
            self.create_in_streams_of_compute_func()
            self.create_in_stream_signals_for_C_datatypes()
            self.create_out_streams_for_compute_func()
            # CREATE THE COMPUTE AGENT FOR THIS PROCESS.
            self.compute_func(
                self.in_streams, self.out_streams,
                *self.positional_args, **self.keyword_args)
            self.create_agents_to_copy_each_out_stream_to_in_streams()
            self.create_agents_to_copy_buffers_to_in_streams()
            self.connect_publications()
            self.connect_subscriptions()

            # CREATE A NEW STREAM.SCHEDULER FOR THIS PROCESS
            # Specify the scheduler, input_queue and name_to_stream for
            # this processes.
            Stream.scheduler = ComputeEngine(self)
            # input_queue is the queue into which all streams for this
            # process are routed.
            Stream.scheduler.input_queue = self.in_queue
            # The scheduler for a process uses a dict, name_to_stream.
            # name_to_stream[stream_name] is the stream with the name stream_name.
            Stream.scheduler.name_to_stream = self.name_to_stream

            self.create_source_threads()

            # Create a thread to receive messages on the channel in
            # APMQ. 
            self.receive_remote_message_thread = threading.Thread(
                target=self.subscriber_channel.start_consuming, args=())

            # START SOURCE THREADS, APMQ RECEIVE THREAD AND START SCHEDULER.
            # Starting the scheduler starts a thread --- the main thread --- of this
            # process. The scheduler thread gets a ready agent from the in_queue of
            # this process and then executes the next step of the agent.
            Stream.scheduler.start()
            ## print ('starting source threads')
            ## for source_thread in self.source_threads: print (source_thread)
            for source_thread in self.source_threads: source_thread.start()
            self.receive_remote_message_thread.start()

            # JOIN SOURCE THREADS, APMQ RECEIVE THREAD, AND JOIN SCHEDULER.
            for source_thread in self.source_threads: source_thread.join()
            Stream.scheduler.join()
            self.receive_remote_message_thread.join()
            return

        # Create the process.
        self.process = multiprocessing.Process(target=target)

def make_distributed_processes(process_specs, connect_streams,
                               publishers, subscribers, host_name, **kwargs):
    
    processes = process_specs
    source_status = multiprocessing.Array('B', MAX_NUM_SOURCES)
    queue_status = multiprocessing.Array('B', MAX_NUM_PROCESSES)
    connections = make_connections_from_connect_streams(connect_streams)
    check_processes_connections_format(processes, connections)
    check_connections_validity(processes, connections)
    procs = {}
    # In the following name is a process name and
    # spec is the specification of the process.
    for name, spec in processes.items():
        procs[name] = PubSub(spec, connect_streams, publishers, subscribers, host_name, name)
    # Make the dict relating output streams to queues of receiving
    # processes and to in_stream_signal_names.
    for name in processes.keys():
        procs[name].make_out_to_q_and_in_stream_signal_names(procs)
    # Make the dict relating in_streams of processes to output
    # processes and output streams to which they are connected.
    for name in processes.keys():
        procs[name].make_in_to_out(procs, connections)

    # Create source ids and set source_status
    source_id_count=0
    source_ids = {}
    for process_name, spec in processes.items():
        source_ids[process_name] = {}
        sources_dict = spec['sources']
        for source_name in sources_dict.keys():
            source_ids[process_name][source_name] = source_id_count
            source_status[source_id_count] = 1
            source_id_count += 1
    for process_name in processes.keys():
        this_process = procs[process_name]
        this_process.source_ids = source_ids
        this_process.source_status = source_status

    #Create main_lock and pass it to all processes.
    main_lock = multiprocessing.Lock()
    # Create process ids and set queue_status
    process_id_count=0
    process_ids = {}
    for process_name in processes.keys():
        process_ids[process_name] = process_id_count
        queue_status[process_id_count] = 1
        process_id_count += 1
    for process_name in processes.keys():
        this_process = procs[process_name]
        this_process.process_ids = process_ids
        this_process.queue_status = queue_status
        this_process.main_lock = main_lock
        this_process.NUM_PROCESSES = len(processes)
        this_process.all_process_specs = processes
        this_process.all_procs = procs
    for name in processes.keys():
        procs[name].make_process()
    process_list = [procs[name].process for name in processes.keys()]
    return process_list, procs

def distributed(process_specs, connect_streams,
                publishers, subscribers, host_name, **kwargs):
    process_list, procs = make_distributed_processes(
        process_specs, connect_streams,
        publishers, subscribers, host_name, **kwargs)
    for name in process_specs.keys():
        procs[name].process.start()
    for name in process_specs.keys():
        procs[name].process.join()
    for name in process_specs.keys():
        procs[name].process.terminate()

## #--------------------------------------------------------------
## #           distributed_process
## #--------------------------------------------------------------
## def distributed_process(
##         compute_func, in_stream_names, out_stream_names,
##         connect_sources=[], connect_actuators=[],
##         host_name='localhost',
##         name='UnnamedDistributedProcess'):
##     """
##     Makes a process which computes the function compute_func
##     on input streams arriving from:
##      (0) other processes in the same SharedMemoryProcess and
##      (1) sources in the same SharedMemoryProcess, and
##      (2) subscriptions
##     and outputs streams going to:
##      (0) other processes in the same SharedMemoryProcess and
##      (1) actuators, in the same SharedMemoryProcess, and
##      (2) puts output streams on publications.

##     Parameters
##     ----------
##     compute_func: function
##        A function with parameters in_streams, out_streams.
##        The lengths of in_stream_names and out_stream_names
##        must equal the lengths of the parameters in_streams
##        and out_streams, respectively.
##     in_stream_names: list of str
##     out_stream_names: list of str
##     connect_sources: list of pairs
##        pair is (in_stream_name, source_func)
##        where in_stream_name is in in_stream_names and
##        source_func is a function that generates a stream from
##        a source. The function runs in its own thread.
##     connect_actuators: list of pairs
##        pair is (out_stream_name, actuator_func)
##        where actuator_func is a function with a single argument
##        which is a queue. The function gets an item from the queue
##        and controls an actuator or other device. The function
##        runs in its own thread.
##     publishers: list of publisher
##        where publisher is a triple:
##        (process, out_stream_name, publication)
##     subscribers: list of subcriber
##        where subscriber is a triple:
##        (subscriber, in_stream_name, subscription)
    
##     """
##     def check_parameter_types():
##         assert isinstance(in_stream_names, list)
##         assert isinstance(out_stream_names, list)
##         assert isinstance(connect_sources, list)
##         assert isinstance(connect_actuators, list)
##         assert callable(compute_func)
##         for in_stream_name in in_stream_names:
##             assert (isinstance(in_stream_name, str) or
##                     ((isinstance(in_stream_name, list) or
##                     isinstance(in_stream_name, tuple))
##                     and
##                     (isinstance(in_stream_name[0], str) and
##                      isinstance(in_stream_name[1], int)))
##                      )
##         for out_stream_name in out_stream_names:
##             assert (isinstance(out_stream_name, str) or
##                     ((isinstance(out_stream_name, list) or
##                     isinstance(out_stream_name, tuple))
##                     and
##                     (isinstance(out_stream_name[0], str) and
##                      isinstance(out_stream_name[1], int)))
##                      )
##         for connect_source in connect_sources:
##             assert (isinstance(connect_source, tuple) or
##                     isinstance(connect_source, list))
##             assert connect_source[0] in in_stream_names
##             assert callable(connect_source[1])
##         for connect_actuator in connect_actuators:
##             assert (isinstance(connect_actuator, tuple) or
##                     isinstance(connect_actuator, list))
##             assert connect_actuator[0] in out_stream_names
##             assert callable(connect_actuator[1])

##     def make_process_f():
##         # Step 1
##         # Create in_streams and out_streams given their names.
##         in_streams = [Stream(in_stream_name)
##                       for in_stream_name in in_stream_names]
##         out_streams = [Stream(out_stream_name)
##                       for out_stream_name in out_stream_names]
##         # Step 2
##         # Enter key-value pairs in the dict
##         # Stream.scheduler.name_to_stream  
##         # The key is a stream name and the value is the stream with
##         # that name. Do this for all the input and output streams.
##         for in_stream in in_streams:
##             Stream.scheduler.name_to_stream[in_stream.name] = \
##               in_stream
##         for out_stream in out_streams:
##             Stream.scheduler.name_to_stream[out_stream.name] = \
##               out_stream 

##         # Step 3
##         # Execute compute_func which sets up the agent
##         # that ingests in_streams and writes out_streams.
##         compute_func(in_streams, out_streams)

##         # Step 4
##         # Determine source_threads which is a list where an element of
##         # the list is a source thread.
##         # A source_thread is defined by:  source_func(source_stream).
##         # This thread executes the source function and puts data from
##         # the source on source_stream.
##         source_threads = []
##         for connect_source in connect_sources:
##             source_stream_name, source_f = connect_source
##             # Get the source stream from its name.
##             source_stream = \
##               Stream.scheduler.name_to_stream[source_stream_name]
##             source_threads.append(source_f(source_stream))

##         # Step 5
##         # Compute actuator_threads which is a list, where an element
##         # of the list is an actuator thread. An actuator thread is
##         # defined by actuator_func(q) where q is a queue.
##         # The queue is fed by the stream with the name specified by
##         # connect_actuator. 
##         actuator_threads = []
##         for connect_actuator in connect_actuators:
##             stream_name, actuator_func = connect_actuator
##             # Get the stream from its name
##             actuator_stream = \
##               Stream.scheduler.name_to_stream[stream_name]
##             # q is the queue into which this actuator stream's
##             # elements are placed.
##             q = queue.Queue()
##             # Create an agent that puts the stream in the queue.
##             stream_to_queue(actuator_stream, q)
##             actuator_thread =  threading.Thread(
##                 target=actuator_func,
##                 args=[q])
##             actuator_threads.append(actuator_thread)
##         return (source_threads, actuator_threads, in_streams,
##                 out_streams)  

##     # make the process
##     check_parameter_types()
##     return DistributedProcess(
##         make_process_f, in_stream_names, out_stream_names,
##         host_name, name)

#---------------------------------------------------------------
#
def f(in_streams, out_streams, ADDEND):
    def ff(v):
        return v + ADDEND
    map_element(ff, in_streams[0], out_streams[0])

def g(in_streams, out_streams):
    def gg(v):
        return v + 100
    s = Stream('s')
    map_element(func=gg, in_stream=in_streams[0], out_stream=s)
    print_stream(s, s.name)

def h(in_streams, out_streams):
    pass


# Target of source thread.
def source_thread_target(proc, stream_name):
    num_steps, step_size = 3, 3
    for i in range(num_steps):
        data = list(range(i*step_size, (i+1)*step_size))
        copy_data_to_stream(data, proc, stream_name)
        time.sleep(0.001)

    finished_source(proc, stream_name)

def test_parameter(ADDEND_VALUE):
    # Specify process_specs and connections.
    # This example has two processes:
    # (1) p0 and
    # (2) p1.

    # Specification of p0:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has a single output stream called 'out'
    # which is of type int ('i').
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function f.
    # (4) Keyword arguments: Function f has a keyword argument
    # called ADDEND.
    # (5) sources: This process has a single source called
    # 'acceleration'. The source thread target is specified by
    # the function source_thread_target. This function generates
    # int ('i').
    # (6) actuators: This process has no actuators.

    # Specification of p1:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has no outputs.
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function g.
    # (4) Keyword arguments: Function g has no keyword argument
    # (5) sources: This process has no sources
    # (6) actuators: This process has no actuators.

    # Connections between processes.
    # (1) Output 'out' of 'p0' is connected to input 'in' of p1.
    # (2) The source, 'acceleration', of 'p0' is connected to input
    #     'in' of 'p1'.

    process_specs = \
      {
        'p0':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [('out', 'i')],
            'compute_func': f,
            'keyword_args' : {'ADDEND' :ADDEND_VALUE},
            'sources':
              {'acceleration':
                  {'type': 'i',
                   'func': source_thread_target
                  },
               },
            'actuators': {}
           },
        'p1':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
            'keyword_args' : {},
            'sources': {},
            'actuators': {}
           }
      }
    
    connect_streams = [['p0', 'acceleration', 'p0', 'in']]

    publishers=[['p0', 'out', 'pubsub0']]
    subscribers=[['p1', 'in', 'pubsub0']]
    host_name = 'localhost'
    kwargs = {}

    # Create and run multiple processes in a multicore machine.
    distributed(process_specs, connect_streams,
                publishers, subscribers, host_name, **kwargs)
    return
    
def test_token_exchange_two_processes():
    def target(proc, stream_name):
        data = [1]
        copy_data_to_stream(data, proc, stream_name)

    def f(in_streams, out_streams):
        def ff(v):
            print ('p0')
            return v
        map_element(ff, in_streams[0], out_streams[0])

    def g(in_streams, out_streams):
        def gg(v):
            print ('p1')
            return v
        map_element(gg, in_streams[0], out_streams[0])
        
    process_specs = \
      {
        'p0':
           {'in_stream_names_types': [('in', 'x')],
            'out_stream_names_types': [('out', 'x')],
            'compute_func': f,
            'sources':
              {'acceleration':
                  {'type': 'x',
                   'func': target
                  },
               }
           },
        'p1':
           {'in_stream_names_types': [('in', 'x')],
            'out_stream_names_types': [('out', 'x')],
            'compute_func': g
           }
      }
    
    connect_streams = [['p0', 'acceleration', 'p0', 'in']]

    publishers=[['p0', 'out', 'pubsub0'],
                ['p1', 'out', 'pubsub1']]
    subscribers=[['p1', 'in', 'pubsub0'],
                 ['p0', 'in', 'pubsub1']]
    host_name = 'localhost'
    kwargs = {}

    # Create and run multiple processes in a multicore machine.
    distributed(process_specs, connect_streams,
                publishers, subscribers, host_name, **kwargs)
    return
    
if __name__ == '__main__':
    #test_parameter(500)
    test_token_exchange_two_processes()

