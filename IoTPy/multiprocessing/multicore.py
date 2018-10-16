
"""
This module defines a Class, StreamProcess, for making a multiprocess
program that runs on a multicore (shared-memory) computer.

For distributed computing with multiple computers with different IP 
addresses, see the module DistributedComputing.py.

"""
import multiprocessing
from collections import defaultdict

import sys
import os
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

def single_process_single_source(source_func, compute_func):
    """
    Create a single process with a single source. The source
    is defined by source_func. The process carries out a
    computation on the data generated by the source; this
    computation is specified by compute_func. This computation
    has no output streams. Typical output operations are
    writing to a file.

    Parameters
    ----------
    source_func: source_function from agent_types/source
    compute_func: network of agents (possibly single agent)
        This network of agents has a single input stream and
        no output stream.

    Notes
    -----
    compute_func in single_process_single_source operates on
    a single input stream, whereas compute_func in
    single_process_multiple_sources operates on a list of
    input streams. The role of function f (below) is merely
    to map a singleton list of streams to a single stream.

    """
    def f(s):
        compute_func(s[0])
    single_process_multiple_sources(
        list_source_func=[source_func], compute_func=f)



def single_process_multiple_sources(list_source_func, compute_func):
    """
    Create a single process with multiple sources specified
    by list_source_func. The process carries out a
    computation on the data generated by the sources; this
    computation is specified by compute_func.
    compute_func has a list of input streams and no output stream.
    The output is typically writing to a file.
    For computations with output streams see run_multiprocess().

    Parameters
    ----------
    list_source_func: list
       elements of the list are source_function from
       agent_types/source
    compute_func: network of agents (possibly single agent)
       The j-th input stream of compute_func is fed by the
       j-th source in list_source_func

    Notes
    -----
    1. Stream.scheduler.name_to_stream is a dict that
       associates a stream name with a stream. For each
       source_func in list_source_func, the code
       creates a stream with a unique stream name which
       is the output stream for the source_func.
    2. The function creates a single stream process, proc_0,
       starts and joins it.

    """
    def target_of_StreamProcess():
        # list_source_streams is the list of streams
        # generated by the sources.
        list_source_streams = []
        # list_thread_objects is the list of thread_objects
        # created by source_func.
        list_thread_objects = []
        for i in range(len(list_source_func)):
            # Create an output stream for each source_func
            # and make a unique name for the stream, and
            # update the dict Stream.scheduler.name_to_stream
            # with this name.
            stream_name = '_source_' + str(i)
            stream = Stream(stream_name)
            Stream.scheduler.name_to_stream[stream_name] = stream
            list_source_streams.append(stream)
            # Apply each source_func to its output stream and
            # put the returned thread object into the list.
            f = list_source_func[i]
            list_thread_objects.append(f(stream))

        # Create the network of agents that operates on the source
        # streams
        compute_func(list_source_streams)

        # returns (1) list of sources i.e. list_thread_objects,
        # (2) list of input streams i.e. list_source_streams, and
        # (3) list of output streams i.e. []
        return list_thread_objects, list_source_streams, []
    
    proc0 = StreamProcess(
        func=target_of_StreamProcess,
        name='single process multiple sources')
    proc0.connect_process()
    proc0.start()
    proc0.join()

def make_process(
        list_source_func, compute_func,
        in_stream_names, out_stream_names,
        process_name='no_name'):
    def f():
        list_source_streams = []
        list_thread_objects = []
        for i in range(len(list_source_func)):
            stream_name = '_source_' + str(i)
            stream = Stream(stream_name)
            Stream.scheduler.name_to_stream[stream_name] = stream
            list_source_streams.append(stream)
            f = list_source_func[i]
            list_thread_objects.append(f(stream))
        in_streams = list_source_streams
        for in_stream_name in in_stream_names:
            in_streams.append(Stream(in_stream_name))
        out_streams = []
        for out_stream_name in out_stream_names:
            out_streams.append(Stream(out_stream_name))
        for in_stream in in_streams:
            Stream.scheduler.name_to_stream[in_stream.name] = in_stream
        for out_stream in out_streams:
            Stream.scheduler.name_to_stream[out_stream.name] = out_stream
        compute_func(in_streams, out_streams)
        return (list_thread_objects, in_streams, out_streams)
    return StreamProcess(func=f, name=process_name)


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
    
def run_multiprocess(processes, connections):
    check_processes(processes)
    check_connections(connections)
    connect_streams(processes, connections)
    for process in processes:
        process.connect_process()
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    
