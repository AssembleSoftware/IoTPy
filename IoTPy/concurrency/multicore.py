"""
This module makes processes for a multicore application.
It uses multiprocessing.Array to enable multiple processes to
share access to streams efficiently.

TO DO: remove source_keyword_args because you can have multiple
sources.
"""
import sys
# Check whether the Python version is 2.x or 3.x
# If it is 2.x import Queue. If 3.x then import queue.
is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue

import multiprocessing
# multiprocessing.Array provides shared memory that can
# be shared across processes.
import threading
import numpy as np
import time
import ctypes

from ..agent_types.sink import sink_list, sink_element
# sink, op are in ../agent_types.

from ..core.compute_engine import ComputeEngine
from ..core.stream import Stream, StreamArray
from ..core.system_parameters import  BUFFER_SIZE, MAX_NUM_SOURCES, MAX_NUM_PROCESSES
# compute_engine, stream and system_parameters are in ../core.
from .utils import check_processes_connections_format, check_connections_validity
# utils is in current folder.

multiprocessing_type_to_np_type = {
    'i': 'int',
    'f': 'float',
    'd': 'double',
    ctypes.c_wchar: '<U5'
    }


#-----------------------------------------------------------------------
class MulticoreProcess(object):
    """
    MulticoreProcess creates a single process in a multicore application.
    The parameters of this class describe ALL the processes in the
    multicore application. Each process is created from the specification
    of the collection of all processes.

    Parameters
    ----------
    multicore_specification: 2-tuple or 2-element list
    [Streams, Processes]
    
    Streams is a list of 2-tuples:
        (stream_name, stream,type)
        stream_type is a single character: 'i', 'f', 'd'
        for int, float, double, ... etc.
        This is a list of all the streams that connect
        processes.
        
    Processes is a list of process specifications, with
    one process specification for each process in the
    multicore application.
    Each process specification has the following keys:
     'name'
     'agent'
     'inputs'
     'outputs'
     'keyword_args'
     'sources'
     'output_queues'
    The keyword 'agent' is required. The other keywords
    of process can be omitted in which case a default is used.

    Notes:
    -----
      The attributes described below are for a SINGLE
      process. By contrast, the multicore specification is for
      all processes.

      Associated with each process is a single agent. This
      agent has input and output streams. The process may
      also have source threads and source streams in addition
      to the agent's input and output streams.
    
    Attributes
    ----------
    inputs : list
       inputs is a list of pairs where each pair is
       (in_stream name, in_stream_type). in_stream_type is a
       str defined in multiprocessing.Array. For example 'i' stands
       for int.
       Example of inputs = [('in', 'i')]
       which says that the agent has a single input stream
       called 'in' which is of type int.
       Default: empty list
       Inputs describes the input streams of the agent associated
       with this process.
    outputs : list
       Similar to inputs.
       Example of outputs = [('out', 'i')]
       which says that the compute function (agent) has a
       single input stream called 'out' which is of type int.
       Default: empty list
       Outputs describes the output streams of the agent associated
       with this process.
    agent: function
       agent(in_streams=inputs, out_streams=outputs) creates
       an agent that reads the streams in inputs and extends
       the streams in outputs.
       The main thread of this process executes the code that
       runs this agent. This thread is started by calling.
       Stream.scheduler.start(). See IoTPy/IoTPy/core/ComputeEngine.py.
    keyword_args: dict
       The keys of this dict are the names of keyword arguments of the
       agent and the values are the corresponding keyword arguments.
       Example: {'ADDEND' :10} where ADDEND is the name of a keyword
       argument of agent, and this keyword argument has value 10.
       The arguments must be constants.
       Default: empty dict.
    sources: list
       list of 2-tuples: stream_name, stream_type
       An external thread is used to put data into the stream with the
       specified stream_name. stream_type is 'i', 'f', 'd',.. as before.
       stream_name is the name of a stream that is fed by a source.
       The stream is an output stream of the process but not necessarily
       an output stream of the agent. This source stream can be
       connected to input streams of the same or other processes.
    output_queues: list
       The list of queues into which this process puts output data.
       When the multicore computation terminates, a special message
       '_finished' is put in each output queue.
       Note: The agent may have arguments that are queues and that are
       not listed as ouput queues. Only output_queues will get the
       message '_finished' when computation terminates.
    out_to_in: dict
        The keys are names of output streams of this process, and the
        values are lists.
        out_to_in[out_stream_name] is a list of pairs:
                     (receiver_process_name, in_stream_name)
        where the out_stream called out_stream_name of this process
        is connected to the in_stream called in_stream_name in the
        receiver process called receiver_process_name.
        Example of self.out_to_in:
          {'out': [('aggregate_and_output_process', 'in')],
          'acceleration': [('get_source_data_and_compute_process', 'in')]
          }
        The output stream called 'out' of this process is connected to
        an input stream called 'in' of the process called
        'aggregate_and_output_process'.
        The output stream called 'acceleration' of this process is connected to
        an input stream called 'in' of the process called
        'get_source_data_and_compute_process'.
        Note that output streams of a process includes output streams
        of the agent associated with the process and source streams
        in the process.
    in_to_out: dict
       The keys are in_stream_names of this process and the values are
       pairs (out_process_name, out_stream_name).
       Example of in_to_out:
       {
         'in': ('get_source_data_and_compute_process', 'acceleration')
       }
       This process has an input stream called 'in' connected to an
       output stream called 'acceleration' in the process called
       'get_source_data_and_compute_process'
       The output stream may be an output of agent or an
       a source.
    stream_name_to_type: dict
       Key is a stream name and value is its type.

    """
    def __init__(self, spec, connect_streams, name):
        """
        Parameters
        ----------
        spec: dict
        connect_streams: list
        name: str

        spec is the specification of this process.
        An example of spec is:
        {'name': 'p1',
        'agent': <function test_1.<locals>.g at 0x119851620>,
        'inputs': ['y'],
        'args': [<multiprocessing.queues.Queue object at 0x10b4fcfd0>],
        'output_queues': [<multiprocessing.queues.Queue object at 0x10b4fcfd0>],
        'threads': [<Thread(Thread-1, initial)>]
        }

        An example of connect_streams is:
        [('p0', 'x', 'p0', 'x'), ('p0', 'y', 'p1', 'y')]
        The first 4-tuple of the list says that:
        output stream called 'x' of the process called 'p0' is connected
        to the input stream called 'x' of the process called 'p0'.
        The second 4-tuple says that:
        output stream called 'y' of the process called 'p0' is connected
        to the input stream called 'y' of the process called 'p1'

        The connection format is changed from connect_streams (which is a
        list) to self.connections (which is a dict). An example of
        self.connections is:
        {'p0': {'x': [('p0', 'x')], 'y': [('p1', 'y')]}}

        A key in self.connections is the name of a process, e.g., 'p0'.
        self.connections['p0'] is alsoa dict. The keys of this dict are names
        of output streams of this process (i.e. the process called 'p0'), and
        the values are lists of pairs identifying the receiving process and
        the receiving stream name. For example, the process called 'p0' has
        output streams called 'x' and 'y'. The output stream of 'p0' called 'x'
        of process 'p0' is connected to the input stream 'x' of process 'p0' because
        of 'x': [('p0', 'x')]. In this case, the output stream 'x' is a source
        stream in process 'p0'. The output stream called 'y' of process 'p0' is
        connected to the input stream 'y' of process 'p1'.

        STEPS
        -----
        Step 1: Get the lists of input and output streams of this process and
                check that the streams are connected.
        Step 2: Set default values --- empty dict or list --- for parameters.
        Step 3: Create out_to_buffer and the buffers associated with each
                output stream. These buffers are used to share data across
                processes.
        Step 4: Create the parameters of this process including main_lock used
                to control access to queues used for termination detection and
                out_to_q_and_in_stream_signal_names, in_queue....

        """
        self.spec = spec
        self.connect_streams = connect_streams
        self.connections = make_connections_from_connect_streams(connect_streams)
        self.name = name
        # ---------------------------------------------------------------------
        #  STEP 1. GET THE LISTS OF INPUT AND OUTPUT STREAMS OF THIS PROCESS.
        # ---------------------------------------------------------------------
        # The list of input streams of a process must be the
        # same as the list of input streams of the agent
        # associated with that process. The list of input
        # stream names are and types are specified in
        # self.spec['inputs'].
        # The output streams of a process the output streams of
        # the agent associated with the process and also the
        # source streams of the process.
        # self.in_stream_names_connected_to_out_streams is
        # the list of input stream names of the process.
        # self.out_stream_names_connected_to_in_streams is
        # the list of output stream names of the process.
        self.in_stream_names_connected_to_out_streams = []
        self.out_stream_names_connected_to_in_streams =[]
        self.get_stream_names_connected_to_streams()

        # GET INPUT STREAMS AND CHECK CONNECTEDNESS
        # inputs is a list of in_stream names and their types.
        # These are the inputs of the agent associated with
        # the process. It is the same as the inputs of the
        # process. Also, every input stream must be connected
        # to an output stream otherwise that input stream will
        # remain empty for ever.
        if 'inputs' in self.spec:
            self.inputs = self.spec['inputs']
        else:
            self.inputs = []
        assert set(self.in_stream_names_connected_to_out_streams) == \
          set([v[0] for v in self.inputs]), \
          "Process name = {0}. \n" \
          "Names of input streams = {1}. \n" \
          "Names of streams connected to outputs = {2}. \n" \
          "Names of input streams and streams connected to outputs must be same".format(
              self.name, [v[0] for v in self.inputs], self.in_stream_names_connected_to_out_streams)

        # GET OUTPUT STREAMS AND CHECK CONNECTEDNESS
        # outputs is a list of out_stream names and their types for
        # the agent associated with the process. It does not include
        # source streams of the process.
        if 'outputs' in self.spec:
            self.outputs = self.spec['outputs']
        else:
            self.outputs = []
        assert set(self.out_stream_names_connected_to_in_streams) >= \
          set([v[0] for v in self.outputs]), \
          "Output streams = {0}. Connections to input streams = {1}".format(
              self.outputs, self.out_stream_names_connected_to_in_streams)

        # ---------------------------------------------------------------------
        #  STEP 2: SET DEFAULT VALUES (EMPTY DICT OR LIST) FOR PARAMETERS.
        # ---------------------------------------------------------------------
        self.agent = self.spec['agent']
        # self.agent is the function with parameters in_streams, out_streams.
        # This function creates the network of agents.
        # self.agent is not a regular agent; it is a function that makes agents.

        # self.keyword_args
        if 'keyword_args' in self.spec:
            self.keyword_args = self.spec['keyword_args']
        else:
            self.keyword_args = {}
        
        self.source_keyword_args = {}

        # self.args
        if 'args' in self.spec:
            self.args = self.spec['args']
        else:
            self.args = []

        # self.sources
        if 'sources' in self.spec:
            self.sources = self.spec['sources']
        else:
            self.sources = []
            self.spec['sources'] = self.sources

        # self.source_functions
        if 'source_functions' in self.spec:
            self.source_functions = self.spec['source_functions']
        else:
            self.source_functions = []

        # self.threads
        if 'threads' in self.spec:
            self.threads = self.spec['threads']
        else:
            self.threads = []

        # self.output_queues
        if 'output_queues' in self.spec:
            self.output_queues = self.spec['output_queues']
        else:
            self.output_queues = []
            self.spec['output_queues'] = self.output_queues

        # self.out_to_in
        if self.name in self.connections.keys():
            self.out_to_in = self.connections[self.name]
        else:
            self.out_to_in = []

        # self.stream_name_to_type
        self.stream_name_to_type = {}
        for stream_name, stream_type in self.outputs + self.inputs + self.sources:
            if not stream_name in self.stream_name_to_type.keys():
                self.stream_name_to_type[stream_name] = stream_type
        
        # ---------------------------------------------------------------------
        #  STEP 3: CREATE OUT_TO_BUFFER AND BUFFERS FOR EACH OUTPUT STREAM.
        # ---------------------------------------------------------------------
        # out_to_buffer[out_stream_name] is (buffer, buffer_ptr) which is
        # the buffer to which this out_stream_name or source_name is connected.
        # Next, compute out_to_buffer.
        self.out_to_buffer = {}
        # create a buffer for each out_stream and each source of this process.
        # 1. Create a buffer for each out_stream of this process.
        # self.out_to_buffer[out_stream_name] becomes the buffer for 
        # the stream called out_stream_name.
        # self.outputs is a list of pairs:
        #                   ( out_stream_name, out_stream_type)
        for out_stream_name, out_stream_type in self.outputs:
            if out_stream_type != 'x':
                buffer = multiprocessing.Array(out_stream_type, BUFFER_SIZE)
                # buffer_ptr is an integer with initial value of 0.
                buffer_ptr = multiprocessing.Value('i', 0)
            else:
                # out_stream_type of 'x' means a type that is not allowed
                # in multiprocessing.Array. So, a buffer of this type cannot
                # be used to share data across processors. Such a buffer can
                # only be used in the process in which it is defined.
                buffer = [0]*BUFFER_SIZE
                # buffer_ptr is an integer with initial value of 0.
                buffer_ptr = multiprocessing.Value('i', 0)
                    
            self.out_to_buffer[out_stream_name] =  (buffer, buffer_ptr)
                
        # 2. Create a buffer for each source of this process.
        # self.out_to_buffer[source_name] is the buffer for the source called
        # source_name
        for source_name, source_type in self.sources:
            #source_type  = source_type_and_func['type']
            if source_type != 'x':
                # This source generates data of a type accepted by
                # multiprocessing.Array
                buffer = multiprocessing.Array(source_type, BUFFER_SIZE)
                # buffer_ptr is a shared integer with initial value of 0.
                buffer_ptr = multiprocessing.Value('i', 0)
            else:
                # This source feeds a stream inside the same process in
                # which the source thread runs. This source does not feed
                # any other process. So, it does not need to use
                # multiprocessing.Array.
                # This source can generate arbitrary Python objects such as
                # tuples.
                # Note that if source_type == 'x' then buffer is a list and
                # buffer_ptr is an integer.
                buffer = [0]*BUFFER_SIZE
                # buffer_ptr is an integer with initial value of 0.
                buffer_ptr = 0
            self.out_to_buffer[source_name] =  (buffer, buffer_ptr)

        # ---------------------------------------------------------------------
        #  STEP 4: MAKE PARAMETERS OF THE PROCESS
        # ---------------------------------------------------------------------
        # threads is a list of thread targets.
        # out_to_q_and_in_stream_signal_names[out_stream_name] is 
        #    a list of pairs (q, in_stream_signal_name).
        #    where q is the queue of the receiving process and
        #    in_stream_signal_name is 's_signal_' where the
        #    in_stream is 's'.
        #    Each process has a unique queue in which it gets messages
        #    for its input streams. q is that unique queue for the
        #    receiver process.
        #    The input stream 's_signal_' gets messages to indicate
        #    that data is available in the buffer for stream 's'.
        # make_out_to_q_and_in_stream_signal_names() is the function
        #    that fills in out_to_q_and_in_stream_signal_names.
        self.out_to_q_and_in_stream_signal_names = {}
        # in_queue is the input queue of this process. Messages for
        #    the process' input streams are put in in_queue.
        self.in_queue = multiprocessing.Queue()
        # process is initially None and is created later by calling
        #    the function make_process() with parameters
        #    process specification and connections.
        self.process = None
        # in_to_out[in_stream_name] is a pair:
        #    (sender_process_name, out_stream_name)
        #    in_to_out is filled in by the function
        #    make_in_to_out()
        self.in_to_out = {}
        # in_to_buffer[in_stream_name] is a buffer. Data in this buffer
        #    is copied into the input stream called in_stream_name.
        #    in_to_buffer is computed by the function make_in_to_out().
        self.in_to_buffer = {}
        # The following parameters are set by calling:
        #    multicore(process_specs, connect_streams)
        self.process_ids = {}
        self.source_ids = {}
        self.source_status = {}
        self.queue_status = {}
        self.all_process_specs = {}
        self.all_procs = {}
        # main_lock is the lock acquired to do operations on
        #   in_queue of processes. These operations check whether the
        #   input queues of all the processes are empty.
        #   Termination of the multiprocess computation is detected
        #   when all processes have empty input queues and all sources
        #   have finished.
        self.main_lock = None
        return
    #-----------------------------------------------------------------
    # FINISHED __init__()
    #-----------------------------------------------------------------


    def make_in_to_out(self, procs, connections):
        """
        Computes self.in_to_out and self.in_to_buffer
        self.in_to_buffer[in_stream_name] is the buffer that feeds
            the input stream called in_stream_name.
        self.in_to_out[in_stream_name] is the pair
            (out_process_name, out_stream_name) which identifies
            the output process and output stream connected to the
            input stream called in_stream_name.

        Parameters
        ----------
        procs: dict
           procs[proc_name] is an instance of the MulticoreProcess class
           procs has a key proc_name (the name of a process) for every
           process in the multicore application.
        connections: dict
           connections is described in __init__()

        """
        for out_process_name, process_connections in connections.items():
            for out_stream_name, stream_connections in process_connections.items():
                for in_process_name, in_stream_name in stream_connections:
                    if in_process_name == self.name:
                        # The out_stream called out_stream_name in the
                        # process called out_process_name is connected
                        # to the in_stream called in_stream_name in THIS
                        # process.
                        self.in_to_out[in_stream_name] = (
                            out_process_name, out_stream_name)
                        # Get the sending process
                        out_process = procs[out_process_name]
                        # Get the output buffer in which data from the sending
                        # stream is placed.
                        out_buffer = out_process.out_to_buffer[out_stream_name]
                        self.in_to_buffer[in_stream_name] = out_buffer
        return

    def make_out_to_q_and_in_stream_signal_names(self, procs):
        """
        Parameters
        ----------
        procs: dict
           procs[proc_name] is an instance of the MulticoreProcess class
           procs has a key proc_name (the name of a process) for every
           process in the multicore application.

        Notes
        -----
        out_to_q_and_in_stream_signal_names is a dict where
           out_to_q_and_in_stream_signal_names[out_stream_name] is a list
           of pairs (receiver_proc.in_queue, in_stream_name + '_signal_')
           where receiver_proc.in_queue is the input queue of a process that
           receives the output stream called out_stream_name and
           's_signal_' is the input stream of the receiver process that
           receives messages (called signals) that tell it that the stream 's'
           buffer has data waiting for it to be ingested.
        
        """
        # Create q_and_in_stream_signal_names for each out_stream and
        # each source of this process.
        # 1. Create q_and_in_stream_signal_names for each out_stream of this process.
        for out_stream_name, out_stream_type in self.outputs:
            # Skip output streams that are not connected to input streams.
            if not out_stream_name in self.out_stream_names_connected_to_in_streams:
                continue

            # self.out_to_q_and_in_stream_signal_names[out_stream_name] is
            # q_and_in_stream_signal_names which is a list of pairs:
            #    (q, in_stream_signal_name).
            # where q is the queue of the receiving process and
            # in_stream_signal_name is 's_signal_' if the in_stream is
            # 's'. These are the queues and in_stream_signals of the
            # input streams connected to this out_stream.
            self.out_to_q_and_in_stream_signal_names[out_stream_name] = []
            # receivers is a list of pairs (process name, in_stream name)
            receivers = self.out_to_in[out_stream_name]
            for receiver_proc_name, in_stream_name in receivers:
                receiver_proc = procs[receiver_proc_name]
                if out_stream_type in multiprocessing_type_to_np_type.keys():
                    # CASE 1 in create_in_stream_signals_for_C_datatypes().
                    self.out_to_q_and_in_stream_signal_names[out_stream_name].append(
                        (receiver_proc.in_queue, in_stream_name + '_signal_'))
                else:
                    # CASE 2.
                    # In this case 'in_stream_name' is used in place of
                    # 'in_stream_name_signal' because there is no signal stream in
                    # this case.
                    self.out_to_q_and_in_stream_signal_names[out_stream_name].append(
                        (receiver_proc.in_queue, in_stream_name))

        # 2. Create q_and_in_stream_signal_names for each source of this process.
        # self.out_to_q_and_in_stream_signal_names[name] is the
        # q_and_in_stream_signal_names for the connections to the source called
        # name
        for source_name, source_type in self.sources:
            self.out_to_q_and_in_stream_signal_names[source_name] = []
            # receivers is a list of pairs (process name, in_stream name)
            # self.out_to_in is a dict.
            # self.out_to_in[source_name] is the list of receivers for this source.
            assert source_name in self.out_to_in.keys(), \
              '{0} must be in list of inputs'.format(source_name)
            receivers = self.out_to_in[source_name]
            for receiver_proc_name, in_stream_name in receivers:
                # receiver_proc is the MulticoreProcess with the name, receiver_proc_name.
                receiver_proc = procs[receiver_proc_name]
                # (1) Associate the in_queue of the receiver process with the
                #     source called source_name.
                # (2) The messages about new data in the source called source_name
                #     are sent to the stream called in_stream_name + '_signal_'
                #     in the receiver process.

                if source_type in multiprocessing_type_to_np_type.keys():
                    # CASE 1.
                    self.out_to_q_and_in_stream_signal_names[source_name].append(
                        (receiver_proc.in_queue, in_stream_name + '_signal_'))
                else:
                    # CASE 2.
                    self.out_to_q_and_in_stream_signal_names[source_name].append(
                        (receiver_proc.in_queue, in_stream_name))
        return

    def create_in_streams_of_agent(self):
        # Create the in_streams of agent from their names:
        # and create compute the dict, name_to_stream.
        # in_streams is the list of in_stream of this process.
        # We have two cases:
        # (1) The in_stream type is a C_datatype such as 'i' or 'f'
        # (2) The in_stream_type is unspecified.
        # In the former case create a StreamArray and in the latter
        # case create a Stream.
        self.in_streams = []
        # name_to_stream is a dict where the key is the name of an
        # input or output stream and the value is the stream itself.
        self.name_to_stream = {}
        for in_stream_name, in_stream_type in self.inputs:
            if in_stream_type in multiprocessing_type_to_np_type.keys():
                # CASE 1.
                # See CASE 1 in create_in_stream_signals_for_C_datatypes().
                # The in_stream is a StreamArray.
                in_stream = StreamArray(
                    name=in_stream_name,
                    dtype=multiprocessing_type_to_np_type[in_stream_type])
            else:
                # CASE 2.
                # The in_stream is a Stream and not a StreamArray.
                in_stream = Stream(name=in_stream_name)
            self.in_streams.append(in_stream)
            self.name_to_stream[in_stream_name] = in_stream

    def get_stream_names_connected_to_streams(self):
        for four_tuple in self.connect_streams:
            (sender_process_name, out_stream_name,
             receiver_process_name, in_stream_name) = four_tuple
            if receiver_process_name == self.name:
                self.in_stream_names_connected_to_out_streams.append(in_stream_name)
            if sender_process_name == self.name:
                self.out_stream_names_connected_to_in_streams.append(out_stream_name)
            
    def create_in_stream_signals_for_C_datatypes(self):
        # in_stream_signals is a list of input streams, with
        # one in_stream_signal for each in_stream. We have
        # two cases:
        # (1) The data type is a C_datatype such as 'i' or 'f'
        #     or a NumPy data type such as dtype='int'.
        # (2) The data type is 'x' for unspecified.
        #
        # CASE 1.
        # in_stream_signal[j] is the stream that tells
        # this process that it has data to be read into
        # in_stream[j].
        # The name of an in_stream_signal associated with an in_stream
        # called 's' is 's_signal_'.
        # Data is copied to all input streams connected to the stream
        # called stream_name by executing:
        #       self.copy_stream(data, stream_name).
        # See step 2 of create_agents_to_copy_each_out_stream_to_in_streams.
        #
        # CASE 2.
        # in_stream_signal[j] is the same as in_stream[j].
        # Data is copied to all input streams connected to the stream
        # called stream_name by executing:
        #       self.data_to_receiver_queue(data, stream_name)
        
        self.in_stream_signals = []
        for in_stream_name, in_stream_type in self.inputs:
            # Skip input streams that are not connected to output streams.
            if not in_stream_name in self.in_stream_names_connected_to_out_streams:
                continue

            if in_stream_type in multiprocessing_type_to_np_type.keys():
                # CASE 1.
                # Create a stream, in_stream_signal, for each in_stream.
                # We put information in in_stream_signal to tell the
                # receiving process to copy data from a shared buffer into
                # in_stream.
                in_stream_signal_name = in_stream_name + '_signal_'
                in_stream_signal = Stream(name=in_stream_signal_name)
                self.in_stream_signals.append(in_stream_signal)
                # name_to_stream is a dict where
                # key is stream-name; value is the stream with that name
                self.name_to_stream[in_stream_signal_name] = in_stream_signal
            else:
                # CASE 2.
                # Do not create a new stream for in_stream signals for this
                # case because data is put directly into the receiver process'
                # queue. We do not copy data from a shared buffer.
                in_stream_signal_name = in_stream_name
                

    def create_out_streams_for_agent(self):
        # Create the out_streams of agent from their names:
        # and create compute the dict, name_to_stream.
        # out_streams is the list of out_stream of this process.
        # We have two cases:
        # (1) The out_stream type is a C_datatype such as 'i' or 'f'
        # (2) The out_stream_type is unspecified.
        # In the former case create a StreamArray and in the latter
        # case create a Stream.
        self.out_streams = []
        for out_stream_name, out_stream_type in self.outputs:
            if out_stream_type in multiprocessing_type_to_np_type.keys():
                # CASE 1.
                # See CASE 1 in create_in_stream_signals_for_C_datatypes().
                # The out_stream is a StreamArray.
                out_stream = StreamArray(
                    name=out_stream_name,
                    dtype=multiprocessing_type_to_np_type[out_stream_type])
            else:
                # CASE 2.
                # The out_stream is a Stream and not a StreamArray.
                out_stream = Stream(name=out_stream_name)
            self.out_streams.append(out_stream)
            self.name_to_stream[out_stream_name] = out_stream

    def create_agents_to_copy_each_out_stream_to_in_streams(self):
        # Note: (1) Create an agent for each out_stream and (2) create
        # an agent for each source. These agents copy the elements
        # in each out_stream and each source into the in_streams to
        # which it is connected.
        # See copy_stream(data, stream_name).
        for out_stream_name, out_stream_type in self.outputs: 
            if not out_stream_name in self.out_stream_names_connected_to_in_streams:
                # If this output stream is not connected to any input stream then
                # skip this step.
                continue
            # Step 1 Get the out_stream called out_stream_name.
            out_stream = self.name_to_stream[out_stream_name]
            # STEP 2: Make agent that copies out_stream to the in_streams to
            # which it is connected.
            # stream_name is a keyword argument of copy_stream().
            # CASE 1. 
            # The stream type is a C_datatype such as 'i' or 'f'.
            # See create_in_stream_signals_for_C_datatypes().
            # CASE 2.
            # The stream type is unspecified.
            if out_stream_type in multiprocessing_type_to_np_type.keys():
                # CASE 1:
                sink_list(self.copy_stream, out_stream,
                          stream_name=out_stream_name,
                          name='copy_stream. stream is:  '+  out_stream_name)
            else:
                # CASE 2:
                sink_list(self.data_to_receiver_queue, out_stream,
                          stream_name=out_stream_name,
                          name='data_to_receiver_queue. stream is:  '+  out_stream_name)
                          

    def create_agents_to_copy_buffers_to_in_streams(self):
        # For each in_stream of this process, create an agent that
        # copies data from the input buffer of this in_stream into
        # the in_stream, ONLY IF this stream type is a
        # C_datatype such as 'i' or 'f'.
        # No buffers are created for other stream types.
        #
        # This agent subscribes to the in_stream_signal associated
        # with this in_stream. When in_stream_signal gets a message
        # (start, end) this agent copies the buffer segment between
        # start and end into the in_stream.
        # copy_buffer_segment() is the function executed by the agent
        # when a new message arrives. This function extends out_stream
        # with the segment of the buffer specified by the message.
        for in_stream_name, in_stream_type in self.inputs:
            if not in_stream_name in self.in_stream_names_connected_to_out_streams:
                continue
            if not in_stream_type in multiprocessing_type_to_np_type.keys():
                continue
            in_stream_signal_name = in_stream_name + '_signal_'
            # Get the in_stream_signal stream from its name.
            in_stream_signal = self.name_to_stream[in_stream_signal_name]
            # Get the in_stream from its name
            in_stream = self.name_to_stream[in_stream_name]
            # Get the buffer that feeds this in_stream.
            buffer, buffer_ptr = self.in_to_buffer[in_stream_name]
            # Create agents
            sink_element(
                func=copy_buffer_segment,
                in_stream=in_stream_signal,
                out_stream=in_stream,
                buffer=buffer, in_stream_type=in_stream_type,
                name='copy_buffer_segment: in_stream is ' + in_stream.name)
        
    def create_source_threads(self):
        """
        threads is a list of thread targets.

        """
        self.source_threads = []
        for source_function in self.source_functions:
            self.source_threads.append(
                #threading.Thread(target=source_function, args=(self,)))
                threading.Thread(target=source_function, args=()))


    #---------------------------------------------------------------------
    # MAKE THE PROCESS.
    #---------------------------------------------------------------------
    def make_process(self):
        def target():
            """
            This is the target function of this process. This function has the
            following steps:
            1. Create in_streams of the this process, i.e., the in_streams of
               the agent of the process.
            2. Create in_stream_signals, with an in_stream_signal corresponding
               to each in_stream.
            3. Create out_streams of this process, i.e. out_streams of the
               agent of this process.
            4. Create the computational agent (agent) of this process.
            5. For each out_stream of agent, create an agent to copy the
               out_stream to its buffer, and then copy the buffer to each
               in_stream to which it is connected.
            6. For each in_stream of agent, create an agent to copy its
               input buffer into the in_stream.
            7. Create the scheduler for this process. Starting the scheduler
               starts the thread that executes agent for this agent.
            8. Create the source threads for each source in this process. The
               source_thread gets data from a source, puts the data into a
               buffer, and then copies the buffer to each in_queue to which the
               source is connected.
            9. Start the scheduler and source threads.
            10. Join the scheduler and source threads.
               
            """
            # 1. Create input streams of this process.
            self.create_in_streams_of_agent()
            # 2. Create input signal streams corresponding to input streams.
            self.create_in_stream_signals_for_C_datatypes()
            # 3. Create output streams of this process.
            self.create_out_streams_for_agent()
            # 4. For each out_stream and each source, create an agent to
            #    copy data from the out_stream or source to all the
            #    in_streams to which it is connected.
            self.create_agents_to_copy_each_out_stream_to_in_streams()
            self.create_agents_to_copy_buffers_to_in_streams()

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

            # CREATE THE COMPUTE FUNCTION FOR THIS PROCESS.
            # self.agent is a function that creates a network of agents.
            self.agent(
                self.in_streams, self.out_streams,
                *self.args, **self.keyword_args)
            
            self.create_source_threads()

            # START SOURCE THREADS AND START SCHEDULER.
            # Starting the scheduler starts a thread --- the main thread --- of this
            # process. The scheduler thread gets a ready agent from the in_queue of
            # this process and then executes the next step of the agent.
            Stream.scheduler.start()
            for thread in self.threads: thread.start()
            for thread in self.source_threads: thread.start()

            # JOIN SOURCE THREADS AND JOIN SCHEDULER.
            for thread in self.source_threads: thread.join()
            Stream.scheduler.join()
            # Put '_finished' on each of the output queues so that threads getting
            # messages from these output queues can terminate upon getting a
            # '_finished' message instead of hanging.
            for output_queue in self.output_queues:
                output_queue.put('_finished')
            for thread in self.threads: thread.join()
            return

        # Create the process.
        self.process = multiprocessing.Process(target=target)

    #---------------------------------------------------------------------
    # COPY DATA FROM A BUFFER INTO A STREAM.
    # See CASE 1 in create_in_stream_signals_for_C_datatypes().
    #---------------------------------------------------------------------
    def copy_stream(self, data, stream_name):
        """
        This function extends a source stream or output stream,
        called stream_name, with data.

        Parameters
        ----------
          data: list
            the sequence of values that extend the stream with name
            stream_name.
          stream_name: str
            The name of the stream. This stream is a source stream or
            an output stream of this process.
        Returns
        -------
           None
        Notes
        -----
        This function takes the following steps:
        STEP 1: Get objects connected to the stream with this name, stream_name.
                These objects are (1) the buffer into which data is placed and
                (2) the list of pairs:
                (receiving process queue, receiving input stream signal name).
        STEP 2: Copy data into the circular buffer which is the output buffer for
                the stream called stream_name.
        STEP 3: Put a message into the queue of each receiving process that
                is connected to this stream_name.
                This message is put into an in_stream_signal of the receiving
                process.
        STEP 4: Update parameters to get ready for next call to this function.

        """
        # STEP 1: GET BUFFER, QUEUE, STREAMS CONNECTED TO THIS STREAM
        buffer, buffer_ptr = self.out_to_buffer[stream_name]
        # self.out_to_q_and_in_stream_signal_name is a dict where
        # self.out_to_q_and_in_stream_signal_names[stream_name] is
        # input queue of the receiver process and the list of in_stream
        # signal names in the receiver connected to the output stream
        # or source called stream_name.
        q_and_in_stream_signal_names = \
            self.out_to_q_and_in_stream_signal_names[stream_name]

        # STEP 2: COPY DATA INTO THE CIRCULAR BUFFER
        n = len(data)
        if n == 0:
            # Take no action if the message is empty.
            return None
        assert n < BUFFER_SIZE, \
          "The length of input data is greater than the buffer size"
        if isinstance(buffer_ptr, int):
            # This buffer is for a local stream.
            # This buffer is a list and not a multiprocessing.Array
            buffer_end_ptr = buffer_ptr + n
            buffer_current_ptr = buffer_ptr
        else:
            # This buffer is a multiprocessing.Array
            # buffer_ptr is  multiprocessing.Value
            buffer_end_ptr = buffer_ptr.value + n
            buffer_current_ptr = buffer_ptr.value
        if buffer_end_ptr < BUFFER_SIZE:
            # In this case, don't need to wrap around the
            # end of the buffer.
            buffer[buffer_current_ptr : buffer_end_ptr] = data
        else:
            # In this case, must wrap around the end of
            # the circular buffer.
            # remaining_space is the space remaining from
            # buffer_ptr to the end of the buffer.
            remaining_space = BUFFER_SIZE - buffer_end_ptr
            # Copy remaining_space elements of the list
            # to fill up the buffer.
            buffer[buffer_current_ptr:] =  data[:remaining_space]
            # That leaves n-remaining_space elements of the
            # list that are yet to be copied into the buffer.
            # Copy the remaining elements of list into the
            # buffer starting from slot 0.
            buffer[:n-remaining_space] = data[remaining_space:]
            buffer_end_ptr = n-remaining_space
        
        # STEP 3: TELL THE RECEIVER PROCESSES THAT THEY HAVE NEW
        # DATA.
        # 1. Set the status of queues that will now get data to
        # 'not empty' or 1.
        # 2. Put a message into the queue of each process that
        # receives a copy of data.

        # Always acquire lock for operations on queue_status or
        # source_status
        self.main_lock.acquire()
        # Step 3.1: Set queue status to "not empty" for queues that
        #         receive this message.
        for receiver in self.out_to_in[stream_name]:
            # The output stream called stream_name is connected to the
            # input stream called in_stream_name in the receiving
            # process called receiver_proc_name.
            receiver_proc_name, in_stream_name = receiver
            receiver_process_id = self.process_ids[receiver_proc_name]
            # queues status is 1 for not empty, 0 for empty.
            self.queue_status[receiver_process_id] = 1
        # Step 3.2: Send a message to the in_stream signal corresponding
        #           to each in_stream saying that new data is available
        #           in the buffer between pointers:
        #             (buffer_ptr.value, buffer_end_ptr)
        for q, in_stream_signal_name in q_and_in_stream_signal_names:
            q.put((in_stream_signal_name, (buffer_current_ptr, buffer_end_ptr)))
        self.main_lock.release()

        # STEP 4: UPDATE BUFFER_PTR TO GET READY FOR NEXT INPUT.
        if isinstance(buffer_ptr, int):
            buffer_ptr = buffer_end_ptr
        else:
            buffer_ptr.value = buffer_end_ptr
        return None

    #---------------------------------------------------------------------
    # COPY DATA FROM ONE STREAM INTO THE QUEUE OF A RECEIVER PROCESS.
    # See CASE 2 in create_in_stream_signals_for_C_datatypes().
    #---------------------------------------------------------------------
    def data_to_receiver_queue(self, data, stream_name):
        """
        This function extends a source stream or output stream,
        called stream_name, with data.

        Parameters
        ----------
          data: list
            the sequence of values that extend the stream with name
            stream_name.
          stream_name: str
            The name of the stream. This stream is a source stream or
            an output stream of this process.
        Returns
        -------
           None
        Notes
        -----

        """
        # See step 1 of copy_stream().
        q_and_in_stream_signal_names = \
            self.out_to_q_and_in_stream_signal_names[stream_name]

        # STEP 2: PUT DATA INTO THE RECEIVER PROCESS' QUEUE.
        # Same as step 3 of copy_stream().
        # 1. Set the status of queues that will now get data to
        # 'not empty' or 1.
        # 2. Put a message into the queue of each process that
        # receives a copy of data.

        # Always acquire lock for operations on queue_status or
        # source_status
        self.main_lock.acquire()
        # Step 2.1: Set queue status to "not empty" for queues that
        #         receive this message.
        for receiver in self.out_to_in[stream_name]:
            # The output stream called stream_name is connected to the
            # input stream called in_stream_name in the receiving
            # process called receiver_proc_name.
            receiver_proc_name, in_stream_name = receiver
            receiver_process_id = self.process_ids[receiver_proc_name]
            # queues status is 1 for not empty, 0 for empty.
            self.queue_status[receiver_process_id] = 1
        # Step 2.2: Put data into the queue of the receiving process.
        for q, in_stream_signal_name in q_and_in_stream_signal_names:
            q.put((in_stream_signal_name, data))
        self.main_lock.release()


    def broadcast(self, receiver_stream_name, msg):
        for process_name in self.all_process_specs.keys():
            this_process = self.all_procs[process_name]
            this_process.in_queue.put((receiver_stream_name, msg))

    def finished_source(self, stream_name):
        """
        Set the source_status of this stream to 0 to
        indicate that this source has terminated execution.

        Called by source thread functions.
        """
        this_source_id = self.source_ids[self.name][stream_name]
        self.source_status[this_source_id] = 0
        self.broadcast('source_finished', (self.name, stream_name))

