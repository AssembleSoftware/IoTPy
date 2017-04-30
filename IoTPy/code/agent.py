""" This module contains the Agent class. The Agent
and Stream classes are the building blocks of
PythonStreams.

"""

from stream import Stream, StreamArray
from collections import namedtuple
import numpy as np

# EPSILON is a small number used to prevent division by 0
# and other numerical problems
EPSILON = 1E-12

"""
Named_Tuple
    ----------------
    InList : a named_tuple with arguments:
        list, start, stop
        An InList defines the list slice:
                   list[start:stop]
"""
InList = namedtuple('InList', ['list', 'start', 'stop'])

class Blackbox(object):
    def __init__(self, in_streams, out_streams, name):
        assert isinstance(in_streams, list) or isinstance(in_streams, tuple)
        assert isinstance(out_streams, list) or isinstance(out_streams, tuple)
        self.in_streams = in_streams
        self.out_streams = out_streams
        self.name = name

class Agent(Blackbox):
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
    input streams is modified. For performance reasons, we
    may not want the agent to execute state transitions each time
    any of its input streams is modified; we may want the agent to
    execute state transitions periodically --- for example, every
    second. In this case, the call streams will be different from
    the input streams. A call stream that has a value appended to
    it every second will cause the agent to execute a state
    transition every second.

    
    Parameters
    ----------
    in_streams : list of streams
        The list of the agent's input streams. This list may be empty.
    out_streams : list of streams
        The list of the agent's output streams. This list may be empty.
    call_streams : list of streams
        When a new value is added to a stream in this list
        a state transition is invoked.
        This the usual way (but not the only way) in which
        state transitions occur. A state transiton for an
        agent ag can also be executed by calling ag.next()
    state: object
        The state of the agent. The state is updated after
        a transition.
    transition: function
        This function is called by next() which
        is the state-transition operation for this agent.
        An agent's state transition is specified by
        its transition function.
    stream_manager : function
        Each stream has management variables, such as whether
        the stream is open or closed. After a state-transition
        the agent executes the stream_manager function
        to modify the management variables of the agent's output
        and call streams.
    name : str, optional
        name of this agent

    Attributes
    ----------
    _in_lists: list of InList
        InList defines the slice of a list.
        The j-th element of _in_lists is an InList
        that defines the slice of the j-th input stream
        that can be read by this agent in a state
        transition. For example, if
        listj = _in_lists[j].lists
        startj = _in_lists[j].start
        stopj = _in_lists[j].stop
        Then this agent can read the slice:
               listj[startj:stopj]
        of the jth input stream. This slice is a slice
        of the most recent values of the stream.
              
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
                    The agent no longer accesses elements of its input
                    streams with indices earlier (i.e. smaller) than
                    'start'.
           (iii) update data structures after the transition.

    """

    def __init__(self, in_streams, out_streams, transition,
                 state=None, call_streams=None,
                 name=None, stream_manager=None):
        assert isinstance(in_streams, list)
        assert isinstance(out_streams, list)
        assert call_streams is None or isinstance(call_streams, list)

        Blackbox.__init__(self, in_streams, out_streams, name)
        #self.in_streams = in_streams
        #self.out_streams = out_streams
        #self.name = name
        self.state = state
        self.transition = transition
        # The default (i.e. when call_streams is None) is that
        # the agent executes a state transition when any
        # of its input streams is modified. If call_streams
        # is not None, then the agent executes a state
        # transition only when one of the specified call_streams is
        # modified.
        self.call_streams = in_streams if call_streams is None \
          else call_streams
        self.stream_manager = stream_manager
        # Register this agent as a reader of its input streams.
        for s in self.in_streams:
            s.reader(self)
        # Register this agent to be called when any of its call
        # streams is extended.
        for s in self.call_streams:
            s.call(self)
        # Initially each element of in_lists is the
        # empty InList: list = [], start=stop=0
        self._in_lists = [InList([], 0, 0) for s in self.in_streams]
        self._in_lists_start_values = [0 for s in self.in_streams]
        # Initially each element of _out_lists is the empty list.
        self._out_lists = [[] for s in self.out_streams]
        # When the agent is created, it executes a state transition
        # reading the current values of its input streams. Note that
        # even though the agent's call_streams may be empty, the agent
        # executes a state transition when the agent is created.
        if call_streams is None:
            self.next()

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
            executes a state transition.

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
        result_of_transition = \
          self.transition(self._in_lists, self.state)
        self._out_lists, self.state, self._in_lists_start_values  = \
          result_of_transition
            
        #----------------------------------------------------------------
        # PART 3
        #----------------------------------------------------------------
        # Update data structures after the state transition.
        # Extend output streams with new values generated in the
        # state transition.

        # For the j-th input stream in_streams[j], inform this stream
        # that this agent will no longer read elements of the stream with
        # indices smaller than _in_lists_start_values[j].
        assert(len(self.in_streams) == len(self._in_lists_start_values)),\
          'Error in agent named {0}. The number, {1}, of input start values returned'\
          ' by a state transition must equal, {2}, the number of input streams'.\
          format(self.name, len(self._in_lists_start_values), len(self.in_streams))
        for j in range(len(self.in_streams)):
            self.in_streams[j].set_start(self, self._in_lists_start_values[j])

        # Checks
        # If a parameter is None, convert it into the empty list.
        if not self._out_lists: self._out_lists = list()
        if not self.out_streams: self.out_streams = list()
        assert len(self._out_lists) == len(self.out_streams), \
          'Error in agent named {0}. The number of output values, {1}, returned'\
          ' by a state transition must equal, {2}, the number of output streams.'\
          ' The output values are {3}'.format(
              self.name, len(self._out_lists), len(self.out_streams), self._out_lists)
        # Finished checking self._out_lists and self.out_streams

        # Put each of the output lists computed in the state
        # transition into each of the output streams.
        for j in range(len(self.out_streams)):
            self.out_streams[j].extend(self._out_lists[j])

        # Update stream management variables. 
        if self.stream_manager is not None:
            self.stream_manager(
                self.out_streams,
                self._in_lists, self._out_lists, self.state)


def main():
    def copy(list_of_in_lists, state):
        return ([in_list.list[in_list.start:in_list.stop] for in_list in list_of_in_lists],
                state, [in_list.stop for in_list in list_of_in_lists])

    input_stream_0 = Stream('input_stream_0', num_in_memory=32)
    input_stream_1 = Stream('input_stream_1', num_in_memory=32 )
    output_stream_0 = Stream('output_stream_0', num_in_memory=32)
    output_stream_1 = Stream('output_stream_1', num_in_memory=32)
    A = Agent(in_streams=[input_stream_0, input_stream_1 ],
              out_streams=[output_stream_0, output_stream_1],
              transition=copy,
              name='A')
    
    input_stream_0.extend(range(10))
    assert(output_stream_0.stop == 10)
    assert(output_stream_1.stop == 0)
    assert(output_stream_0.recent[:10] == range(10))
    assert(input_stream_0.start == {A:10})
    assert(input_stream_1.start == {A:0})

    input_stream_1.extend(range(10, 25, 1))
    assert(output_stream_0.stop == 10)
    assert(output_stream_1.stop == 15)
    assert(output_stream_0.recent[:10] == range(10))
    assert(output_stream_1.recent[:15] == range(10, 25, 1))
    assert(input_stream_0.start == {A:10})
    assert(input_stream_1.start == {A:15})


if __name__ == '__main__':
    main()
    
        
        
    
