"""
This module makes processes for a multicore application.
It uses multiprocessing.Array to enable multiple processes to
share access to streams efficiently.
"""
import sys
import os
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
import time
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../helper_functions"))

# sink, op are in the agent_types folder
from sink import stream_to_queue, sink_list, sink_element
from op import map_element, map_list
# compute_engine, stream are in the core folder
from compute_engine import ComputeEngine
from stream import Stream
# basics is in the helper_functions folder
from basics import map_e, fmap_e, map_l, f_mul
from print_stream import print_stream
# utils is in the current folder
from utils import check_processes_connections_format, check_connections_validity

# BUFFER_SIZE is the default length of each buffer.
BUFFER_SIZE = 2**20
# MAX_NUM_SOURCES is the maximum number of sources in a multicore application.
MAX_NUM_SOURCES = 10
MAX_NUM_PROCESSES = 8

#-----------------------------------------------------------------------
class Proc(object):
    """
    Proc creates a process in a multicore application.

    Parameters
    ----------
    spec: dict
      spec is a specification of a process.
      The keywords of spec are the following strings.
         'in_stream_names_types'
         'out_stream_names_types'
         'compute_func'
         'keyword_args'
         'sources'
         'actuators'
       The keyword 'compute_func' is required. The other keywords
       of spec can be omitted in which case a default value is used.
    connections: dict
      connections specifies the connection of an output stream of a
      process to the input stream of the same or another process.
    name: str
      Every process must have a unique name.

    Attributes
    ----------
    in_stream_names_types : list
       in_stream_names_types is a list of pairs where each pair is
       (in_stream name, in_stream_type). An in_stream_type is a
       str defined in multiprocessing.Array. For example 'i' stands
       for int.
       The order of the pairs must correspond to the order of
       in_streams in compute_func.
       Example of in_stream_names_types = [('in', 'i')]
       which says that the compute function (compute_func) has a
       single input stream called 'in' which is of type int.
       Default: empty list
    out_stream_names_types : list
       Similar to in_stream_names_types.
       Example of out_stream_names_types = [('out', 'i')]
       which says that the compute function (compute_func) has a
       single input stream called 'out' which is of type int.
       Default: empty list
    compute_func: function
       The main thread of this process executes compute_func which
       creates a network of agents and runs the agents.
       compute_func is the function that carries out computation for
       this agent. compute_func(in_streams, out_streams) creates a
       network of agents.
       in_streams must correspond to in_stream_names_types.
       out_streams must correspond to out_stream_names_types.
       The thread that executes compute_func is started by starting
       stream.scheduler (see core/ComputeEngine.py).
    keyword_args: dict
       The keys of this dict are the keyword arguments of the
       function, compute_func. The value corresponding to a key
       is the CONSTANT value for the corresponding keyword argument.
       Example: {'ADDEND' :10} where ADDEND is a keyword argument of
       compute_func, and this keyword argument has value 10.
       Default: empty dict.
    sources: dict
       The keys of sources are names of sources. The value corresponding
       to a key is a description of the source. This description is
       also a dict with two keys: The type of data produced by the source
       and the function that generates the data. This function runs in
       its own thread.
       Example of sources:
          {'acceleration':
              {'type': 'i',
               'func': source_thread_target
              }
       This process has a single source called 'acceleration' which uses
       the function source_thread_target to generate int data.
       Default: empty dict
    out_to_in: dict
        The keys are out_stream names of this process, and the
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
    in_to_out: dict
       The keys are in_stream_names of this process and the values are
       pairs (out_process_name, out_stream_name).
       Example of self. in_to_out:
       {
         'in': ('get_source_data_and_compute_process', 'acceleration')
       }
       This process has an input stream called 'in' connected to an
       output stream called 'acceleration' in the process called
       'get_source_data_and_compute_process'
       The output stream may be an output of compute_func or an
       a source.
        

    Notes
    -----
    Examples of spec and connections are at the end of this file.
    See TEST.

    """
    def __init__(self, spec, connections, name):
        self.spec = spec
        # Connections is a dict that specifies connections from outputs of
        # processes or sources to inputs of other processes.
        self.connections = connections
        self.name = name
        # in_stream_names_types is a list of in_stream names and their types.
        if 'in_stream_names_types' in self.spec:
            self.in_stream_names_types = self.spec['in_stream_names_types']
        else:
            self.in_stream_names_types = []
        # out_stream_names_types is a list of out_stream names and their types.
        if 'out_stream_names_types' in self.spec:
            self.out_stream_names_types = self.spec['out_stream_names_types']
        else:
            self.out_stream_names_types = []
        self.compute_func = self.spec['compute_func']
        if 'keyword_args' in self.spec:
            self.keyword_args = self.spec['keyword_args']
        else:
            self.keyword_args = {}
        if 'sources' in self.spec:
            self.sources = self.spec['sources']
        else:
            self.sources = {}
        if 'actuators' in self.spec:
            self.actuators = self.spec['actuators']
        else:
            self.actuators = {}
        self.out_to_in = self.connections[self.name]
        # out_to_buffer[out_stream_name] is (buffer, buffer_ptr) which is
        # the buffer to which this out_stream_name or source_name is connected.
        # Next, compute out_to_buffer.
        self.out_to_buffer = {}
        # create a buffer for each out_stream and each source of this process.
        # 1. Create a buffer for each out_stream of this process.
        # self.out_to_buffer[out_stream_name] becomes the buffer for the stream called
        # out_stream_name.
        # self.out_stream_names_types is a list of pairs:
        #                   ( out_stream_name, out_stream_type)
        for out_stream_name, out_stream_type in self.out_stream_names_types:
            buffer = multiprocessing.Array(out_stream_type, BUFFER_SIZE)
            # buffer_ptr is an integer with initial value of 0.
            buffer_ptr = multiprocessing.Value('i', 0)
            self.out_to_buffer[out_stream_name] =  (buffer, buffer_ptr)
        # 2. Create a buffer for each source of this process.
        # self.out_to_buffer[source_name] is the buffer for the source called
        # source_name
        for source_name, source_type_and_func in self.sources.items():
            source_type  = source_type_and_func['type']
            buffer = multiprocessing.Array(source_type, BUFFER_SIZE)
            # buffer_ptr is an integer with initial value of 0.
            buffer_ptr = multiprocessing.Value('i', 0)
            self.out_to_buffer[source_name] =  (buffer, buffer_ptr)
        # out_to_q_and_in_stream_signal_names[out_stream_name] is 
        # a list of pairs (q, in_stream_signal_name).
        # where q is the queue of the receiving process and
        # in_stream_signal_name is 's_signal_' if the in_stream is 's'.
        # make_out_to_q_and_in_stream_signal_names() is the function
        # that fills in out_to_q_and_in_stream_signal_names.
        self.out_to_q_and_in_stream_signal_names = {}
        # in_queue is the input queue of this process.
        self.in_queue = multiprocessing.Queue()
        # process is created from the process specification and
        # connections. It is obtained by the function make_process().
        self.process = None
        # in_to_out[in_stream_name] is a pair:
        #    (sender_process_name, out_stream_name)
        # in_to_out is filled in by the function
        # make_in_to_out()
        self.in_to_out = {}
        # in_to_buffer[in_stream_name] is a buffer. Data in this buffer
        # is copied into this in_stream.
        # in_to_buffer is computed by the function make_in_to_out().
        self.in_to_buffer = {}
        # Set by calling multicore
        self.process_ids = {}
        self.source_ids = {}
        self.source_status = {}
        self.queue_status = {}
        self.all_process_specs = {}
        self.all_procs = {}
        # main_lock is the lock acquired to do operations on
        # in_queue of processes. These operations check whether the
        # queues are empty. Empty queues are used to detect termination.
        self.main_lock = None
        return

    def make_in_to_out(self, procs, connections):
        """
        Computes self.in_to_out and self.in_to_buffer

        Parameters
        ----------
        procs: dict
           procs[proc_name] is an instance of the Proc class

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
        # Create q_and_in_stream_signal_names for each out_stream and
        # each source of this process.
        # 1. Create q_and_in_stream_signal_names for each out_stream of this process.
        for out_stream_name, out_stream_type in self.out_stream_names_types:
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
                self.out_to_q_and_in_stream_signal_names[out_stream_name].append(
                    (receiver_proc.in_queue, in_stream_name + '_signal_'))

        # 2. Create q_and_in_stream_signal_names for each source of this process.
        # self.out_to_q_and_in_stream_signal_names[name] is the
        # q_and_in_stream_signal_names for the connections to the source called
        # name
        for source_name, source_type_and_func in self.sources.items():
            self.out_to_q_and_in_stream_signal_names[source_name] = []
            # receivers is a list of pairs (process name, in_stream name)
            receivers = self.out_to_in[source_name]
            for receiver_proc_name, in_stream_name in receivers:
                # receiver_proc is the Proc with the name, receiver_proc_name.
                receiver_proc = procs[receiver_proc_name]
                # (1) Associate the in_queue of the receiver process with the
                #     source called source_name.
                # (2) The messages about new data in the source called source_name
                #     are sent to the stream called in_stream_name + '_signal_'
                #     in the receiver process.
                self.out_to_q_and_in_stream_signal_names[source_name].append(
                    (receiver_proc.in_queue, in_stream_name + '_signal_'))
        return

    # Make the process. First define the target() function of the process.
    def make_process(self):
        def target():
            """
            This is the target function of this process. This function has the
            following steps:
            1. Create in_streams of the this process, i.e., the in_streams of
               the compute_func of the process.
            2. Create in_stream_signals, with an in_stream_signal corresponding
               to each in_stream.
            3. Create out_streams of this process, i.e. out_streams of the
               compute_func of this process.
            4. Create the computational agent (compute_func) of this process.
            5. For each out_stream of compute_func, create an agent to copy the
               out_stream to its buffer, and then copy the buffer to each
               in_stream to which it is connected.
            6. For each in_stream of compute_func, create an agent to copy its
               input buffer into the in_stream.
            7. Create the scheduler for this process. Starting the scheduler
               starts the thread that executes compute_func for this agent.
            8. Create the source threads for each source in this process. The
               source_thread gets data from a source, puts the data into a
               buffer, and then copies the buffer to each in_queue to which the
               source is connected.
            9. Start the scheduler and source threads.
            10. Join the scheduler and source threads.
               
            """
            # STEP 1
            # CREATE THE IN_STREAMS OF COMPUTE_FUNC 
            # and compute the dict, name_to_stream.
            # in_streams is the list of in_stream of this process.
            self.in_streams = []
            # name_to_stream is a dict where the key is the name of an
            # input or output stream and the value is the stream itself.
            self.name_to_stream = {}
            for in_stream_name, in_stream_type in self.in_stream_names_types:
                in_stream = Stream(name=in_stream_name)
                self.in_streams.append(in_stream)
                self.name_to_stream[in_stream_name] = in_stream

            # STEP 2
            # CREATE IN_STREAM_SIGNALS which is a list of input streams, with
            # one in_stream_signal for each in_stream.
            # in_stream_signal[j] is the stream that tells
            # this process that it has data to be read into
            # in_stream[j]. The name of an in_stream_signal associated with an
            # in_stream called 's' is 's_signal_'.
            self.in_stream_signals = []
            for in_stream in self.in_streams:
                in_stream_signal_name = in_stream.name + '_signal_'
                in_stream_signal = Stream(name=in_stream_signal_name)
                self.in_stream_signals.append(in_stream_signal)
                self.name_to_stream[in_stream_signal_name] = in_stream_signal

            # STEP 3
            # CREATE THE OUT_STREAMS FOR COMPUTE_FUNC.
            # out_streams is a list of the output streams of this process.
            self.out_streams = []
            for out_stream_name, out_stream_type in self.out_stream_names_types:
                out_stream = Stream(out_stream_name)
                self.out_streams.append(out_stream)
                self.name_to_stream[out_stream_name] = out_stream

            # STEP 4
            # CREATE THE COMPUTE AGENT FOR THIS PROCESS.
            self.compute_func(self.in_streams, self.out_streams, **self.keyword_args)

            # STEP 5
            # CREATE AGENTS TO COPY EACH OUT_STREAM OF COMPUTE_FUNC TO IN_STREAMS.
            # Note: Create an agent for each out_stream of compute_func and
            # create an agent for each source. This agent copies the elements
            # in each out_stream into the in_streams to which it is connected.
            # See copy_stream().
            #
            # self.out_stream_names_types is a list of pairs:
            #             (out_stream_name, out_stream_type)
            for out_stream_name, out_stream_type in self.out_stream_names_types:
                # STEP 5.1: Get parameters of each agent.
                # Step 5.1.1 Get the out_stream with the specified name.
                out_stream = self.name_to_stream[out_stream_name]
                # Step 5.1.2 Get the buffer and buffer_ptr into which this out_stream
                # is copied.
                buffer, buffer_ptr = self.out_to_buffer[out_stream_name]
                # Step 5.1.3 Get the list of pairs (q, in_stream_signal_name) connected
                # to this out_stream
                q_and_in_stream_signal_names = \
                    self.out_to_q_and_in_stream_signal_names[out_stream_name]
                # STEP 5.2: Make agent that copies out_stream to the in_streams to
                # which it is connected. The input stream to this agent is out_stream.
                # stream_name is a keyword argument of copy_stream().
                sink_list(func=self.copy_stream, in_stream=out_stream,
                          stream_name=out_stream_name)

            # STEP 6
            # CREATE AGENTS TO COPY BUFFERS TO IN_STREAMS.
            # For each in_stream of this process, create an agent that
            # copies data from the input buffer of this in_stream into
            # the in_stream.
            # This agent subscribes to the in_stream_signal associated
            # with this in_stream. When in_stream_signal gets a message
            # (start, end) this agent copies the buffer segment between
            # start and end into the in_stream.
            # copy_buffer_segment() is the function executed by the agent
            # when a new message arrives. This function extends out_stream
            # with the segment of the buffer specified by the message.
            for in_stream_name, in_stream_type in self.in_stream_names_types:
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
                    buffer=buffer, in_stream_type=in_stream_type)

            # STEP 7
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

            # STEP 8
            # CREATE SOURCE_THREADS
            source_threads = []
            for source_name, description in self.sources.items():
                # thread_creation_func returns a thread which
                # gets data from a source with name source_name and then
                # uses self.copy_stream to copy the data into a
                # buffer associated with this source, and
                # informs all in_streams connected to this source that
                # new data has arrived.
                thread_target = description['func']
                # Get the source_thread for the source with this name.
                #source_thread = thread_creation_func(self.copy_stream, source_name)
                source_thread = self.create_source_thread(thread_target, source_name)
                source_threads.append(source_thread)

            # STEP 9
            # START SOURCE THREADS AND START SCHEDULER.
            # Starting the scheduler starts a thread --- the main thread --- of this
            # process. The scheduler thread gets a ready agent from the in_queue of
            # this process and then executes the next step of the agent.
            Stream.scheduler.start()
            for source_thread in source_threads:
                source_thread.start()

            # STEP 10
            # JOIN SOURCE THREADS AND JOIN SCHEDULER.
            for source_thread in source_threads:
                source_thread.join()

            Stream.scheduler.join()
            return

        # Create the process.
        self.process = multiprocessing.Process(target=target)

    def create_source_thread(self, thread_target, stream_name):
        this_source = (self, stream_name)
        return threading.Thread(target=thread_target,
                                args=(this_source,))
    
    def copy_stream(self, lst, stream_name):
        """
        Parameters
        ----------
          lst: list
            the sequence of values that are copied to streams connected to this
            stream
          stream_name: str
            The name of the stream that is copied to other streams.
        Notes
        -----
        This is the function called by sink agents to take the following steps:
        STEP 1: Get objects connected to the stream with this name.
        STEP 2: Copy lst into the circular buffer which is the output buffer for
                this stream.
        STEP 3: Put a message into the queue of each process that receives lst.
                This message is put into an in_stream_signal of the receiving
                process.
        STEP 4: Update parameters to get ready for next call to this function.

        """
        # STEP 1: GET BUFFER, QUEUE, STREAMS CONNECTED TO THIS STREAM
        buffer, buffer_ptr = self.out_to_buffer[stream_name]
        q_and_in_stream_signal_names = \
            self.out_to_q_and_in_stream_signal_names[stream_name]

        # STEP 2: COPY LST INTO THE CIRCULAR BUFFER
        n = len(lst)
        assert n < BUFFER_SIZE, \
          "The length of input data is greater than the buffer size"
        buffer_end_ptr = buffer_ptr.value + n
        if buffer_end_ptr < BUFFER_SIZE:
            # In this case, don't need to wrap around the
            # end of the buffer.
            buffer[buffer_ptr.value : buffer_end_ptr] = lst
        else:
            # In this case, must wrap around the end of
            # the circular buffer.
            # remaining_space is the space remaining from
            # buffer_ptr to the end of the buffer.
            remaining_space = BUFFER_SIZE - buffer_ptr.value
            # Copy remaining_space elements of the list
            # to fill up the buffer.
            buffer[buffer_ptr.value:] =  lst[:remaining_space]
            # That leaves n-remaining_space elements of the
            # list that are yet to be copied into the buffer.
            # Copy the remaining elements of list into the
            # buffer starting from slot 0.
            buffer[:n-remaining_space] = lst[remaining_space:]
            buffer_end_ptr = n-remaining_space

        # STEP 3: TELL THE RECEIVER PROCESSES THAT THEY HAVE NEW
        # DATA.
        # 1. Set the status of queues that will now get data to
        # 'not empty' or 1.
        # 2. Put a message into the queue of each process that
        # receives a copy of lst.

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
            q.put((in_stream_signal_name, (buffer_ptr.value, buffer_end_ptr)))
        self.main_lock.release()

        # STEP 4: UPDATE BUFFER_PTR TO GET READY FOR NEXT INPUT.
        buffer_ptr.value = buffer_end_ptr
        return
    def broadcast(self, receiver_stream_name, msg):
        for process_name in self.all_process_specs.keys():
            this_process = self.all_procs[process_name]
            this_process.in_queue.put((receiver_stream_name, msg))

#-------------------------------------------------------------------

#-------------------------------------------------------------------
def copy_buffer_segment(message, out_stream, buffer, in_stream_type):
    """
    copy_buffer_segment() is the function executed by the agent
    when a new message arrives. A message is (start, end).
    This function extends out_stream with the segment of the buffer
    between start and end.
    """
    start, end = message
    if end >= start:
        return_value = buffer[start:end]
    else:
        # The return value is read from the circular buffer
        # by going to the end of the buffer and adding values
        # from the beginning of the buffer.
        remaining_space = BUFFER_SIZE - start
        segment_length = remaining_space + end
        # Set up an array with appropriate length to be filled in later.
        return_value = multiprocessing.Array(in_stream_type, range(segment_length))
        return_value[:remaining_space] = \
            multiprocessing.Array(in_stream_type, buffer[start:])
        return_value[remaining_space:] = \
            multiprocessing.Array(in_stream_type, buffer[:end])
    out_stream.extend(list(return_value))
    return
#-------------------------------------------------------------------

def copy_data_to_source(data, source):
    """
    Function used by source thread targets.
    See source_thread_target in TEST

    """
    proc, stream_name = source
    proc.copy_stream(data, stream_name)

def source_finished(source):
    """
    Set the source_status of this source to 0 to
    indicate that this source has terminated execution.

    Called by source thread functions.
    """
    proc, source_name = source
    process_name = proc.name
    this_source_id = proc.source_ids[process_name][source_name]
    proc.source_status[this_source_id] = 0
    proc.broadcast('source_finished', (process_name, source_name))
        
def multicore(processes, connections):
    source_status = multiprocessing.Array('B', MAX_NUM_SOURCES)
    queue_status = multiprocessing.Array('B', MAX_NUM_PROCESSES)
    check_processes_connections_format(processes, connections)
    check_connections_validity(processes, connections)
    procs = {}
    # In the following name is a process name and
    # spec is the specification of the process.
    for name, spec in processes.items():
        procs[name] = Proc(spec, connections, name)
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
    for name in processes.keys():
        procs[name].process.start()
    for name in processes.keys():
        procs[name].process.join()
    for name in processes.keys():
        procs[name].process.terminate()

def run_single_process_single_source(source_func, compute_func, source_type='f'):
    """
    Function for creating a multiprocess application consisting
    of a single process with a single source and no actuators
    and with no external input or output streams from or to other
    processes.
    This function creates the process, starts the process and
    finally joins (stops) the process.
    """

    # Specify processes and connections.
    processes = \
      {
        'process':
           {'in_stream_names_types': [('in', source_type)],
            'out_stream_names_types': [],
            'compute_func': compute_func,
            'sources':
              {'single_source':
                  {'type': source_type,
                   'func': source_func
                  },
               },
            'actuators': {}
           }
      }
    
    connections = \
      {
          'process' :
            {
                'single_source' : [('process', 'in')]
            }
      }

    multicore(processes, connections)
    
    
#-------------------------------------------------------------
#  TEST
#-------------------------------------------------------------

@map_e
def gg(v, ADD_VALUE):
    return v + ADD_VALUE

@map_e
def increment(v): return v+1
            
def test_parameter(ADDEND_VALUE):
    # Functions wrapped by agents
    # Function f is used in get_source_data_and_compute_process
    # ADDEND is a keyword arg of f.
    # Note: ADDEND must be passed in the specification of
    # the process. See the line:
    # 'keyword_args' : {'ADDEND' :ADDEND_VALUE},
    def f(in_streams, out_streams, ADDEND):
        gg(in_streams[0], out_streams[0], ADD_VALUE=ADDEND)
    # Function g is used in aggregate_and_output_process
    # Function g has no arguments other than in_streams and out_streams.
    # So we do not have to add 'keyword_args' : {}
    # to the specification of the process.
    def g(in_streams, out_streams):
        s = Stream(name='s')
        increment(in_stream=in_streams[0], out_stream=s)
        print_stream(s, name=s.name)

    # Target of source thread.
    def source_thread_target(source):
        num_steps=3
        step_size=3
        for i in range(num_steps):
            data = list(range(i*step_size, (i+1)*step_size))
            copy_data_to_source(data, source)
            time.sleep(0.001)
        source_finished(source)
        return

    #---------------------------------------------------------------------
    # Specify processes and connections.
    # This example has two processes:
    # (1) get_source_data_and_compute_process and
    # (2) aggregate_and_output_process.
    
    # Specification of get_source_data_and_compute_process:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has a single output stream called 'out'
    # which is of type int ('i').
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function f.
    # (4) Keyword arguments: Function f has a keyword argument
    # called ADDEND. This argument must be a constant.
    # (5) sources: This process has a single source called
    # 'acceleration'. The source thread target is specified by
    # the function source_thread_target. This function generates
    # int ('i').
    # (6) actuators: This process has no actuators.
    
    # Specification of aggregate_and_output_process:
    # (1) Inputs: It has a single input stream called 'in' which
    # is of type int ('i').
    # (2) Outputs: It has no outputs.
    # (3) Computation: It creates a network of agents that carries
    # out computation in the main thread by calling function g.
    # (4) Keyword arguments: Function g has no keyword argument
    # (5) sources: This process has no sources
    # (6) actuators: This process has no actuators.

    # Connections between processes.
    # (1) Output 'out' of 'get_source_data_and_compute_process' is
    # connected to input 'in' of aggregate_and_output_process.
    # (2) The source, 'acceleration', of 'get_source_data_and_compute_process'
    # is connected to input 'in' of 'get_source_data_and_compute_process'.
    
    processes = \
      {
        'get_source_data_and_compute_process':
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
        'aggregate_and_output_process':
           {'in_stream_names_types': [('in', 'i')],
            'out_stream_names_types': [],
            'compute_func': g,
            'keyword_args' : {},
            'sources': {},
            'actuators': {}
           }
      }
    
    connections = \
      {
          'get_source_data_and_compute_process' :
            {
                'out' : [('aggregate_and_output_process', 'in')],
                'acceleration' : [('get_source_data_and_compute_process', 'in')]
            },
           'aggregate_and_output_process':
            {}
      }
    #--------------------------------------------------------------------

    #--------------------------------------------------------------------
    # Create and run multiple processes in a multicore machine.
    multicore(processes, connections)

def test_single_process_single_source():
    # Target of source thread.
    def source_func(source):
        num_steps=5
        step_size=4
        for i in range(num_steps):
            data = list(range(i*step_size, (i+1)*step_size))
            copy_data_to_source(data, source)
            time.sleep(0.001)
        source_finished(source)
    def compute_func(in_streams, out_streams):
        print_stream(in_streams[0])

    run_single_process_single_source(source_func, compute_func)





if __name__ == '__main__':
    print ('Output printed are values of stream s. See function g')
    print ('s[j] = 500 + j, because the ADDEND is 500')
    test_parameter(500)
    test_single_process_single_source()
