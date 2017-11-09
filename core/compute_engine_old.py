import threading
import time
import multiprocessing
import Queue
import sys
import os
#sys.path.append(os.path.abspath("../core"))
#from stream import *

# Add lock for scheduled_agents


class ComputeEngine(object):
    """
    Manages the queue of agents scheduled for execution.
    When an agent has new data on which to operate, the
    agent is placed on a queue called
    q_agents.

    Parameters
    ----------
    input_queue: multiprocessing.Queue
       Elements for input streams of this thread are put
       in this queue.
    name_to_stream: dict
       key: stream name
       value: stream

    Attributes
    ----------
    q_agents: Queue.Queue() or multiprocessing.Queue()
       The queue of agents scheduled for execution.
    scheduled_agents: Set
       An agent is in the set if and only if it is
       in the queue. This set is used to ensure that
       each agent appears at most once in the queue.

    """
    def __init__(self, name=None):
        self.input_queue = multiprocessing.Queue()
        self.name_to_stream = None
        self.name = name
        self.q_agents = Queue.Queue()
        self.scheduled_agents = set()
        self.compute_thread = None
        self.started = False
        self.stopped = False
        self.lock = threading.Lock()
        self.ready = threading.Event()
        
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
        Waits until q_agents is non-empty, 
        and then gets and returns the agent at the head
        of the queue.

        Returns
        -------
        a: Agent
           The agent at the head of the queue of scheduled
           agents.

        """
        with self.lock:
            a = self.q_agents.get()
            self.scheduled_agents.discard(a)
            return a

    def start(self):
        self.ready.set()
        def execute_computation():
            nnn = 0
            while not self.stopped:
                try:
                    v = self.input_queue.get(timeout=0.5)
                    #v = self.input_queue.get()
                    if v == 'closed':
                        self.stopped = True
                        break
                    out_stream_name, new_data_for_stream = v
                    out_stream = self.name_to_stream[out_stream_name]
                    #out_stream.extend(new_data_for_stream)
                    out_stream.append(new_data_for_stream)
                except:
                    print 'no data in input queue', self.input_queue
                    # Sleep for SLEEP_TIME seconds
                    # Stop after LIMIT number of empty gets
                    SLEEP_TIME = 0.5
                    LIMIT = 2
                    nnn += 1
                    if nnn > LIMIT:
                        self.stopped = True
                    time.sleep(SLEEP_TIME)
                self.step()
        self.compute_thread = threading.Thread(
            target=execute_computation, args=())
        self.compute_thread.start()
    
    def stop(self):
        self.stopped = True
        self.compute_thread.join()
    def join(self):
        self.compute_thread.join()

    def step(self):
        while self.scheduled_agents:
            a = self.q_agents.get()
            # This next discard is necessary!! Check.
            self.scheduled_agents.discard(a)
            a.next()
        return
    
# Creates one scheduler from compute_engine.py
#scheduler = ComputeEngine()


        