#-----------------------------------------------------------------------    
# FINISHED class MulticoreProcess
#-----------------------------------------------------------------------

def make_spec_from_multicore_specification(multicore_specification):
    """
    Converts from the multicore specification format to the process
    specification format (called spec).

    """
    streams_spec, processes_spec = multicore_specification

    # --------------------------------------------------------
    # Set default values for unspecified keywords in
    # processes_spec.
    # Give names no_name_0, no_name_1, ... for unnamed processes.
    num_unnamed_processes = 0
    for p_spec in processes_spec:
        if 'name' in p_spec:
            process_name = p_spec['name']
        else:
            p_spec['name'] = 'no_name_' + str(num_unnamed_processes)
            num_unnamed_processes += 1
        assert 'agent' in p_spec.keys()
        if not 'inputs' in p_spec: p_spec['inputs'] = []
        if not 'outputs' in p_spec: p_spec['outputs'] = []
        if not 'args' in p_spec: p_spec['args'] = []
        if not 'args' in p_spec: p_spec['kwargs'] = {}
        if not 'sources' in p_spec: p_spec['sources'] = []
        if not 'queues' in p_spec: p_spec['queues'] = []
        if not 'state' in p_spec: p_spec['state'] = None

    # --------------------------------------------------------
    # Set up connect_streams which is a list of 4-tuples
    # Each 4-tuple is:
    #  1. name of sending process
    #  2. name of output stream
    #  3. name of receiving process
    #  4. name of input stream
    # The names out output and input stream will be the same.
    connect_streams = []
    for stream_name, stream_type in streams_spec:
        # ---------------------------------------------
        # Find which unique process outputs this stream.
        process_outputting_stream = None
        for p_spec in processes_spec:
            if stream_name in p_spec['outputs']:
                assert process_outputting_stream == None
                process_outputting_stream = p_spec['name']
            if stream_name in p_spec['sources']:
                assert process_outputting_stream == None, \
                  "stream name: {0} is in multiple outputs: {1} and in multiple sources: {2}".format(
                      stream_name, p_spec['outputs'], p_spec['sources'])
                process_outputting_stream = p_spec['name']
        assert process_outputting_stream != None, \
          "stream name: {0} is not an output or a source".format(stream_name)
        # ---------------------------------------------

        # ---------------------------------------------
        # Find which processes (possibly more than one) inputs
        # this stream.
        for p_spec in processes_spec:
            if stream_name in p_spec['inputs']:
                connect_streams.append(
                    (process_outputting_stream, stream_name,
                     p_spec['name'], stream_name))
        # ---------------------------------------------

    # --------------------------------------------------------
    # Insert stream type for each stream in a process's
    # 'inputs', 'outputs' and 'sources'.
    #
    # processes_spec is a list of process_spec.
    # Each process_spec is a dict with keywords 'inputs',
    # 'outputs', 'sources' and others.
    #
    # process_spec['inputs'] is initially a list of
    # stream names.
    # We now want to make process_spec['inputs'] a list of
    # pairs: (stream name, stream type).
    # We want to do the same for 'outputs' and 'sources.
    for p_spec in processes_spec:
        for category in ['inputs', 'outputs', 'sources']:
            # category_stream_names is the list of stream names for
            # each category.
            category_stream_names = p_spec[category]
            stream_names_and_types = []
            # For each stream name in each category, we find the
            # same stream name in streams_spec. Then append the
            # stream type to the stream name.
            for category_stream_name in category_stream_names:
                found_category_stream_name = False
                for stream_name, stream_type in streams_spec:
                    if category_stream_name == stream_name:
                        stream_names_and_types.append(
                            (stream_name, stream_type))
                        found_category_stream_name = True
                assert found_category_stream_name, \
                  " Category: {0}. \n "\
                  " Stream name: {2} is not in list of streams: {1}".format(
                      category, streams_spec, category_stream_name)
            # Replace the list of stream names by a list of pairs
            # (stream name, stream type)
            p_spec[category] = stream_names_and_types

    # Convert processes_spec from a list of dict to
    # a dict of dict with the keyword being the process name
    processes_dict = {}
    for p_spec in processes_spec:
        processes_dict[p_spec['name']] = p_spec
        # delete the 'name' key from the inner dict
        del processes_dict[p_spec['name']]['name']
    return connect_streams, processes_dict

