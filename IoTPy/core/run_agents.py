import threading
import time
import Queue


class ComputeEngine(object):
    """
    Manages the queue of agents scheduled for execution.
    When an agent has new data on which to operate, the
    agent is placed on a queue called
    q_agents.

    Parameters
    ----------
    name: str (optional)
       name used only for debugging.

    Attributes
    ----------
    q_agents: Queue.Queue()
       The queue of agents scheduled for execution.
    scheduled_agents: Set
       An agent is in the set if and only if it is
       in q_agents. This set is used to ensure that
       each agent appears at most once in the queue.
    lock: threading.RLock()
       Controls access to q_agents and scheduled_agents.
    stopped: bool
       Set to True to stop the thread that runs
       agents.
    run_agents_thread: threading.Thread
       The thread that gets the next agent from q_agents
       and executes the (next step of the) agent.

    """
    def __init__(self, name=None):
        self.q_agents = Queue.Queue()
        self.scheduled_agents = set()
        self.rlock = threading.RLock()
        self.name = name
        self.stopped = False
        self.run_agents_thread = None
        self.ready = threading.Event()
        
    def put(self, a):
        """
        Puts the agent a into q_agents if the 
        agent is not already in the queue.
        
        Parameters
        ----------
        a : Agent

        """
        with self.rlock:
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
        a = self.q_agents.get()
        with self.rlock:
            self.scheduled_agents.discard(a)
        return a

    def start(self):
        # execute_agents is the target for the
        # run_agents_thread
        self.ready.set()
        def execute_agents():
            nnn = 0
            while not self.stopped:
                a = self.get()
                # Release rlock so that other
                # threads can put agents into
                # q_agents, or set stopped to
                # True
                a.next()
                nnn += 1
                if nnn > 10:
                    self.stopped=True
        self.run_agents_thread = threading.Thread(
            target=execute_agents, args=())
        self.run_agents_thread.start()

    def stop(self):
        self.stopped = True
        self.run_agents_thread.join()
    def join(self):
        self.stopped = True
        self.run_agents_thread.join()
    def step(self):
        """
        Execute agents until no agents are
        available for execution.

        """
        while self.scheduled_agents:
            with self.rlock:
                a = self.q_agents.get()
                # This discard seems necessary!
                self.scheduled_agents.discard(a)
            # Release lock while running an agent.
            a.next()
        return

        


