""" This module contains the Stream class. The
Stream and Agent classes are the building blocks
of PythonStreams.
(Version 1.0 June 16, 2016. Created by: Mani Chandy)
"""

from system_parameters import DEFAULT_NUM_IN_MEMORY,\
                             DEFAULT_MIN_HISTORY
# Import numpy and pandas if StreamArray (numpy) and StreamSeries (Pandas)
# are used.
import numpy as np
#import pandas as pd
from collections import namedtuple

import logging.handlers

# TimeAndValue is used for timed messages.
TimeAndValue = namedtuple('TimeAndValue', ['time', 'value'])

# _no_value is the message sent on a stream to indicate that no
# value is sent on the stream at that point. _no_value is used
# instead of None because you may want an agent to send a message
# with value None and for the agent receiving that message to
# take some specific action.
class _no_value(object):
    def __init__(self):
        pass

# _close is the message sent on a stream to indicate that the
# stream is closed.
class _close(object):
    def __init__(self):
        pass

# When _multivalue([x1, x2, x3,...]) is sent on a stream, the
# actual values sent are the messages x1, then x2, then x3,....
# as opposed to a single instance of the class _multivalue.
# See examples_element_wrapper for examples using _multivalue.
class _multivalue(object):
    def __init__(self, lst):
        self.lst = lst
        return

class _array(object):
    def __init__(self, value):
        self.value = value
        return
    
def remove_novalue_and_open_multivalue(l):
    """ This function returns a list which is the
    same as the input parameter l except that
    (1) _no_value elements in l are deleted and
    (2) each _multivalue element in l is opened
        i.e., for an object _multivalue(list_x)
        each element of list_x appears in the
        returned list.

    Parameter
    ---------
    l : list
        A list containing arbitrary elements
        including, possibly _no_value and
        _multi_value

    Returns : list
    -------
        Same as l with every _no_value object
        deleted and every _multivalue object
        opened up.

    Example
    -------
       l = [0, 1, _no_value, 10, _multivalue([20, 30])]
       The function returns:
           [0, 1, 10, 20, 30]

    """
    if not isinstance(l, list):
        return l
    return_list = []
    for v in l:
        if (isinstance(v, list) or
            isinstance(v, np.ndarray) or
            isinstance(v, tuple)):
            return_list.append(v)
        else:
            if v == _no_value:
                continue
            elif isinstance(v, _multivalue):
                return_list.extend(v.lst)
            else:
                return_list.append(v)
    return return_list


