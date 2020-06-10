""" This module contains the Agent class. The Agent
and Stream classes are the building blocks of IoTPy.

The module also contains the BasicAgent class. This
class has only two parameters: call_streams and next().
When a call_stream is modified, next() is called.

The Agent class, in contrast to BasicAgent, has an
parameter transition() which is called when a call
stream is modified. The difference between transition()
and next() is that transition operates on lists whereas
next() operates on streams.

"""
from collections import namedtuple

"""
Named_Tuple
    ----------------
    InList : a named_tuple with arguments:
        list, start, stop
        An InList defines the list slice:
                   list[start:stop]
"""
InList = namedtuple('InList', ['list', 'start', 'stop'])


class Agent(object):
    """
    An agent is an automaton: a state-transition machine.
    An agent has only one important method: the method
    next() that makes the agent execute a state transition.

    An agent has lists of:
    (1) input streams,
    (2) output streams and
    (3) call streams.
    Streams are described in Stream.py.
    
    During a state transition an agent:
    (1) May read values from its input streams. (Note that
        reading values in a stream does not change the
        stream.)
    (2) Append values to the tails of its output streams.
    (3) Change the agent's own state.

    When a call stream is modified the agent's next() method
    is called which causes the agent to execute a state transition.
    
    The default is that every input stream is also a call stream,
    i.e., the agent executes a state transition when any of its
    input streams is modified.

    You may want the agent to execute a step when some event occurs
    where the event is not a change in an input stream.
    For example, for performance reasons, we may want an agent to
    execute state transitions periodically --- for example, every
    second --- rather than when an input stream is modified.
    In this case, the call streams will be different from
    the input streams because the call streams will be the streams
    that cause the agent to be woken up. For example, a call stream
    that has a value appended to it every second will cause the agent
    to execute a state transition every second.
  
    Parameters
    ----------
    in_streams : list of streams
        The list of the agent's input streams.
        This list may be empty.
    out_streams : list of streams
        The list of the agent's output streams.
        This list may be empty.
    call_streams : list of streams
        When a new value is added to a stream in this list
        a state transition is invoked.
        This the usual way in which state transitions occur.
        A state transiton for an agent ag can also be
        executed by calling ag.next()
    state: object
        The state of the agent. The state is updated after
        a transition.
    transition: function
        This function is called by next() which
        is the state-transition operation for this agent.
        An agent's state transition is specified by
        its transition function.
    name : str, optional
        name of this agent

    Attributes
    ----------
    _in_lists: list of InList
        Recall that Inlist has fields: ['list', 'start', 'stop']
        _in_lists[j].list refers to a slice of the most recent
        values of the j-th input stream of this agent.
        The slice into self.recent of the j-th input stream
        starts at _in_lists[j].start and stops at _in_lists[j].stop.
        This agent can read the following slice of self.recent of
        the j-th input stream:
           _in_lists[j][  _in_lists[j].start :  _in_lists[j].stop  ]
        of the jth input stream. 
              
    _out_lists: list
        The j-th element of _out_lists is the list of
        values to be appended to the j-th output
        stream after the state transition.

    Methods
    -------
    next()
        Execute a state transition. The method has 3 parts:
           (i) set up the data structures to execute
               a state transition,
           (ii) call the transition function to:
                (a) get the values to be appended to output streams,
                (b) get the next state, and
                (c) update 'start' indices for each input stream.
                    A start index for a stream indicates that this
                    agent no longer accesses elements of this input
                    streams with indices earlier (i.e. smaller) than
                    'start'. So, as far as this agent is concerned,
                    elements with indices earlier than start can be
                    discarded.
           (iii) update data structures after the transition.
    Notes
    -----
    Implementation notes: The next() method of this agent is called
    when any call_stream of this agent is modified. Calling the
    next() method happens in the following way.

    Step 1.  When a call_stream is modified, the agent is placed in
    the queue, q_agents, of the ComputeEngine of this process. See
    ComputeEngine.q_agents. This queue contains agents waiting to
    execute a next() step.
    Step 2. The main compute thread of this process gets agents from
    this queue and calls next() on them. (See create_compute_thread()
    in ComputeEngine).

    """

    def __init__(self, in_streams, out_streams, transition,
                 state=None, call_streams=None,
                 name=None):

        # Check types of inputs
        assert isinstance(in_streams, list) or isinstance(in_streams, tuple)
        assert isinstance(out_streams, list) or isinstance(in_streams, tuple)
        assert (call_streams is None or isinstance(call_streams, list) or
                isinstance(in_streams, tuple))

        # Copy parameters into object attributes
        self.in_streams = in_streams
        self.out_streams = [] if out_streams is None else out_streams
        self.transition = transition
        self.state = state
        self.call_streams = call_streams
        self.name = name
        
        # The default (i.e. when call_streams is None) is that
        # the agent executes a state transition when any
        # of its input streams is modified. If call_streams
        # is not None, then the agent executes a state
        # transition only when one of the specified call_streams is
        # modified.
        self.call_streams = in_streams if call_streams is None \
          else call_streams

        # Register this agent as a reader of its input streams.
        for s in self.in_streams:
            s.register_reader(self)

        # Register this agent to be called when any of its call
        # streams is extended.
        for s in self.call_streams:
            s.register_subscriber(self)

        # Initially each element of each in_list is the
        # empty InList: list = [], start=0, stop=0
        # Initially, the agent has no visibility into any of its
        # input streams.
        self._in_lists = [InList([], 0, 0) for s in self.in_streams]

        # self._in_lists_start_values[i] is the index into the i-th
        # input stream's recent list that the agent starts reading.
        # This attribute is modified in a state transition.
        self._in_lists_start_values = [0 for s in self.in_streams]

        # Initially each element of _out_lists is the empty list.
        self._out_lists = [[] for s in self.out_streams]

    def halt(self):
        """
        The agent stops operating because it is no longer woken
        up when streams are modified.

        """
        for s in self.call_streams: s.delete_subscriber(self)

    def restart(self):
        """
        This function can be used only after the agent has been
        halted by calling halt(). The restart is nondeterministic.
        The restarted agent may re-read parts of streams that it had
        read before it was halted. Also, it may skip parts of
        streams that it hasn't read. This function is rarely used
        in most applications.

        """
        for s in self.call_streams: s.register_subscriber(self)
        self._in_lists = [InList([], 0, 0) for s in self.in_streams]
        self._in_lists_start_values = [0 for s in self.in_streams]

    def next(self, stream_name=None):
        """Execute the next state transition.

        This function does the following:
        Part 1: set up data structures for the state transition.
        Part 2: execute the state transition by calling self.transition
        Part 3: update data structures after the transition.

        This method can be called by any agent and is
        called whenever a value is appended to any
        stream in call_streams

        Parameters
        ----------
        stream_name : str, optional
            A new value was appended to the stream with name
            stream_name as a result of which this agent
            executes a state transition. The stream_name tells this
            agent the name of stream that is causing this agent
            to be woken up and execute a state transition.
            

        """
        #----------------------------------------------------------------
        # PART 1
        #----------------------------------------------------------------
        # Set up data structures, _in_lists, _out_lists, for
        # the state transition.

        # For a stream s, s.recent is the list that includes the
        # most recent values of stream s.
        # The values of s.recent[s.stop:] are arbitrary padding
        # values (0), and the the values of s.recent[:s.stop]
        # contain the s.stop most recent values of stream s.
        # s.start[self] is an index where agent self
        # will no longer access elements with indices less than
        # s.start[self]. Therefore agent self will only access the slice
        #           s.recent[s.start[self]:s.stop]
        # of stream s.
        self._in_lists = [InList(s.recent, s.start[self], s.stop)\
                          for s in self.in_streams]

        # Initially, the output lists of the agent are empty.
        # Values will be appended to these output lists during a
        # state transition.
        self._out_lists = [[] for s in self.out_streams]

        #----------------------------------------------------------------
        # PART 2
        #----------------------------------------------------------------
        # Execute the transition_function.

        # The transition function has two input parameters:
        # (1) The recent values of input streams of the agent,
        #     i.e., self._in_lists
        # (2) The state of the agent.

        # The transition function returns:
        # (1) The lists of values to be appended
        #     to its output streams (self._out_lists)
        # (2) The new state (self.state), and
        # (3) For each input stream s, the new value of s.start[self].
        #     This agent will no longer read elements of the
        #     stream with indexes less than s.start[self].

        # The result of the transition is:
        #     self.transition(self._in_lists, self.state)
        self._out_lists, self.state, self._in_lists_start_values  = \
          self.transition(self._in_lists, self.state)
            
        #----------------------------------------------------------------
        # PART 3
        #----------------------------------------------------------------
        # Update data structures after the state transition.
        # Part 3a:
        # For the j-th input stream, in_streams[j], inform this stream
        # that this agent will no longer read elements of the stream with
        # indices smaller than _in_lists_start_values[j].
        # Part 3b:
        # Extend the j-th output stream with values returned in the
        # state transition.

        # Part 3a
        assert(len(self.in_streams) == len(self._in_lists_start_values)),\
          'Error in agent named {0}. The number, {1}, of input start values returned'\
          ' by a state transition must equal, {2}, the number of input streams'.\
          format(self.name, len(self._in_lists_start_values), len(self.in_streams))
        for j in range(len(self.in_streams)):
            self.in_streams[j].set_start(self, self._in_lists_start_values[j])

        # Part 3b
        # If a parameter is None, convert it into the empty list.
        if not self._out_lists: self._out_lists = list()
        assert len(self._out_lists) == len(self.out_streams), \
          ' Error in agent named:   {0}. \n '\
          ' The number of output values returned by the agent function is:  {1}. \n' \
          ' The number of output streams is: {2}. \n' \
          ' The numbers of output values and output streams should be equal. \n'\
          ' The output streams are:  {3}. \n' \
          ' The output values are:  {4}'.format(
              self.name, len(self._out_lists), len(self.out_streams),
              [out_stream.name for out_stream in self.out_streams], self._out_lists)
        # Put each of the output lists computed in the state
        # transition into each of the output streams.
        for j in range(len(self.out_streams)):
            self.out_streams[j].extend(self._out_lists[j])

#-------------------------------------------------------------------------
class BasicAgent(Agent):
    def __init__(self, call_streams, next):
        super(BasicAgent, self).__init__(
            in_streams=[], out_streams=[], transition=None,
            call_streams=call_streams)
        self.next = next
        return
        
        
    
