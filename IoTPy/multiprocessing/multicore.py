
"""
This module has 3 parts:
(0) It has a Class, SharedMemoryProcess, for making a multiprocess
    program that runs on a multicore (shared-memory) computer.
    For distributed computing with multiple computers with different
    IP addresses, see the module distributed.py.
(1) It has a function shared_memory_process which makes and returns a
    multicore process.
(2) It has a class, MulticoreApp, for making an application consisting
    of a single multicore computer (and no message passing to other
    computers). A MulticoreApp consists of a set of SharedMemoryProcesses
    and connections between them.

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
#from distributed import make_distributed_process

#--------------------------------------------------------------
#           PART 0. SharedMemoryProcess
#--------------------------------------------------------------
class SharedMemoryProcess(object):
    """
    Class for creating and executing a process in a shared-memory
    multicomputer. This class has an attribute called 'process' of type
    multiprocessing.Process which is the process that executes code.
    A SharedMemoryProcess communicates only with other
    SharedMemoryProcess on a multicomputer, by using shared memory. It
    does not use message passing and cannot communicate with other
    computers. For distributed applications see distributed.py and
    VM.py 

    Parameters
    ----------
       func: function
          The function that is encapsulated to create this process.
          This function is returned by shared_memory_process()
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
    in_queue: multiprocessing.Queue()
       All sources put their data, tagged with the name of the
       destination stream, in this queue.
    out_to_in: defaultdict(list)
       Identifies connections from an out_stream of this process to an
       in_stream of another process in the same shared-memory
       multicomputer. 
       key: str
            Name of an out_stream of this process
       value: name_and_queue_list
              list of pairs (2-tuples) where each pair is:
              (1) name: pickled object
                  This name is the name of the input stream
                  of a function in the receiver process. This
                  name may be different from the name of the 
                  stream in the sending process attached to it.
                  This name is typically a str: the name of the
                  target stream. This name can also be a
                  pair (str, int) where str is the name
                  of an array of target streams and int is an index
                  into the array. 
              (2) shared_memory_process: SharedMemoryProcess
                      The receiver process.
    process: multiprocessing.Process
       The core process of SharedMemoryProcess. This process executes the
       the source threads, the actuator threads and the computation
       thread. This process is created by the call
       self.create_process().
    
    Methods
    -------
    * start: starts self.process
    * join: joins self.process
    * attach_stream: specifies that a sending stream on this process
      is the same as a receiving stream in some other process.
    * connect_processes: connects all the attached output streams of
      this process to input streams of other processes in the same
      shared-memory space.
    * target_of_create_process: the target function for
      shared_memory_process(). This function calls the encapsulated function
      func(), and starts source, actuator and computation threads. 
    * create_process: makes a multiprocessing.Process with the target:
      target_of_create_process(). Assigns self.process to this process.

    """
    def __init__(self, func, in_stream_names, out_stream_names,
                 name='SharedMemoryProcess'): 
        self.func = func
        self.in_stream_names = in_stream_names
        self.out_stream_names = out_stream_names
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
        """
        Parameters
        ----------
        sending_stream_name: str
           The name of an output stream of the sending
            SharedMemoryProcess. 
        receiving_process: SharedMemoryProcess
           The process receiving the stream sent by self.process.
        receiving_stream_name: str
           The name of input stream of the receiving
           SharedMemoryProcess. 

        """
        self.out_to_in[sending_stream_name].append(
            (receiving_stream_name, receiving_process))

    def connect_processes(self, out_streams):
        """
        Connects output streams of processes to input streams of
        processes.

        Parameters
        ----------
        out_streams: list of Stream
            list of output streams of the process. Each of these
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
                # Get the sending stream from its name.
                sending_stream = name_to_stream[sending_stream_name]
                # stream_to_queue(....) is an agent that puts tuples on the 
                # input queue of the receiving process where each tuple is:
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

    def create_process(self):
        """
        Create the multiprocessing.Process that is the core of this
        SharedMemoryProcess. 

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
            # Obtain the externalities of func, i.e. its
            # source threads, actuator threads,and input and output
            # streams. Put in_stream names in the dict name_to_stream
            source_threads, actuator_threads, in_streams, out_streams = \
              self.func()
            # The scheduler for a process uses a dict name_to_stream
            # from stream name to stream.
            name_to_stream = {s.name: s for s in in_streams}
            Stream.scheduler.name_to_stream = name_to_stream
            # Connect the output streams of ths process to input
            # streams of other processes as specified in the dict
            # self.out_to_in. 
            self.connect_processes(out_streams)

            # START THREADS AND THE SCHEDULER
            # Start the source threads
            for source_thread in source_threads:
                source_thread.start()
            # Start the actuator threads.
            for actuator_thread in actuator_threads:
                actuator_thread.start()
            # Start the scheduler for this process
            Stream.scheduler.start()

            # JOIN THREADS
            # Join the actuator threads.
            for actuator_thread in actuator_threads:
                actuator_thread.join()
            # Join the source threads. The source threads may
            # execute for ever in which case this join() will not
            # terminate.
            for source_thread in source_threads:
                source_thread.join()
            # Join the scheduler for this process. The scheduler
            # may execute for ever, and so this join() may not
            # terminate. You can set the scheduler to run for a
            # fixed number of steps during debugging.
            Stream.scheduler.join()

        self.process = multiprocessing.Process(
            target=target_of_create_process)


#--------------------------------------------------------------
#           PART 1. shared_memory_process
#--------------------------------------------------------------
def shared_memory_process(
        compute_func, in_stream_names, out_stream_names,
        connect_sources=[], connect_actuators=[],
        name='unnamed'):
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
    def check_shared_memory_parameters():
        # CHECK PARAMETER TYPES
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

    def shared_memory_process_f():
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
    check_shared_memory_parameters()
    return SharedMemoryProcess(shared_memory_process_f, in_stream_names,
                         out_stream_names, name)

#--------------------------------------------------------------
#           Part 2: Multiprocess
#--------------------------------------------------------------
class Multiprocess(object):
    """
    Makes a multicore application from a collection of processes and
    connections between their output and input streams.

    Parameters
    ----------
    processes: list
       list of SharedMemoryProcess where each SharedMemoryProcess is created by
       calling shared_memory_process().
    connections: list
       list of 4-tuples where each tuple is:
       (0) sending SharedMemoryProcess,
       (1) name of out_stream of the sender
       (2) receiving SharedMemoryProcess
       (3) name of in_stream of the receiver
    name: str, optional
       The name of the Multiprocess. The default is
       'unnamed_Multiprocess'. 
    

    """
    def __init__(self, processes, connections,
                 name='unnamed_Multiprocess'): 
        self.processes = processes
        self.connections = connections
        self.check_parameters()
        self.connect_streams()
        for process in processes:
            process.create_process()

    def check_parameters(self):
        assert isinstance(self.processes, list)
        for proc in self.processes:
            assert isinstance(proc, SharedMemoryProcess)
        assert isinstance(self.connections, list)
        for connection in self.connections:
            assert (isinstance(connection, list) or
                    isinstance(connection, tuple))
            assert len(connection) == 4
            sender, sending_stream_name, \
              receiver, receiving_stream_name = connection
            assert sender in self.processes
            assert receiver in self.processes
            assert sending_stream_name in sender.out_stream_names
            assert receiving_stream_name in receiver.in_stream_names
        
    def start(self):
        for process in self.processes:
            process.start()
    def join(self):
        for process in self.processes:
            process.join()
    def run(self):
        self.start()
        self.join()
    def connect_streams(self):
        """
        Insert connections into the dict out_to_in of each
        sending SharedMemoryProcess.

        """
        for connection in self.connections:
            sender, sending_stream_name, \
              receiver, receiving_stream_name = connection
            sender.out_to_in[sending_stream_name].append(
                (receiving_stream_name, receiver))

def run_multiprocess(processes, connections=[]):
    mp = Multiprocess(processes, connections)
    mp.start()
    mp.join()

#--------------------------------------------------------------
# Functions to simplify testing of single process applications.
#--------------------------------------------------------------
def single_process_single_source(
        source_func, compute_func):
    assert callable(source_func)
    assert callable(compute_func)
    def g(in_streams, out_streams):
        return compute_func(in_streams[0])
    proc = shared_memory_process(
        compute_func=g, in_stream_names=['in'], out_stream_names=[],
        connect_sources=[['in', source_func]]
        )
    vm = Multiprocess(processes=[proc], connections=[])
    vm.run()

def single_process_multiple_sources(list_source_func, compute_func):
    in_stream_names = [
        'in_'+ str(i) for i in range(len(list_source_func))]
    connect_sources = [['in_' + str(i), list_source_func[i]]
                       for i in range(len(list_source_func))]
    out_stream_names=[]
    def f(in_streams, out_streams):
        return compute_func(in_streams)

    proc = shared_memory_process(
        f, in_stream_names, out_stream_names,
        connect_sources)
    vm = Multiprocess(processes=[proc], connections=[])
    vm.run()

    
    
    