class Stream(object):
    """
    A stream is a sequence of values. Agents can:
    (1) Append values to the tail of stream and
    close a stream.
    (2) Read a stream.
    (3) Subscribe to be notified when a
    value is added to a stream.
    (See Agent.py for details of agents.)

    The ONLY way in which a stream can be
    modified is that values can be appended to its
    tail. The length of a stream (number of elements
    in its sequence) can stay the same or increase,
    but never decrease. If at some point, the length
    of a stream is k, then from that point onwards, the
    first k elements of the stream remain unchanged.

    A stream is written by only one agent. Any
    number of agents can read a stream, and any
    number of agents can subscribe to a stream.
    An agent can be a reader and a subscriber and
    a writer of the same stream. An agent may subscribe
    to a stream without reading the stream's values; for
    example the agent may subscribe to a clock stream
    and the agent executes a state transition when the
    the clock stream has a new value, regardless of
    the value.

    Parameters
    ----------
    name : str, optional
          name of the stream. Though the name is optional
          a named stream helps with debugging.
          default : 'NoName'
    proc_name : str, optional
          The name of the process in which this agent
          executes.
          default: 'UnknownProcess'
    initial_value : list or array, optional
          The list (or array) of initial values in the
          stream. If a stream starts in a known state, i.e.,
          with a known sequence of messages, then set the
          initial_value to this sequence.
          default : []
    num_in_memory: positive int, optional
          It is the initial value of the number of
          elements in the stream that are stored in main
          memory. If the stream has 9000 elements and
          num_in_memory is 100 then the most recent 100
          elements of the stream are stored in main memory
          and the earlier 8900 elements are stored in a file
          or discarded.
          num_in_memory may change. It increases if a reader
          is reading the i-th value of the stream and if j is
          the index of the most recent value in the stream and
          |j - i| exceeds num_in_memory.
          It may decrease if the gap between the indices
          of the most recent value in the stream and the
          earliest value being read by any agent is less than
          num_in_memory
          default : DEFAULT_NUM_IN_MEMORY
                    specified in SystemParameters.py
    min_history: non-negative int, optional
           The minimum number of elements of the stream that
           are stored in main memory.
           If min_history is 3 and the stream has 9000
           elements then the elements 8997, 8998, 8999 will
           be stored in main memory even if no agent is reading
           the stream.
           min_history is used primarily for debugging.
           A debugger may need to read early values of the stream,
           and reading from main memory is faster than reading
           from a file.
           default : DEFAULT_MIN_HISTORY
                     specified in SystemParameters.py.


    Attributes
    ----------
    recent : list or NumPy array.
          A list or array that includes the most recent values of
          the stream. This list or array is padded with default
          values (see stop).
    stop : int
          index into the list recent.
          s.recent[:s.stop] contains the s.stop most recent
          values of stream s.
          s.recent[s.stop:] contains padded values.
    offset: int
          index into the stream used to map the location of
          an element in the entire stream with the location
          of the same element in s.recent, which only
          contains the most recent elements of the stream.
          For a stream s:
                   s.recent[i] = s[i + s.offset]
                      for i in range(s.stop)
          Note: In later versions, offset will be implemented
          as a list of ints.
    start : dict of readers.
            key = reader
            value = start index of the reader
            Reader r can read the slice:
                      s.recent[s.start[r] : s.stop ]
            in s.recent which is equivalent to the following
            slice in the entire stream:
                    s[s.start[r]+s.offset: s.stop+s.offset]
            Invariant:
            For all readers r:
                        stop - start[r] <= len(recent)
            This invariant is maintained by increasing the
            size of recent when necessary.
    subscribers_set: set
             the set of subscribers for this stream.
             Subscribers are agents to be notified when an
             element is added to the stream.
    closed: boolean
             True if and only if the stream is closed.
             An exception is thrown if a value is appended to
             a closed stream.
    close_message: _close or np.NaN
            This message is appended to a stream to indicate that
            when this message is received the stream should be closed.
            If the stream is implemented as a list then close_message
            is _close, and for StreamArray the close_message is np.NaN
            (not a number).
    _begin : int
            index into the list, recent
            recent[:_begin] is not being accessed by any reader;
            therefore recent[:_begin] can be deleted from main
            memory.
            Invariant:
                    for all readers r:
                          _begin <= min(start[r])

    Notes
    -----
    1. AGENTS SUBSCRIBING TO A STREAM

    An agent is a state-transition automaton and
    the only action that an agent executes is a
    state transition. If agent x is a subscriber
    to a stream s then x.next() --- a state
    transition of x --- is invoked whenever messages
    are appended to s.

    The only point at which an agent executes a
    state transition is when a stream to which
    the agent subscribes is modified.

    An agent x subscribes to a stream s by executing
            s.call(x).
    An agent x unsubscribes from a stream s by
    executing:
            s.delete_caller(x)


    2. AGENTS READING A STREAM

    2.1 Agent registers for reading

    An agent can read a stream only after it registers
    with the stream as a reader. An agents r registers
    with a stream s by executing:
                   s.reader(r)
    An agent r deletes its registration for reading s
    by executing:
                   s.delete_reader(r)
    An agent that reads a stream is also a subscriber to
    that stream unless the agent has a call-stream. If
    an agent has no call-stream and stream s is an input
    stream of that agent, then whenever s is modified,
    the agent is told to execute a state transition.

    2.2 Slice of a stream that can be read by an agent

    At any given point, an agent r that has registered
    to read a stream s can only read some of the most
    recent values in the stream. The number of values
    that an agent can read may vary from agent to agent.
    A reader r can only read a slice:
             s[s.start[r]+s.offset: s.stop+s.offset]
    of stream s where start[r], stop and offset are
    defined later.


    3. WRITING A STREAM

    3.1 Extending a stream

    When an agent is created it is passed a list
    of streams that it can write.

    An agent adds a single element v to a stream s
    by executing:
                  s.append(v)

    An agent adds the sequence of values in a list
    l to a stream s by executing:
                   s.extend(l)
    The operations append and extend of streams are
    analogous to operations with the same names on
    lists.

    3.2 Closing a Stream

    A stream is either closed or open.
    Initially a stream is open.
    An agent that writes a stream s can
    close s by executing:
                  s.close()
    A closed stream cannot be modified.

    4. MEMORY

    4.1 The most recent values of a stream

    The most recent elements of a stream are
    stored in main memory. In addition, the
    user can specify whether all or part of
    the stream is saved to a file.

    Associated with each stream s is a list (or
    array) s.recent that includes the most
    recent elements of s. If the value of s is a
    sequence:
                  s[0], ..., s[n-1],
    at a point in a computation then at that point,
    s.recent is a list
                    s[m], .., s[n-1]
    for some m, followed by some padding (usually
    a sequence of zeroes, as described later).

    The system ensures that all readers of stream
    s only read elements of s that are in s.recent.

    4.2 Slice of a stream that can be read

    Associated with a reader r of stream s is an
    integer s.start[r]. Reader r can only read
    the slice:
               s.recent[s.start[r] : ]
    of s.recent.

    For readers r1 and r2 of a stream s the values
    s.start[r1] and s.start[r2] may be different.

    4.3 When a reader finishes reading part of a stream

    Reader r informs stream s that it will only
    read values with indexes greater than or
    equal to j in the list, recent,  by executing
                  s.set_start(r, j)
    which causes s.start[r] to be set to j.


    5. OPERATION

    5.1 Memory structure

    Associated with a stream is:
    (1) a list or NumPy darray, recent.
    (2) a nonnegative integer stop  where:
       (a) recent[ : stop] contains
           the most recent values of the stream,
       (b) the slice recent[stop:] is
           padded with padding values
           (either 0 or 0.0 or default value
           specified by the numpy data type).
    (3) a nonnegative integer s.offset where
          recent[i] = stream[i + offset]
             for 0 <= i < s.stop

    Example: if the sequence of values in  a stream
    is:
               0, 1, .., 949
    and s.offset is 900, then
       s.recent[i] = s[900+i] for i in 0, 1, ..., 49.
    and
       s.recent[i] is the default value for i > 49.

    Invariant:
              len(s) = s.offset + s.stop
    where len(s) is the number of values in stream s.

    The size of s.recent increases and decreases so
    that the length of slice that any reader may read
    is less than the length of s.recent.

    The entire stream, or the stream up to offset,
    can be saved in a file for later processing.
    You can also specify that no part of the stream
    is saved to a file.

    In the current implementation old values of the
    stream are not saved.

    5.2 Memory Management

    We illustrate memory management with the
    following example with num_in_memory=4 and
    buffer_size=1

    Assume that a point in time, for a stream s,
    the list of values in the stream is
    [1, 2, 3, 10, 20, 30]; num_in_memory=4;
    s.offset=3; s.stop=3; and
    s.recent = [10, 20, 30, 0]. 
    The length of s.recent is num_in_memory (i.e. 4).
    The s.stop (i.e. 3) most recent values in the
    stream are 10, 20, 30.
    s[3] == 10 == s.recent[0]
    s[4] == 20 == s.recent[1]
    s[5] == 30 == s.recent[2]
    The values  in s.recent[s.stop:] are padded
    values (zeroes).

    A reader r of stream s has access to the list:
      s.recent[s.start[r] : s.stop]
    Assume that s has two readers r and q where:
    s.start[r] = 1 and s.start[q] = 2.
    So agent r can read the slice [1:3] of recent which
    is the list [20, 30], and agent q can read the slice
    [2:3] of recent which is the list [30].
    An invariant is:
          0 <= s.start[r] <= s.stop
    for any reader r.

    When a value v is appended to stream s, 
    v is inserted in s.recent[s.stop], replacing a
    default value, and s.stop is incremented.
    If s.stop >= len(s.recent) then a new s.recent
    is created and the values that may be read by
    any reader are copied into the new s.recent,
    and s.start, s.stop, and s._begin are modified.

    Example: Start with the previous example.
    (Assume min_history is 0. This parameter is
    discussed in the next paragraph.)
    When a new value, 40 is appended to the stream,
    the list of values in s becomes.
    [1, 2, 3, 10, 20, 30, 40].
    s.recent becomes [10, 20, 30, 40], and
    s.stop becomes 4. Since s.stop >= len(recent), a
    new copy of recent is made and the elements that
    are being read in s are copied into the new copy.
    So, recent becomes [20, 30, 40, 0] because no
    agent is reading s[3] = 10. Then s.stop becomes 3
    and s.offset becomes 4. s.start is modified with
    s.start[r] becoming 0 and s.start[q] becoming 1,
    so that r continues to have access to values of
    the stream after 20; thus r can now read the
    list [20, 30, 40] and q can read the list [30, 40].

    At a later point, agent r informs the stream that it
    no longer needs to access elements 20, 30, 40 and
    so s.start[r] becomes 3. Later agent q informs the
    stream that it no longer needs to access element 30
    and s.start[q] becomes 2. At this point r has access
    to the list [] and q to the list [40].

    Now suppose the agent writing stream s extends the
    stream by the list [50, 60, 70, 80]. At this point,
    agent q needs to access the list [40, 50, 60, 70, 80]
    which is longer than len(recent). In this case the
    size of recent is doubled, and the new recent becomes:
    [40, 50, 60, 70, 80, 0, 0, 0], with s.start[r] = 1 and
    s.start[q] = 0. s.stop becomes 5.

    Example of min_history = 4.
    Now suppose the stream is extended by 90, 100 so
    that s.recent becomes [40, 50, 60, 70, 80, 90, 100, 0] with
    s.stop = 7. Suppose r and q inform the stream that they no
    longer need to access the elements currently in the stream, and
    so s.start[r] and s.start[q] become 7. (In this case the size of
    recent may be made smaller (halved); but, this is not done in
    the current implementation and will be done later.) Next
    suppose the stream is extended by [110]. Since r and q only need
    to read this value, all the earlier values could be deleted from
    recent; however, min_history elements must remain
    in recent and so recent becomes:
    [80, 90, 100, 110, 0, 0, 0, 0]

    """
    def __init__(self, name="NoName", proc_name="UnknownProcess",
                 initial_value=[],
                 num_in_memory=DEFAULT_NUM_IN_MEMORY,
                 min_history = DEFAULT_MIN_HISTORY):
        self.name = name
        self.proc_name = proc_name
        self.num_in_memory = num_in_memory
        self.min_history = min_history
        self._begin = 0
        self.offset = 0
        self.stop = 0
        # Initially the stream is open and has no readers or subscribers.
        self.start = dict()
        self.subscribers_set = set()
        self.closed = False
        self.close_message = _close
        self.recent = self._create_recent(num_in_memory)
        self.extend(initial_value)
        

    def reader(self, r, start_index=0):
        """
        A newly registered reader starts reading recent
        from index start, i.e., reads  recent[start_index:s.stop]
        If reader has already been registered with this stream
        its start value is updated to start_index.
        """
        self.start[r] = start_index

    def delete_reader(self, reader):
        """
        Delete this reader from this stream.
        """
        if reader in self.start:
            del self.start[reader]

    def call(self, agent):
        """
        Register a subscriber for this stream.
        """
        self.subscribers_set.add(agent)

    def delete_caller(self, agent):
        """
        Delete a subscriber for this stream.
        """
        self.subscribers_set.discard(agent)

    def append(self, value):
        """
        Append a single value to the end of the
        stream.
        """
        self.extend([value])
        return
    
    def extend(self, value_list):
        """
        Extend the stream by value_list.

        Parameters
        ----------
            value_list: list
        """
        if self.closed:
            raise Exception("Cannot write to a closed stream.")

        # Since this stream is a regular Stream (i.e.
        # implemented as a list) rather than Stream_Array
        # (which is implemented as a NumPy array), convert
        # any NumPy arrays to lists before inserting them
        # into the stream. See StreamArray for dealing with
        # streams implemented as NumPy arrays.
        if isinstance(value_list, np.ndarray):
            value_list = list(value_list)
        if isinstance(value_list, tuple):
            value_list = list(value_list)
        assert (isinstance(value_list, list)), \
          'value_list = {0}, stream = {1}. value_list is not a list'.format(
              value_list, self.name)

        if len(value_list) == 0:
            return
        
        value_list = remove_novalue_and_open_multivalue(value_list)
        
        # Deal with messages to close the stream.
        if self.close_message in value_list:
            # Since close_message is in value_list, first output
            # the messages in value_list up to and including 
            # the message close_message and then close the stream.
            # close_flag indicates that this stream must
            # be closed after close_message is output
            close_flag = True
            # Value_list is up to, but not including, close_message
            value_list = value_list[:value_list.index(self.close_message)]
        else:
            close_flag = False

        self.new_stop = self.stop + len(value_list)

        # Make a new version of self.recent if necessary
        if self.new_stop >= len(self.recent):
            self._set_up_new_recent(self.new_stop)
            
        self.recent[self.stop: self.stop + len(value_list)] = value_list
        self.stop += len(value_list)
        # Inform subscribers that the stream has been modified.
        for a in self.subscribers_set:
            a.next()

        # Close the stream if close_flag was set to True
        # because a close_message value was added to the stream.
        if close_flag:
            self.close()

    def set_name(self, name):
        self.name = name

    def print_recent(self):
        print self.name, '=', self.recent[:self.stop]

    def close(self):
        """
        Close this stream."
        """
        if self.closed:
            return
        self.closed = True

    def set_start(self, reader, starting_value):
        """ The reader tells the stream that it is only accessing
        elements of the list recent with index start or higher.

        """
        self.start[reader] = starting_value
 
    def get_latest(self):
        """ Returns the latest element in the stream.
        If the stream is empty then it returns the empty list

        """
        if self.stop == 0:
            return []
        else:
            return self.recent[self.stop - 1]

    def get_last_n(self, n):
        """
        Parameters
        ----------
        n : positive integer

        Returns
        -------
            The list of the last n elements of the stream. If the
            number of elements in the stream is less than n, then
            it returns all the elements in the stream.
        Note
        ----

             Requirement: n >= self.min_history
        """
        return self.recent[max(self.stop-n, 0) : self.stop]
    
    def get_latest_n(self, n):
        """ Same as get_last_n()

        """
        return self.get_last_n(n)

    def is_empty(self):
        """
        Returns: boolean
        -------
            True if and only if this stream is empty.

        """
        return self.stop == 0

    def get_contents_after_column_value(self, column_number, value):
        """ Assumes that the stream consists of rows where the
        number of elements in each row exceeds column_number. Also
        assumes that values in the column with index column_number
        are in increasing order.
           Returns the rows in the stream for which:
               row[column_number] >= value

        """
        assert(isinstance(column_number, int))
        assert(column_number >= 0)
        try:
            start_index = np.searchsorted(
                [row[column_number] for row in self.recent[:self.stop]], value)
            if start_index >= self.stop:
                return []
            else:
                return self.recent[start_index:self.stop]
        except:
            print 'Error In Stream.py. In get_contents_after_column_value()'
            print 'column_number =', column_number
            print 'value =', value
            raise
        return

    def get_index_for_column_value(self, column_number, value):
        """ Similar to get_contents_after_column_value except that the
        value returned is an index into recent rather than the sequence
        of rows.

        """
        assert(isinstance(column_number, int))
        try:
            start_index = np.searchsorted(
                [row[column_number] for row in self.recent[:self.stop]], value)
            if start_index >= self.stop:
                return -1
            else:
                return start_index
        except:
            print 'Error in get_index_for_column_value in Stream.py'
            print 'column_number =', column_number
            print 'value =', value
            raise
        return


    def _set_up_new_recent(self, new_stop=None):
        """
        stop for the stream will become new_stop. Since
        new_stop exceeds the length of recent, a new
        copy of recent is created. This step deletes elements
        of recent that are not accessed by any reader.
        If the number of active elements is excessive compared
        to the length of recent then the size of recent is
        increased. It the number of active elements is very small
        compared to the length of recent, the size of of
        recent may be decreased.
        
        """

        if not new_stop:
            new_stop = self.stop
        else:
            if new_stop < self.stop:
                print 'Error in Stream.py. In set_up_new_recent'
                print 'new_stop', new_stop, 'self.stop', self.stop

        self._begin = (0 if self.start == {}
                       else min(self.start.itervalues()))
        num_items_active_in_stream = new_stop - self._begin

        self.num_in_memory = len(self.recent)
        while num_items_active_in_stream >= self.num_in_memory:
            self.num_in_memory *= 2

        # new_recent becomes a list or numpy array with
        # default elements and of length self.num_in_memory.
        # Note: _create_recent() is different for
        # StreamArray.
        self.new_recent = self._create_recent(self.num_in_memory)

        # Ensure that recent contains at least min_history
        # elements.
        if num_items_active_in_stream < self.min_history:
            self._begin = max(0, new_stop - self.min_history)
            
        # Copy active values from recent into new_recent; then
        # copy new_recent into recent and then delete new_recent.
        self.new_recent[:self.stop - self._begin] = \
            self.recent[self._begin: self.stop]
        self.recent = list(self.new_recent)
        del self.new_recent

        # Maintain the invariant recent[i] = stream[i + offset]
        # by incrementing offset since messages in new_recent were
        # shifted left (earlier) from the old recent by offset
        # number of slots.
        self.offset += self._begin

        # A reader reading the value in slot l in the old recent
        # will now read the same value in slot (l - _begin) in
        # new_recent.
        for key in self.start.iterkeys():
            self.start[key] -= self._begin
        self.stop -= self._begin
        self._begin = (0 if self.start == {}
                       else min(self.start.itervalues()))
        

    def _create_recent(self, size):
        # Note: This function is different for StreamArray.
        return [0] * size

    