#-------------------------------------------------------------------
def make_connections_from_connect_streams(connect_streams):
    """
    Converts from the format of connect_streams to the format of
    connections.
    connect_streams is a list of 4-tuples:
        sender_process, out_stream, receiver_process, in_stream
    connections is a dict where
        connections[sender_process] is a dict where
        connections[sender_process][out_stream_name] is a list of 2-tuples
        (receiver_process, in_stream_name)
    In this code, sender_process, out_stream, receiver_process, in_stream
    refer to the NAMES of the sender process, output stream receiver process
    and input stream.
    """
    connections = {}
    for four_tuple in connect_streams:
        sender_process, out_stream, receiver_process, in_stream = four_tuple
        if not sender_process in connections.keys():
            # Create dict and then enter the first tuple
            # (receiver_process, in_stream) into empty list.
            connections[sender_process] = {}
            connections[sender_process][out_stream] = \
              [(receiver_process, in_stream)]
        else:
            if not out_stream in connections[sender_process].keys():
                # Enter the first tuple (receiver_process, in_stream)
                # into an empty list.
                connections[sender_process][out_stream] = \
                  [(receiver_process, in_stream)]
            else:
                # Append tuple to the existing list.
                connections[sender_process][out_stream].append(
                    (receiver_process, in_stream))
    return connections
    
