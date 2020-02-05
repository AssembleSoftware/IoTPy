import threading
import time
import multiprocessing
import sys
is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue
#import Queue
import sys
import os
sys.path.append(os.path.abspath("../helper_functions"))
# helper_control is in ../helper_functions
# max_wait_time is the maximum time that this thread waits to
# get a new value from a source or other process, before giving
# up and stopping the process.
from system_parameters import max_wait_time

class ComputeEngine(object):
    """
    Manages the queue of agents scheduled for execution.
    When an agent has new data on which to operate, the
    agent is placed on a queue called
    q_agents.

    Parameters
    ----------
    name: str (optional)
      The name of the process in which this ComputeEngine
      operates.
      A process name is required for executing multicore
      computations using multicore.py

    Attributes
    ----------
    input_queue: multiprocessing.Queue
       Elements for input streams of this thread are put
       in this queue.
    name_to_stream: dict
       key: stream name
       value: stream
       The values in name_to_stream are the in_streams of
       compute_func. name_to_stream is set by multicore.
    q_agents: multiprocessing.Queue()
       The queue of agents scheduled for execution.
    scheduled_agents: Set
       An agent is in the set if and only if it is
       in the queue, q_agent. This set is used to ensure
       that each agent appears at most once in the queue.
    compute_thread: threading.Thread
       The compute engine runs in this thread.
    lock: threading.Lock()
       The lock on using scheduled_agents. Ensures
       thread safety for scheduling and de-scheduling
       agents.
    stopped: Boolean
       True if and only if this computation is stopped.
       This attribute can be set to True in
       compute_engine.

    Notes
    -----
    1. Implementation of functionality to get new data from
    sensors and other sources. Also see:
    IoTPy/IoTPy/multiprocessing/multicore.py.
    
    The function create_compute_thread() creates a thread
    and makes self.compute_thread that thread. This thread
    gets a message from input_queue. A message is a 2-tuple:
    (stream_name, data). The thread appends data to the
    stream with the name stream_name. It gets the stream
    from its name by looking up the dict self.name_to_stream.
    
    Incoming messages are "pickleable" provided that
    the data is "pickleable". The thread calls self.step()
    which causes agents to execute their next() functions.

    2. Implementation of execution of agents.
    The queue, q_agents, is the queue of agents scheduled
    for execution. The function self.step() executes a loop
    to get the next agent from the queue and call its next()
    function. The loop terminates when the queue becomes
    empty.

    When an agent that is executing its next() function
    extends a stream s, the stream puts an agent A in
    the queue, q_agents, if s is a call stream of A. So,
    self.step() continues execution until all agents are
    quiescent, i.e., no stream has been modified since an
    agent has read it.

    When self.step() terminates, the compute thread attempts
    to get more data from input_queue. The compute thread
    terminates if no data is available in input_queue for
    a specified time, max_wait_time.

    """
    def __init__(self, process=None):
        self.process = process
        if self.process == None:
            self.process_name = 'DefaultProcess'
            self.process_id = 0
            self.main_lock = None
            self.source_status = None
            self.queue_status = None
        else:
            self.process_name = process.name
            self.process_id = self.process.process_ids[self.process_name]
            self.main_lock = self.process.main_lock
            self.source_status = self.process.source_status
            self.queue_status = self.process.queue_status
        self.input_queue = multiprocessing.Queue()
        self.name_to_stream = {}
        self.q_agents = queue.Queue()
        self.scheduled_agents = set()
        self.compute_thread = None
        self.lock = threading.Lock()
        self.stopped = False
        
    def put(self, a):
        """
        Puts the agent a into q_agents if the 
        agent is not already in the queue.
        
        Parameters
        ----------
        a : Agent

        """
        with self.lock:
            if a not in self.scheduled_agents:
                self.scheduled_agents.add(a)
                self.q_agents.put(a)

    def get(self):
        """
        Waits until q_agents is non-empty, and then gets
        and returns the agent at the head of the queue.
        Updates the set, scheduled_agents, to ensure that
        the set contains exactly those agents in q_agents.

        Returns
        -------
        a: Agent
           The agent at the head of the queue of scheduled
           agents.

        Note
        ----
        Get the agent at the head of the queue of agents waiting to be
        executed and discard that agent from the set of
        waiting-for-scheduling agents. 

        """
        with self.lock:
            a = self.q_agents.get()
            self.scheduled_agents.discard(a)
            return a

    def create_compute_thread(self):
        def target_of_compute_thread():
            while not self.stopped:
                # Wait at most max_wait_time seconds to get the next
                # message from self.input_queue. If the message is
                # obtained then process it; else, stop this iteration
                # and thread.
                # max_wait_time is specified in system_parameters.
                self.main_lock.acquire()
                if self.input_queue.empty():
                    self.queue_status[self.process_id] = 0
                if sum(self.source_status) + sum(self.queue_status) == 0:
                    self.process.broadcast('stop', 'stop')
                self.main_lock.release()
                try:
                    v = self.input_queue.get()
                except:
                    self.stopped = True

                if not self.stopped:
                    # Succeeded in getting a message from input_queue.
                    # This message, v, is:
                    #     (stream name, element for this stream)
                    # Get the specified stream name and its next element.
                    out_stream_name, new_data_for_stream = v
                    if out_stream_name == 'source_finished':
                        # Then new_data_for_stream is the
                        # (process name, source name) of the source
                        # that has finished execution.
                        # Check the termination condition to determine
                        # if the entire computation has terminated.
                        # Go to the beginning of the while loop.
                        pass
                    elif out_stream_name == 'stop':
                        # Stop this process.
                        self.stopped = True
                    else:
                        # This message is to be appended to the specified
                        # out_stream.
                        # Get the stream from its name
                        out_stream = self.name_to_stream[out_stream_name] 
                        out_stream.append(new_data_for_stream)
                        # Take a step of the computation, i.e.
                        # process the new input data and continue
                        # executing this thread.
                        self.step()
            # Exit loop, and terminate thread when self.stopped is
            # True. 
            return
        self.compute_thread = threading.Thread(
            target=target_of_compute_thread,
            name=self.process_name, args=())

    def start(self):
        """
        Starts the compute thread.
        Gets stream_name, data_for_stream from input_queue and appends
        the data to the stream with the specified name.

        """
        self.create_compute_thread()
        self.compute_thread.start()

    def step(self):
        """
        Continues executing the next() step of an
        agent in the queue of agents until the queue
        gets empty.
        Note: Update the set, scheduled_agents, to
        ensure that this set contains exactly the
        agents in the queue of agents.

        """
        while self.scheduled_agents:
            a = self.q_agents.get()
            self.scheduled_agents.discard(a)
            a.next()
        return

    def join(self):
        self.compute_thread.join()


        