##########################################################
##########################################################
class StreamArray(Stream):
    def __init__(self, name="NoName", proc_name="UnknownProcess",
                 dimension=0, dtype=float, initial_value=None,
                 num_in_memory=DEFAULT_NUM_IN_MEMORY,
                 min_history = DEFAULT_MIN_HISTORY):
        """ A StreamArray is a version of Stream in which recent
        is a NumPy array. The parameters are the same as for Stream
        except for the additional ones.

        Parameters
        ----------
        dimension: a nonnegative integer, a nonempty tuple or list,
            or an array of positive integers.
        dtype: a NumPy data type

        Notes
        -----
        If dimension is 0, then:
            each element of the stream is an an element of type dtype.
            For example, if dimension is 0, and dtype is float then
            the stream is a sequence of floats.
        If dimension is a positive integer, then:
            each element of the stream is a 1-D array where the 
            length of the array is dimension. Each element of the array
            is of type, dtype.
            In this case, recent is a 2-D array whose elements are of
            type dtype, and the number of columns of recent is dimension
            and the number of rows is num_in_memory.
            We think of the stream as an infinite 2-D array where the
            number of columns is dimension and the number of rows is
            unbounded.
            For example, if dimension is 3 and dtype is float, then the
            stream is a sequence of NumPy arrays: (float, float, float)
        If dimension is a tuple or list then:
            the elements of dimension must be strictly positive integers.
            In this case, each element of the stream is an N-dimensional
            array where N is the length of the tuple, and the lengths of
            the N dimensions are the elements of the tuple. The type of
            the elements of the array is dtype.
            For example, if dimension is (2, 2) and dtype is float, then
            each element of the stream is a 2 X 2 NumPy array of floats.

        """
        
        assert(isinstance(num_in_memory, int) and num_in_memory > 0)
        assert(isinstance(min_history, int) and min_history >= 0)
        assert((isinstance(dimension, int) and dimension >=0) or
               ((isinstance(dimension, tuple) or
                isinstance(dimension, list) or
                isinstance(dimension, np.ndarray) and
                all(isinstance(v, int) and v > 0 for v in dimension)))
               )
        self.num_in_memory = num_in_memory
        self.min_history = min_history
        self.name = name
        self.proc_name = proc_name
        self.dimension = dimension
        self.dtype = dtype
        self.recent = self._create_recent(num_in_memory)
        self._begin = 0
        self.offset = 0
        self.stop = 0
        self.start = dict()
        self.subscribers_set = set()
        self.closed = False
        # The command to close the stream is np.NaN
        # which is 'not a number'
        self.close_message = np.NaN

    def _create_recent(self, size):
        """Returns an array of np.zeros of the appropriate type
        where the length of the array is size.

        """
        if self.dimension is 0:
            return np.zeros(size, self.dtype)
        elif isinstance(self.dimension, int):
            return np.zeros([size, self.dimension], self.dtype)
        else:
            # d is a tuple or list. Insert size into the zeroth
            # position of d, and return array with dimension d.
            d = list(self.dimension)
            d.insert(0, size)
            return np.zeros(d, self.dtype)


    def append(self, value):
        """
        Parameters
        ----------
            value: 1-D numpy array
               The value appended to the StreamArray

        Notes
        -----
            See self._create_recent() for a description of
            the elements of the stream.

        """
        # Handle case where lst is of type _array.
        if isinstance(value, _array):
            multidimensional_array = np.array(value.value)
            self.extend(multidimensional_array)
            return

        if self.closed:
            raise Exception("Cannot write to a closed stream.")

        # row is a single row (element) of the output stream.
        row = value

        #----------------------------------------------
        # Check the type of row.
        assert(row.dtype == self.dtype), \
            'StreamArray {0} of type {1} is being appended by'\
            ' an incompatible type {2}'.\
            format(self.name, self.dtype, row.dtype)

        # Check dimensions of the row.
        # If dimension is 0 then row must be a scalar or a user defined dtype.
        # The shape of a user defined dtype is a tuple
        # (num_rows, num_columns_1,..)
        if self.dimension == 0:
            assert(not isinstance(row, np.ndarray) or row.shape is ()), \
              'Appending StreamArray {0} which has shape (i.e. dimension) 0 '\
              ' with row {1} which has shape {2}'.format(self.name, row, row.shape)

        # If dimension is a positive integer, then row must be a 1-D
        # numpy array, where the number of elements in the row is dimension.
        if isinstance(self.dimension, int) and self.dimension > 0:
            # row.shape[0] is the number of elements in row.
            assert(isinstance(row, np.ndarray)), \
              'Appending row {0} that is not a NumPy array to StreamArray {1}'\
              ' which has dimension {2}'. format(row, self.name, self.dimension)
            assert(len(row.shape) == 1 and row.shape[0] == self.dimension),\
              'Appending row with shape {0} to a StreamArray {1}'\
              ' which has shape (i.e. dimension) {2}:'.format(row.shape, self.name, self.dimension)
            
        # If dimension is a tuple, list or array, then row is a numpy array
        # whose dimensions, row.shape, must be the same as the dimension of the stream.
        if (isinstance(self.dimension, tuple) or
            isinstance(self.dimension, list) or
            isinstance(self.dimension, np.ndarray)):
            assert(row.shape == self.dimension),\
              'Appending row with shape {0} to StreamArray {1} with dimension {2}:'.\
              format(row.shape, self.name, self.dimension)

        # Finished checking types of elements of row
        #----------------------------------------------
        
        # Append row to the stream.
        self.new_stop = self.stop + 1
        if self.new_stop >= len(self.recent):
            self._set_up_new_recent(self.new_stop)
        self.recent[self.stop] = row
        self.stop += 1
        for a in self.subscribers_set:
            a.next()


    def extend(self, lst):
        """
        See extend() for the class Stream.
        Extend the stream by an numpy ndarray.

        Parameters
        ----------
            lst: np.ndarray

        Notes
        -----
            See self._create_recent() for a description of
            the elements of the stream.

        """
        if len(lst) == 0:
            return
        if self.closed:
            raise Exception("Cannot write to a closed stream.")

        # output_array is a more suitable name than lst which
        # is suitable for Stream but not StreamArray.
        output_array = lst
        # output_array has an arbitrary (positive) number of rows.
        # Each row must be of the same type as an element of this
        # StreamArray. Each row of output_array is inserted into
        # the StreamArray.

        #----------------------------------------------
        # Check types of the rows of output_array.
        assert(isinstance(output_array, np.ndarray)),\
          'Expect extension of a numpy stream to be a numpy ndarray,'\
          'not {0}'.format(output_array)

        # Check the type of the array.
        assert(output_array.dtype == self.dtype),\
          'StreamArray {0} of type {1} is being extended with an incompatible type {2}'.\
                format(self.name, self.dtype, output_array.dtype)


        # Check dimensions of the array.
        # If dimension is 0 then output_array must be a 1-D array. Equivalently
        # the number of "columns" of this array must be 1.
        if self.dimension == 0:
            assert(len(output_array.shape) == 1),\
              'Extending StreamArray {0} which has shape (i.e. dimension) 0' \
              ' by an array with incompatible shape {1}'.\
              format(self.name, output_array.shape[1:])

        # If dimension is a positive integer, then output_array must be a 2-D
        # numpy array, where the number of columns is dimension.
        if isinstance(self.dimension, int) and self.dimension > 0:
            # output_array.shape[1] is the number of columns in output_array.
            assert(output_array.shape[1:][0] == self.dimension),\
                'Extending StreamArray {0} which has shape (i.e. dimesion) {1}'\
                ' with an array with incompatible shape {2}'.\
                format(self.name, self.dimension, output_array.shape[1:][0])
            
        # If dimension is a tuple, list or array, then output_array is a numpy array
        # whose dimensions are output_array.shape[1:].
        # The number of elements entered into the stream is output_array.shape[0:].
        # The dimension of each row of output_array must be the same as the
        # dimension of the entire stream.
        if (isinstance(self.dimension, tuple) or
            isinstance(self.dimension, list) or
            isinstance(self.dimension, np.ndarray)):
            assert(output_array.shape[1:] == self.dimension),\
                'Extending StreamArray {0} which has shape (i.e. dimesion) {1}'\
                ' with an array with incompatible shape {2}'.\
                format(self.name, self.dimension, output_array.shape[1:])

        # Finished checking types of elements of output_array
        #----------------------------------------------

        # Append output_array to the stream. Same for StreamArray and Stream classes.
        self.new_stop = self.stop + len(output_array)
        if self.new_stop >= len(self.recent):
            self._set_up_new_recent(self.new_stop)
        self.recent[self.stop: self.stop + len(output_array)] = output_array
        self.stop += len(output_array)
        for subscriber in self.subscribers_set:
            subscriber.next()

    def get_contents_after_time(self, start_time):
        try:
            start_index = np.searchsorted(self.recent[:self.stop]['time'], start_time)
            if start_index >= self.stop:
                return np.zeros(0, dtype=self.dtype)
            else:
                return self.recent[start_index:self.stop]
        except:
            print 'start_time =', start_time
            print 'self.dtype =', self.dtype
            raise

        return