#-------------------------------------------------------------------
def copy_buffer_segment(message, out_stream, buffer, in_stream_type):
    """
    copy_buffer_segment() is the function executed by the agent
    when a new message arrives. A message is (start, end).
    This function extends out_stream with the segment of the buffer
    between start and end.
    """
    start, end = message
    if end == start:
        # Empty message. So take no action.
        return
    if end > start:
        # The end pointer hasn't crossed the termination of the
        # circular buffer. So, this segment is the linear
        # sequence from start to end.
        return_value = buffer[start:end]
    else:
        # The return value is read from the circular buffer
        # by going to the end of the buffer and adding values
        # from the beginning of the buffer.
        # The segment includes the values in the remaining_space
        # in the buffer concatenated with the values in the
        # buffer from cells 0 to end.
        remaining_space = BUFFER_SIZE - start
        segment_length = remaining_space + end
        # Set up an array with appropriate length to be filled in.
        return_value = multiprocessing.Array(in_stream_type, range(segment_length))
        # Copy the buffer from start to the termination of the buffer into
        # the first part of return_value.
        return_value[:remaining_space] = \
            multiprocessing.Array(in_stream_type, buffer[start:])
        # Roll over the end of the circular buffer. Copy the buffer
        # in cells 0 to end into the second part of remaining_space.
        return_value[remaining_space:] = \
            multiprocessing.Array(in_stream_type, buffer[:end])
            
    out_stream.extend(
        np.array(return_value,
                 dtype=multiprocessing_type_to_np_type[in_stream_type]))
    return
