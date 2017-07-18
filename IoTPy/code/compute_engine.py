import threading
import time
import Queue

source_queue = Queue.Queue()

class StopComputeEngine(object):
    pass
_stop_compute_engine = StopComputeEngine()



class Scheduler():
    """
    Manages the queue of agents scheduled for execution.
    When an agent has new data on which to operate, the
    agent is placed on a queue called
    queue_of_scheduled_agents.

    Attributes
    ----------
    queue_of_scheduled_agents: Queue.Queue()
       The queue of agents scheduled for execution.
    set_of_scheduled_agents: Set
       An agent is in the set if and only if it is
       in the queue. This set is used to ensure that
       each agent appears at most once in the queue.

    """
    def __init__(self):
        self.queue_of_scheduled_agents = Queue.Queue()
        self.set_of_scheduled_agents = set()
        self.thread = None
        self.started = False
        self.stopped = False
    def put(self, a):
        """
        Puts the agent a into the queue if the agent
        is not already in the queue.
        
        Parameters
        ----------
        a : Agent

        """
        if a not in self.set_of_scheduled_agents:
            self.set_of_scheduled_agents.add(a)
            self.queue_of_scheduled_agents.put(a)

    def get(self):
        """
        Waits until the queue is non-empty, and then
        gets and returns the agent at the head
        of the queue.
        
        Parameters
        ----------
        None

        Returns
        -------
        a: Agent
           The agent at the head of the queue of scheduled
           agents.

        """
        a = self.queue_of_scheduled_agents.get()
        self.set_of_scheduled_agents.discard(a)
        return a

    def start(self):
        self.stopped = False
        self.started = True
        def execute_computation():
            while not self.stopped:
                while not source_queue.empty():
                    out_stream, new_data_for_stream = source_queue.get()
                    out_stream.extend(new_data_for_stream)
                    self.unity()
                time.sleep(0.1)
            return
        
        self.thread = threading.Thread(
            target=execute_computation, args=())
        self.thread.start()
    
    def stop(self):
        self.stopped = True
        self.thread.join()

    def join(self):
        self.thread.join()

    def unity(self):
        while self.set_of_scheduled_agents:
            a = self.queue_of_scheduled_agents.get()
            self.set_of_scheduled_agents.discard(a)
            a.next()

    def execute_single_step(self):
        self.unity()

compute_engine = Scheduler()