class StreamTimed(StreamArray):
    def __init__(self):
        StreamArray.__init__(name)

class StreamSeries(Stream):
    def __init__(self, name=None):
        super(StreamSeries, self).__init__(name)

    def _create_recent(self, size): return pd.Series([np.nan] * size)



def main():
    #################################################
    #   TEST SUITE
    #################################################

    txyz_dtype = np.dtype([('time','int'), ('data', '3float')])

    #--------------------------------------------
    # Testing StreamArray with positive dimension
    s = StreamArray(name='s', dimension=3)
    s.append(np.zeros(3))
    assert(s.stop == 1)
    assert(np.array_equal(s.recent[s.stop], np.array([0.0, 0.0, 0.0])))
    s.extend(np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))
    
    assert(np.array_equal(s.recent[:s.stop],
                          np.array([[0.0, 0.0, 0.0],
                                    [1.0, 2.0, 3.0],
                                    [4.0, 5.0, 6.0]]
                                    )))
    
    #---------------------------------------------------------------
    # Testing StreamArray with zero dimension and user-defined dtype
    t = StreamArray(name='t', dimension=0, dtype=txyz_dtype)
    assert(t.stop == 0)
    t.append(np.array((0, [0.0, 0.0, 0.0]), dtype=txyz_dtype))
    assert(t.stop == 1)
    t.append(np.array((2, [11.0, 12.0, 13.0]), dtype=txyz_dtype))
    assert (t.stop==2)
    a =  np.array([(0, [0.0, 0.0, 0.0]),
                   (2, [11.0, 12.0, 13.0])],
                   dtype=txyz_dtype)
    assert all(t.recent[:t.stop] == a)
    t.extend(np.zeros(2, dtype=txyz_dtype))
    a = np.array([(0, [0.0, 0.0, 0.0]),
                   (2, [11.0, 12.0, 13.0]),
                   (0, [0.0, 0.0, 0.0]),
                   (0, [0.0, 0.0, 0.0])],
                   dtype=txyz_dtype)
    assert(t.stop == 4)
    assert all(t.recent[:t.stop] == a)

    #---------------------------------------------------------------
    # Testing simple Stream
    u = Stream('u')
    v = Stream('v')
    u.extend(range(4))
    assert u.recent[:u.stop] == [0, 1, 2, 3]
    v.append(10)
    v.append([40, 50])
    assert v.recent[:v.stop] == [10, [40, 50]]
    v.extend([60, 70, 80])
    assert v.recent[:v.stop] == [10, [40, 50], 60, 70, 80]

    ######################################################
    # TESTING GROWTH OF recent
    ######################################################
    import random
    # Test data for StreamArray with user-defined data type.
    test_data = np.zeros(128, dtype=txyz_dtype)
    for i in range(len(test_data)):
        test_data[i]['time']= random.randint(0, 1000)
        for j in range(3):
            test_data[i]['data'][j] = random.randint(2000, 9999)

    w = StreamArray(name='w', dimension=0, dtype=txyz_dtype,
                    num_in_memory=8, min_history=4)
    assert(len(w.recent) == 8)
    w.reader('a')
    w.reader('b')
    assert(w.start == {'a':0, 'b':0})

    # Doubling size of recent because number of active
    # elements (10) exceeds the previous size (8) of recent.
    w.extend(test_data[:10])
    assert(len(w.recent) == 16)
    assert(w.stop == 10)
    assert(all(w.recent[:10] == test_data[:10]))

    # Change start values for readers
    w.set_start('a', 10)
    assert(w.start == {'a':10, 'b':0})
    w.set_start('b', 10)
    assert(w.start == {'a':10, 'b':10})

    # Extending stream without increasing size of recent.
    w.extend(test_data[10:20])
    assert(len(w.recent) == 16)
    assert(w.stop == 10)
    assert(all(w.recent[:10] == test_data[10:20]))
    assert(w.start == {'a':0, 'b':0})

    # Extending stream and causing recent to double in size.
    w.extend(test_data[20:32])
    assert(len(w.recent) == 32)
    assert(w.stop == 22)
    assert(all(w.recent[:22] == test_data[10:32]))
    assert(w.start == {'a':0, 'b':0})

    # Extending stream and causing recent to double in size.
    w.extend(test_data[32:50])
    assert(len(w.recent) == 64)
    assert(w.stop == 40)
    assert(all(w.recent[:40] == test_data[10:50]))
    assert(w.start == {'a':0, 'b':0})

    # Extending stream without increasing size of recent.
    w.extend(test_data[50:64])
    assert(len(w.recent) == 64)
    assert(w.stop == 54)
    assert(all(w.recent[:54] == test_data[10:64]))
    assert(w.start == {'a':0, 'b':0})
    w.set_start('a', 53)
    assert(w.start == {'a':53, 'b':0})
    w.set_start('b', 54)
    assert(w.start == {'a':53, 'b':54})

    # Extending stream without increasing size of recent.
    w.extend(test_data[64:73])
    assert(len(w.recent) == 64)
    assert(w.stop == 63)
    assert(all(w.recent[:63] == test_data[10:73]))
    assert(w.start == {'a':53, 'b':54})

    # Change start values for readers
    w.set_start('a', 63)
    w.set_start('b', 62)
    assert(w.start == {'a':63, 'b':62})

    # Checking min_history
    w.extend(test_data[73:74])
    assert(len(w.recent) == 64)
    assert(w.stop == 4)
    assert(all(w.recent[:4] == test_data[70:74]))
    assert(w.start == {'a':3, 'b':2})

    # Checking append with StreamArray
    w.append(test_data[74])
    assert(len(w.recent) == 64)
    assert(w.stop == 5)
    assert(all(w.recent[:5] == test_data[70:75]))
    assert(w.start == {'a':3, 'b':2})

    ordered_test_data = np.copy(test_data)
    for i in range(len(ordered_test_data)):
        ordered_test_data[i]['time'] = i

    #------------------------------------------
    # Test helper functions: get_contents_after_column_value()
    y = StreamArray(name='y', dimension=0, dtype=txyz_dtype,
                    num_in_memory=64, min_history=4)
    y.extend(ordered_test_data[:60])
    assert(len(y.recent) == 64)
    assert(y.stop == 60)
    assert(all(y.recent[:60] == ordered_test_data[:60]))

    assert all (y.get_contents_after_column_value(column_number=0, value=50) ==
                ordered_test_data[50:60])
    assert all(y.get_contents_after_time(start_time=50) ==
               ordered_test_data[50:60])
    assert(y.get_index_for_column_value(column_number=0, value=50) ==
           50)

    #------------------------------------------
    # Test helper functions: get_last_n()
    assert all(w.get_last_n(n=2) == test_data[73:75])
    

    # TESTING regular Stream class
    x = Stream(name='x', num_in_memory=8, min_history=4)
    assert(len(x.recent) == 8)
    assert(x.stop == 0)

    # Test append
    x.append(10)
    assert(len(x.recent) == 8)
    assert(x.stop == 1)
    assert(x.recent[0] == 10)
    x.append(20)
    assert(len(x.recent) == 8)
    assert(x.stop == 2)
    assert(x.recent[:2] == [10, 20])

    # Test extend
    x.extend([30, 40])
    assert(len(x.recent) == 8)
    assert(x.stop == 4)
    assert(x.recent[:4] == [10, 20, 30, 40])
    x.extend([])
    assert(len(x.recent) == 8)
    assert(x.stop == 4)
    assert(x.recent[:4] == [10, 20, 30, 40])
    x.extend([50])
    assert(len(x.recent) == 8)
    assert(x.stop == 5)
    assert(x.recent[:5] == [10, 20, 30, 40, 50])

    x.reader('a', 3)
    x.reader('b', 4)
    assert(x.start == {'a':3, 'b':4})
    
    x.extend([1, 2, 3, 4, 5])
    assert(len(x.recent) == 8)
    assert(x.stop == 7)
    assert(x.recent[:7] == [40, 50, 1, 2, 3, 4, 5])
    assert(x.start == {'a':0, 'b':1})

    x.reader('a', 7)
    x.reader('b', 7)
    assert(x.start == {'a':7, 'b':7})

    # Test min_history
    x.append(6)
    assert(len(x.recent) == 8)
    # min_history is 4
    assert(x.stop == 4)
    assert(x.recent[:4] == [3, 4, 5, 6])
    assert(x.start == {'a':3, 'b':3})

    # Test doubling
    x.extend(range(0, 320, 10))
    assert(len(x.recent) == 64)
    assert(x.stop == 33)
    assert(x.recent[0] == 6)
    assert(x.recent[1:33] == range(0, 320, 10))

    #------------------------------------------
    # Test helper functions
    assert(x.get_last_n(n=2) == [300, 310])
    

    
    
    

if __name__ == '__main__':
    main()
