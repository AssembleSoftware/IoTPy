import threading
import multiprocessing
import sys
# Check the version of Python
is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue

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
       in this queue. Each element of the queue is a 2-tuple:
       (stream_name, data). 
    name_to_stream: dict
       key: stream name
       value: stream
       The values in name_to_stream are the in_streams of
       compute_func. name_to_stream is defined in multicore().
       name_to_stream['s'] is the stream with name 's'.
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
       This attribute can be set to True only in the
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
    from the stream's name by looking up the dict
    self.name_to_stream.
    
    Incoming messages are "pickleable" provided that
    the data is "pickleable". The thread calls self.step()
    which causes agents to execute their next() functions.

    2. Implementation of execution of agents.
    The queue, q_agents, is the queue of agents scheduled
    for execution. The function self.step() executes a loop
    to get the next agent from the queue and call its next()
    function. The loop terminates when the queue becomes
    empty. At that point all agents are quiescent, waiting
    for more input.

    When an agent that is executing its next() function
    extends a stream s, the stream puts an agent A in
    the queue, q_agents, if s is a call stream of A. So,
    self.step() continues execution until all agents are
    quiescent, i.e., no stream has been modified since an
    agent has read it.

    When self.step() terminates, the compute thread attempts
    to get more data from input_queue. The compute thread
    terminates if no data is available in input_queue.

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

                # With main_lock -------------------------------
                self.main_lock.acquire()
                # If the input queue is empty then set the queue
                # status of this process to empty, i.e., 0.
                if self.input_queue.empty():
                    self.queue_status[self.process_id] = 0
                # If all the sources have finished and all the queues
                # are empty then broadcast 'stop'. This broadcast
                # message is received by this process as well.
                # So, the input queue of this process will also contain
                # the 'stop' message, and so this queue will not be empty.
                # When a 'stop' message is received, this thread terminates.
                if sum(self.source_status) + sum(self.queue_status) == 0:
                    # Broadcast 'stop'
                    # The stream name and stream element are both 'stop'.
                    self.process.broadcast('stop', 'stop')
                self.main_lock.release()
                # Released main_lock -------------------------------

                try:
                    v = self.input_queue.get()
                except:
                    # Something unexpected happen. So, this thread terminates.
                    # Also, tell other processes to terminate.
                    self.stopped = True
                    # msg_to_all_other_processes() is like broadcast, except
                    # that a process does not send a message to itself.
                    self.process.msg_to_all_other_processes('stop', 'stop')

                if not self.stopped:
                    # Succeeded in getting a message from input_queue.
                    # The status of this queue is not empty.
                    self.queue_status[self.process_id] = 1
                    # This message, v, is:
                    #     (stream name, element for this stream)
                    # Get the specified stream name and its next element.
                    out_stream_name, new_data_for_stream = v
                    if out_stream_name == 'source_finished':
                        # A source has finished generating values. The
                        # status of this source is set to finished, i.e. 0.
                        # Execution returns to the beginning of the while loop
                        # where the check for termination is carried out.
                        # Termination is when all sources have terminated
                        # and input queues of all processes are empty.
                        pass
                    elif out_stream_name == 'stop':
                        # This process may have broadcast 'stop' itself, and it
                        # now receives its own 'stop' message. Or, some other
                        # process broadcast ('stop', 'stop'). In either case, this
                        # process receives a 'stop' message. So stop this process.
                        self.stopped = True
                    else:
                        # This message is to be appended to the specified
                        # out_stream.
                        # Get the stream from its name
                        out_stream = self.name_to_stream[out_stream_name]
                        if out_stream_name.endswith('_signal_'):
                            out_stream.append(new_data_for_stream)
                        else:
                            out_stream.extend(new_data_for_stream)
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

#----------------------------------------------------------



        