#-------------------------------------------------------------------

def copy_data_to_stream(data, proc, stream_name):
    """
    Another version of copy_stream. This can be more convenient
    in running applications of MulticoreProcess.

    Parameters
    ----------
    data: list or array
    proc: MulticoreProcess
    stream_name: str

    """
    proc.copy_stream(data, stream_name)

def finished_source(proc, stream_name):
    """
    Parameters
    ----------
    proc: MulticomputerProcess
    stream_name: str
    
    Set the source_status of this stream to 0 to
    indicate that this source has terminated execution.
    Used for detecting termination of a multicore
    application.

    Called by source thread functions.
    """
    # Each source stream has a unique id which is a
    # nonnegative integer. Get the id for the source with
    # this stream_name in the process called proc.name
    this_source_id = proc.source_ids[proc.name][stream_name]
    # The source status for a given id is 0 when the corresponding
    # source has finished, and is 1 otherwise. Initially it is 1.
    proc.source_status[this_source_id] = 0
    # Inform all processes that this source has finished. The
    # other processes will terminate only after all sources are
    # finished.
    proc.broadcast('source_finished', (proc.name, stream_name))
    
def make_multicore_processes(process_specs, connect_streams, **kwargs):
    processes = process_specs
    # source_status is an array of bytes, one for each source in
    # the multiprocess system. Note that source_status is not restricted to
    # the status of sources in a SINGLE process; it includes source
    # statuses across ALL processes in the multicore application.
    # source_status[j] = 1 if the j-th source is still generating values.
    # source_status[j] = 0 if the j-th source has terminated.
    # Initially source_status[j] = 1 for 0 <= j < MAX_NUM_SOURCES.
    source_status = multiprocessing.Array('B', MAX_NUM_SOURCES)
    # queue_status is an array of bytes, one for each process.
    # queue_status[j] = 1 if the j-th queue is operational and
    # queue_status[j] = 0 if the j-th queue has finished.
    # Initially queue_status[j] = 1 for 0 <= j < MAX_NUM_PROCESSES.
    queue_status = multiprocessing.Array('B', MAX_NUM_PROCESSES)
    connections = make_connections_from_connect_streams(connect_streams)
    #check_processes_connections_format(processes, connections)
    #check_connections_validity(processes, connections)
    
    # Make a proc (i.e. a MulticoreProcess) for each spec (i.e.
    # process specification).
    procs = {}
    # In the following name is a process name and
    # spec is the specification of the process.
    for name, spec in processes.items():
        procs[name] = MulticoreProcess(spec, connect_streams, name)

    # Make the dict relating output streams to queues of receiving
    # processes and to in_stream_signal_names.
    for name in processes.keys():
        procs[name].make_out_to_q_and_in_stream_signal_names(procs)

    # Make the dict relating in_streams of processes to output
    # processes and output streams to which they are connected.
    for name in processes.keys():
        procs[name].make_in_to_out(procs, connections)

    # Create source ids and set source_status to 1 for all sources.
    # The source_id goes from 0, to 1, ... to the number of sources.
    # We associate a source_id with each source. The source_id for
    # each source across the multicore application is unique.
    source_id_count=0
    # source_ids is a dict. key is process_name. value is a dict where
    # source_ids[process_name] is a dict. key: source_name, value: source_id.
    # source_ids[process_name][source_name] is unique for each source in the
    # multicore application.
    source_ids = {}
    for process_name, spec in processes.items():
        source_ids[process_name] = {}
        #sources_dict = spec['sources']
        sources = spec['sources']
        for source_name_and_type in sources:
            source_name, source_type = source_name_and_type
            source_ids[process_name][source_name] = source_id_count
            source_status[source_id_count] = 1
            source_id_count += 1

    # Put the (global) source_ids and source_status in each process.
    for process_name in processes.keys():
        this_process = procs[process_name]
        this_process.source_ids = source_ids
        this_process.source_status = source_status

    #Create main_lock and pass it to all processes.
    main_lock = multiprocessing.Lock()

    # Create process ids and set queue_status.
    # process_ids is a dict where process_ids[process_name]
    # is a unique process_id. This id is unique across all
    # processes in the multicore application.
    #
    # This section of code assigns a unique id (which is
    # process_id_count) to each process. This also sets the
    # queue_status for this process to 1.
    process_id_count=0
    process_ids = {}
    for process_name in processes.keys():
        process_ids[process_name] = process_id_count
        queue_status[process_id_count] = 1
        process_id_count += 1

    # Pass global information, such as main_lock, to each process.
    for process_name in processes.keys():
        this_process = procs[process_name]
        this_process.process_ids = process_ids
        this_process.queue_status = queue_status
        this_process.main_lock = main_lock
        this_process.NUM_PROCESSES = len(processes)
        this_process.all_process_specs = processes
        this_process.all_procs = procs

    # Make processes.
    for name in processes.keys():
        procs[name].make_process()

    # process_list is the list of all processes.
    process_list = [procs[name].process for name in processes.keys()]
    return process_list, procs

