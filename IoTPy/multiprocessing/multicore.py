
"""
This module defines a Class, StreamProcess, for making a multiprocess
program that runs on a multicore (shared-memory) computer.

For distributed computing with multiple computers with different IP 
addresses, see the module DistributedComputing.py.

"""
import multiprocessing
from collections import defaultdict
import threading

import sys
import os
import Queue
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
# sink is in the agent_types folder
# compute_engine, stream are in the core folder
from sink import stream_to_queue
from compute_engine import ComputeEngine
from stream import Stream

class StreamProcess(object):
    """
    Class for creating and executing a process in a shared-memory
    machine.

    Parameters
    ----------
       func: function
          The function that is encapsulated to create this process.
       name: str (optional)
          Name given to the process. The name helps with debugging.

    Attributes
    ----------
    in_queue: multiprocessing.Queue()
       All sources put their data, tagged with the name of the
       destination stream, in this queue.
    out_to_in: defaultdict(list)
       key: str
            Name of an out_stream
       value: name_and_queue_list
              list of pairs (2-tuples) where each pair is:
              (1) name: pickled object
                  This name is the name of the input stream
                  of a function in the receiver process. This
                  name may be different from the name of the 
                  stream in the sending process attached to it.
                  e.g. str: the name of the target stream, or
                  e.g. pair (str, int) where str is the name
                  of an array of target streams and int is an index
                  into the array. 
              (2) stream_process: StreamProcess
                      The receiver stream process.
    process: multiprocessing.Process
       The process that executes the threads running the sources and
       the encapsulated function. This process is created by the call
       connect_process().
    
    Methods
    -------
    * attach_stream: specifies that a sending stream on this process
    is the same as a receiving stream in some other process.
    * connect_processor: connects all the attached output streams of
    func in this process to input streams of functions in other processes
    * target_of_connect_process: the target function for make process. This
    function calls the encapsulated function func, and starts threads.
    * connect_process: makes a multiprocessing.Process with the target:
    target_of_connect_process. Assigns self.process to this process.
    * start: starts self.process
    * join: joins self.process

    """
    def __init__(self, func, name='StreamProcess'):
        self.func = func
        self.name = name
        self.in_queue = multiprocessing.Queue()
        self.out_to_in = defaultdict(list)
        self.process = None
    def start(self):
        self.process.start()
    def join(self):
        self.process.join()
    def attach_stream(
            self, sending_stream_name, receiving_process,
            receiving_stream_name):   
        self.out_to_in[sending_stream_name].append(
            (receiving_stream_name, receiving_process))
    def connect_processor(self, out_streams):
        """
        Parameters
    ,     ----------
        out_streams: list of Stream
            list of output streams of the function. Each of these
            output streams must have a unique name.

        Notes
        -----
        Creates an agent that does the following:
        for each stream s with a name, s.name, in out_to_in.keys(),
        for each element v of stream s, the  agent obtains
        out_to_in[s.name] which is a list of pairs:
        (1) receiver stream name, (2) receiver streaming process
        For each receiver stream name, receiver streaming process in
        this list,  the agent puts [receiver stream name, v] in the
        in_queue of the receiving process.
        The receiving process then appends v to the stream in the
        receiving process with the specified receiver name.

        """
        # name_to_stream is a dict: sending_stream_name -> sending_stream
        name_to_stream = {s.name: s for s in out_streams}
        for sending_stream_name, stream_procs in self.out_to_in.items():
            # stream_procs is a list of pairs, where each pair is:
            # (receiving stream name, receiving stream processor)
            for receiver_stream_name, receiver_proc in stream_procs:
                sending_stream = name_to_stream[sending_stream_name]
                # stream_to_queue is an agent that puts tuples on the 
                # receiving queue where each tuple is:
                # (receiver stream name, element of the sending stream)
                # For help in debugging we give a name to this agent
                # which is:
                # stream_to_queue plus sending and receiving stream names.
                stream_to_queue(
                    sending_stream, receiver_proc.in_queue,
                    lambda x: [receiver_stream_name, x],
                    name=('stream_to_queue_'+ sending_stream_name +
                          receiver_stream_name)
                          )

    def target_of_connect_process(self):
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
        Stream.scheduler.input_queue = self.in_queue
        # Obtain the externalities of func, i.e. its
        # source threads, actuator threads,and input and output
        # streams. Put in_stream names in the dict name_to_stream
        source_threads, actuator_threads, in_streams, out_streams = \
          self.func() 
        name_to_stream = {s.name: s for s in in_streams}
        Stream.scheduler.name_to_stream = name_to_stream
        # Connect the output streams to other processes
        self.connect_processor(out_streams)

        # START THREADS AND THE SCHEDULER
        # Start the source threads
        for ss in source_threads:
            ss_thread, ss_ready = ss
            ss_thread.start()
        # Start the actuator threads.
        for actuator_thread in actuator_threads:
            actuator_thread.start()
        # Wait for source threads to be ready to execute, and
        # then start executing them.
        for ss in source_threads:
            ss_thread, ss_ready = ss
            ss_ready.wait()
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

