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
       the encapsulated function.
    
    Methods
    -------
    * attach_stream: specifies that a sending stream on this process
    is the same as a receiving stream in some other process.
    * connect_processor: connects all the attached output streams of
    func in this process to input streams of functions in other processes
    * target_of_connect_process: the target function for make process. This
    function calls the encapsulated function func, and starts threads.
    * connect_process: makes a multiprocessing.Process with the target:
    target_of_connect_process
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