def get_processes(multicore_specification):
    connect_streams, process_specs = make_spec_from_multicore_specification(
        multicore_specification)
    processes, procs = make_multicore_processes(process_specs, connect_streams)
    return processes

def get_processes_and_procs(multicore_specification):
    connect_streams, process_specs = make_spec_from_multicore_specification(
        multicore_specification)
    processes, procs = make_multicore_processes(process_specs, connect_streams)
    #input_process, output_process = get_proc_name_for_input_and_output_stream(procs)
    #return processes, procs, input_process, output_process
    return processes, procs

## def get_proc_name_for_input_and_output_stream(procs):
##     input_process = {}
##     output_process = {}
##     for proc_name, multicore_proc in procs.items():
##         process_inputs = multicore_proc.inputs
##         process_outputs = multicore_proc.outputs
##         for process_input in process_inputs:
##             in_stream_name, in_stream_type = process_input
##             input_process[in_stream_name] = proc_name
##         for process_output in process_outputs:
##             out_stream_name, out_stream_type = process_output
##             output_process[out_stream_name] = proc_name
##     return input_process, output_process

def get_proc_that_inputs_source(procs):
    source_stream_name_to_proc = {}
    for proc_name, proc in procs.items():
        for source_stream_name, source_stream_type in proc.sources:
            source_stream_name_to_proc[source_stream_name] = proc
    return source_stream_name_to_proc

def extend_stream(procs, data, stream_name):
    source_stream_name_to_proc = get_proc_that_inputs_source(procs)
    proc = source_stream_name_to_proc[stream_name]
    stream_type = proc.stream_name_to_type[stream_name]
    if stream_type in multiprocessing_type_to_np_type.keys():
        proc.copy_stream(data, stream_name)
    else:
        proc.data_to_receiver_queue(data, stream_name)

def terminate_stream(procs, stream_name):
    source_stream_name_to_proc = get_proc_that_inputs_source(procs)
    proc = source_stream_name_to_proc[stream_name]
    finished_source(proc, stream_name)
    
    
    
    