def make_process(
        compute_func, in_stream_names, out_stream_names,
        connect_sources=[], connect_actuators=[],
        process_name='unnamed'):
    """
    Makes a process which computes the function compute_func
    on streams arriving from other processes and sources, and
    outputs streams going to other processes and actuators.

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
    
    """
    # CHECK PARAMETER TYPES
    assert isinstance(in_stream_names, list)
    assert isinstance(out_stream_names, list)
    assert isinstance(connect_sources, list)
    assert isinstance(connect_actuators, list)
    assert callable(compute_func)
    for in_stream_name in in_stream_names:
        assert isinstance(in_stream_name, str)
    for out_stream_name in out_stream_names:
        assert isinstance(out_stream_name, str)
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
            Stream.scheduler.name_to_stream[in_stream.name] = in_stream
        for out_stream in out_streams:
            Stream.scheduler.name_to_stream[out_stream.name] = out_stream

        # Step 3
        # Execute compute_func which sets up the network of agents
        # that ingests in_streams and writes out_streams.
        compute_func(in_streams, out_streams)

        
        # Step 1
        # Compute source_threads which is a list where an element of
        # the list is a source thread.
        # A source_thread is defined by:
        # source_func(source_stream).
        # This thread executes the source function and puts data from
        # the source on source_stream.
        source_threads = []
        for connect_source in connect_sources:
            source_stream_name, source_f = connect_source
            source_stream = \
              Stream.scheduler.name_to_stream[source_stream_name]
            source_threads.append(source_f(source_stream))

        # Step 2
        # Compute actuator_threads which is a list, where an element
        # of the list is an actuator thread. An actuator thread is
        # defined by actuator_func(q) where q is a queue.
        # The queue is fed by the stream with the name specified by
        # connect_actuator. 
        actuator_threads = []
        for connect_actuator in connect_actuators:
            stream_name, actuator_func = connect_actuator
            actuator_stream = \
              Stream.scheduler.name_to_stream[stream_name]
            q = Queue.Queue()
            stream_to_queue(actuator_stream, q)
            actuator_thread =  threading.Thread(
                target=actuator_func,
                args=[q])
            actuator_threads.append(actuator_thread)
        return (source_threads, actuator_threads, in_streams, out_streams)

    # make the process
    return StreamProcess(func=make_process_f, name=process_name)


def check_processes(process_list):
    assert isinstance(process_list, list), \
      "process_list must be a list"
    assert process_list, "process_list must not be empty"
    for process in process_list:
        assert isinstance(process, StreamProcess)
    return True

def check_connections(connection_list):
    assert isinstance(connection_list, list) \
      or isinstance(connection_list, tuple), \
      "connection_list must be a list or tuple"
    for connection in connection_list:
        assert isinstance(connection, list) or \
          isinstance(connection, tuple),\
          "A connection must be a list or tuple"
        assert len(connection) == 4,\
          "Connection must have length 4"
    return True

def check_process_in_connections(process_list, connection_list):
    process_dict = {
        process_name : function for
        (process_name, function) in process_list
        }
    for connection in connection_list:
        out_proc, out_stream, in_proc, in_stream = connection
        assert out_proc in process_dict, \
          "output process in connection is not in process list"
        assert in_proc in process_dict, \
          "input process in connection is not in process list"
    return True

def connect_stream(sender, sending_stream_name,
                   receiver, receiving_stream_name):
    sender.attach_stream(
        sending_stream_name, receiver, receiving_stream_name
        )

def connect_streams(processes, connections):
    """
    Parameters
    ----------
       processes: list of StreamProcess
       connections: list of 4-tuples
           each 4-tuple is (sender, sending_stream_name,
                            receiver, receiving_stream_name)
           where sender, receiver are StreamProcess in
           processes.
           sending_stream_name is a str and is the name of
           an output stream of sender.
           receiving_stream_name is a str and is the name of
           an input stream of receiver.
    Makes the connection for each 4-tuple
      
    """
    for connection in connections:
        sender, sending_stream_name, \
          receiver, receiving_stream_name = connection
        assert sender in processes
        assert receiver in processes
        assert isinstance(sending_stream_name, str)
        assert isinstance(receiving_stream_name, str)
        connect_stream(sender, sending_stream_name,
                       receiver, receiving_stream_name)
    
def run_multiprocess(processes, connections=[]):
    check_processes(processes)
    check_connections(connections)
    connect_streams(processes, connections)
    for process in processes:
        process.connect_process()
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    

def single_process_single_source(
        source_func, compute_func):
    assert callable(source_func)
    assert callable(compute_func)
    def g(in_streams, out_streams):
        return compute_func(in_streams[0])
    proc = make_process(
        compute_func=g, in_stream_names=['in'], out_stream_names=[],
        connect_sources=[['in', source_func]]
        )
    run_multiprocess(processes=[proc], connections=[])

def single_process_multiple_sources(list_source_func, compute_func):
    in_stream_names = [
        'in_'+ str(i) for i in range(len(list_source_func))]
    connect_sources = [['in_' + str(i), list_source_func[i]]
                       for i in range(len(list_source_func))]
    out_stream_names=[]
    def f(in_streams, out_streams):
        return compute_func(in_streams)

    proc = make_process(
        f, in_stream_names, out_stream_names,
        connect_sources)
    run_multiprocess(processes=[proc], connections=[])
    
    
    
