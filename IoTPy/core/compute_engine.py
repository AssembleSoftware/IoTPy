import threading
import time
import multiprocessing
import Queue
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
      The name given to the thread in which the
      computational engine executes. Used in
      debugging.

    Attributes
    ----------
    input_queue: multiprocessing.Queue
       Elements for input streams of this thread are put
       in this queue.
    name_to_stream: dict
       key: stream name
       value: stream
    q_agents: Queue.Queue() or multiprocessing.Queue()
       The queue of agents scheduled for execution.
    scheduled_agents: Set
       An agent is in the set if and only if it is
       in the queue. This set is used to ensure that
       each agent appears at most once in the queue.
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

    """
    def __init__(self, name='compute_engine_thread'):
        self.name = name
        self.input_queue = multiprocessing.Queue()
        self.name_to_stream = {}
        self.q_agents = Queue.Queue()
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

    def start(self):
        def execute_computation():
            while not self.stopped:
                # Wait at most max_wait_time seconds to get the next
                # message from self.input_queue. If the message is
                # obtained then process it; else, stop this iteration
                # and thread.
                try:
                    v = self.input_queue.get(
                        timeout=max_wait_time)
                except:
                    print 'Stopped: No more input.'
                    self.stopped = True

                if not self.stopped:
                    # Succeeded in getting a message from input_queue.
                    # This message is:
                    #     (stream name, element for this stream)
                    # Get the specified stream and its next element.
                    out_stream_name, new_data_for_stream = v
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
            target=execute_computation, name=self.name, args=())
        self.compute_thread.start()
        return

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


        


