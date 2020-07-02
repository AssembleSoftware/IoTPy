""" This module contains the Stream class. The
Stream and Agent classes are the building blocks
of PythonStreams.
(Version 1.5 January, 2020. Created by: K. Mani Chandy)
"""
# division is used in stream/value operations
from __future__ import division
# numpy used in StreamArray.
import numpy as np
# system_parameters is in IoTPy/IoTPy/core
from .system_parameters import DEFAULT_NUM_IN_MEMORY
# compute_engine is in IoTPy/IoTPy/core
from .compute_engine import ComputeEngine
# helper_control is in IoTPy/IoTPy/core
from .helper_control import TimeAndValue, _multivalue
from .helper_control import _no_value
from .helper_control import remove_novalue_and_open_multivalue
from .helper_control import remove_None

class Stream(object):
    """
    A stream is a sequence of values. Agents can:
    (1) Append values to the tail of stream.
    (2) Read a stream.
    (3) Subscribe to be notified when a stream is
        modified.
    (See Agent.py for details of agents.)

    An agent is either asleep (inactive)
    or awake (active). An agent sleeps until it is
    woken up by a notification from a stream to which
    the agent has subscribed.

    When an agent wakes up it executes a method called
    next(). The agent may read and write streams while it
    executes this method. When execution of the method
    terminates, the agent goes back to sleep. The method
    is called "next" because waking up the agent causes
    it to execute its next step.

    The ONLY way in which a stream can be
    modified is that values can be appended to its
    tail. The length of a stream (number of elements
    in its sequence) can stay the same or increase,
    but never decrease. If at some point, the length
    of a stream is k, then from that point onwards, the
    first k elements of the stream remain unchanged.

    Any number of agents can read or subscribe to the
    same stream. A stream can be modified by more than one
    agent; however, reasoning about the correctness of an
    application is much simpler if a stream is modified by
    exactly one agent. If a stream is modified by multiple
    agents, then values may be appended to the tail of the
    stream by different agents in a nondeterministic fashion.
    Testing nondeterministic programs is difficult because
    successive runs with the same input may produce different
    outputs. For each stream, we recommend having exactly one
    agent that writes the stream.

    An agent can reade, write and subscribe to the same stream.
    An agent may subscribe to a stream without reading the
    stream's values; for example the agent may subscribe to a clock
    stream so that the agent is woken up whenever the clock
    stream has a new value.

    The most recent values of a stream are stored either
    in a list or a NumPy array. For the NumPy array case see
    the class StreamArray.

    Parameters
    ----------
    name : str, optional
          name of the stream. The name helps with debugging.
          default : 'UnnamedStream'
    initial_value : list or array, optional
          The list (or array) of initial values in the
          stream. 
          default : []
    num_in_memory: int (positive)
          If the length of a stream is less than or equal
          to num_in_memory then readers can read the entire
          stream. If the stream length exceeds num_in_memory
          then readers of the stream can read the latest
          num_in_memory elements of the stream.
    discard_None: Boolean (optional)
          default is True
          The default is that a stream does not contain None values.
          If discard_None is True then None values are discarded from
          the stream. If discard_None is False then the stream may
          contain elements that are None.

    Attributes
    ----------
    recent : list or NumPy array.
          A list or array whose elements up to self.stop contain
          the most recent elements of the stream.
          recent is a buffer that is written and read by
          agents.
          recent[:stop] contains the most recent elements of
          the stream. The elements of recent[stop:] are garbage.
          The length of recent is: num_in_memory
    stop : int
          index into the list recent.
            0 <= stop < len(self.recent) = num_in_memory
          recent[:stop] contains the stop most recent
          values of this stream.
          recent[stop:] contains arbitrary (garbage) values.
    offset: int (nonnegative)
          recent is a list or array of a given length whereas
          a stream can grow to an arbitrary length.
          offset maps a value in a stream to a value in the buffer
          self.recent.
          For a stream s:
            s.recent[i] = s[i + s.offset] for i in range(s.stop)
          The length of a stream s (i.e. the number of elements in
          it) is s.offset + s.stop.
    start : dict
            key = reader
            value = start index of the reader
            The next element of stream s that reader r will read is: 
                     s.recent[s.start[r]]
            The usual case is that a reader r starts reading a stream s
            when the stream is created, and reads at a rate that keeps
            up with the rate that the stream is written. In this case
            r will have read s.offset + s.start[r] elements.
            If r reads s at a rate that is so slow that the size of the
            buffer, recent, is too small, then r may miss reading some
            elements in which case r will have read fewer than
            s.recent[s.start[r]] elements.
    num_elements_lost : dict
            key = reader
            value = int
            The value is the number of elements in the stream that the
            reader missed reading because a reader read slower than the
            stream was being written. If the buffer, recent, gets full
            before a reader has read the first elements of the buffer
            then these elements are over-written and the reader
            misses reading them.
    subscribers_set: set
             the set of subscribers for this stream.
             Subscribers are agents that are notified when
             the stream is modified.
             When a new subscriber r is added, s.start[r] = 0.

    Notes
    -----
    1. SUBSCRIBING TO A STREAM

    An agent is an object that implements a method next().
    If agent x is a subscriber to a stream s then x.next()
    is invoked when s is modified.

    The only reason for an agent x to subscribe to a stream is
    to be "woken up" by the call: x.next(). An agent can read
    or write a stream without subscribing for it.

    An agent x subscribes to a stream s by executing
            s.call(x).
    An agent x unsubscribes from a stream s by
    executing:
            s.delete_caller(x)

    When a stream is modified, all agents that are subscribers
    of the stream are put on a queue called the compute_engine queue.
    The compute_engine wakes up each agent in its queue in turn.

    2. READING A STREAM

    An agent can read a stream only after it registers
    with the stream as a reader. An agents r registers
    with a stream s by executing:
                   s.register_reader(r)
    An agent r deletes its registration for reading s
    by executing:
                   s.delete_reader(r)

    In most (but not all) cases, a reader r of a stream
    s wants to be woken up when s is modified. So, the
    default case is: a reader of a stream is woken up
    whenever the stream is modified. In some cases, however,
    a reader of a stream does not want to be woken up when
    the stream is modified, but wants to be woken up only
    when some other event - such as the next clock tick -
    occurs.
    
    An agent that reads a stream is also a subscriber to
    that stream unless the agent has a call-stream. 
    Default Case: an agent has no call-stream.
      In this case the agent is woken up whenever any of
      its input streams is modified.
    Non Default Case: the agent has one or more call streams.
      The agent is woken up only when one of its call
      streams is modified. If an input stream s is not a
      call stream then the agent is not woken up when s
      gets modified.

    An agent r registered to read a stream s can read
    the stream from its next value at index s.start[r]
    to the end of the stream at index s.stop.

    Reader r informs stream s that it will only
    read values with indexes greater than or
    equal to j in the list, recent,  by executing
                  s.set_start(r, j)
    which makes s.start[r] to be set to j.


    3. WRITING A STREAM

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

    Notes
    -----
    1. Implementing the functionality of mapping an
    infinite stream on finite memory.
    
    The elements of a stream are stored in the buffer
    self.recent which is a NumPy array or a list of
    fixed size num_in_memory. The most recent values
    of the stream are in self.recent[: self.stop].

    If appending values to self.recent causes self.stop
    to exceed num_in_memory, then the elements in
    self.recent are compacted so as to retain only the
    most recent values, and the earlier values are
    discarded. This is done by the function
    _set_up_next_recent().

    A reader r does not read elements of the stream
    before index self.start[r]. So, no reader reads
    elements of the stream before:
         min_start = min(self.start.values()
    So, only the elements of recent with indices
    between min_start and stop need to be retained
    in self.recent. These elements are shifted down
    by _set_up_next_recent().

    2. Waking up agents subscribing to a stream.
    When a stream is modified, the stream calls
    wakeup_subscribers() which puts the subscribing
    agents into a queue in ComputeEngine. This queue is
    called q_agents and contains agents waiting for
    execution. The main compute thread of the process
    (see create_compute_thread() in ComputeEngine)
    gets agents from this queue and calls the funcion
    next() of each agent.

    """
    # SCHEDULER
    # The scheduler is a Class attribute. It is not an
    # object instance attribute. All instances of Stream
    # use the same scheduler. Each process has its own
    # scheduler. Each process executes its computation in
    # a single thread. This computational thread takes an
    # agent from the scheduler queue and executes a step
    # of that agent.
    scheduler = ComputeEngine()
    
    def __init__(self, name="UnnamedStream", 
                 initial_value=[],
                 num_in_memory=DEFAULT_NUM_IN_MEMORY,
                 discard_None=True):
        self.name = name
        self.num_in_memory = num_in_memory
        self._begin = 0
        self.offset = 0
        self.stop = 0
        # Initially the stream is open and has no readers or subscribers.
        self.start = dict()
        self.num_elements_lost = dict()
        self.subscribers_set = set()
        # The length of recent is num_in_memory.
        self.recent = [0] * self.num_in_memory
        self.discard_None = discard_None
        # Set up the initial value of the stream.
        self.extend(initial_value)
        
    def register_reader(self, new_reader, start_index=0):
        """
        A newly registered reader starts reading  the stream from
        the point start_index.
        If reader has already been registered with this stream
        its start value is updated to start_index.
        
        """
        self.start[new_reader] = start_index
        self.num_elements_lost[new_reader] = 0

    def delete_reader(self, reader):
        """
        Delete this reader from the set of agents that read this
        stream. 
        """
        if reader in self.start:
            del self.start[reader]
        if reader in self.num_elements_lost:
            del self.num_elements_lost[reader]

    def register_subscriber(self, agent):
        """
        Register a subscriber for this stream.
        Same as call()
        """
        self.subscribers_set.add(agent)

    def delete_subscriber(self, agent):
        """
        Delete a subscriber for this stream.
        Same as delete_caller()
        """
        self.subscribers_set.discard(agent)

    def wakeup_subscribers(self):
        # Put subscribers (i.e. agents in self.subscribers_set) into
        # the compute_engine's queue. Each agents in this queue will be
        # removed from the queue and then execute a step.  
        for subscriber in self.subscribers_set:
            self.scheduler.put(subscriber)

    def append(self, value):
        """
        Append a single value to the end of the stream.

        """
        self.extend([value])
    
    def extend(self, value_list):
        """
        Extend the stream by value_list.

        Parameters
        ----------
            value_list: list
        """
        # Convert arrays and tuples into lists.
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

        # Remove _no_value from value_list, and
        # open up each _multivalue element into a list.
        value_list = remove_novalue_and_open_multivalue(value_list)
        if self.discard_None:
            # Remove None from the value_list.
            value_list = remove_None(value_list)

        # Make a new version of self.recent if the space in
        # self.recent is insufficient. 
        # This operation changes self.recent, self.stop and self.start.
        if self.stop + len(value_list) >= len(self.recent):
            # Insufficient space to store value_list.
            self._set_up_next_recent()

        # Check that this method is not putting a value_list that is
        # too large for the memory size.
        assert(self.stop+len(value_list) < len(self.recent)), \
          'memory is too small to store the stream, {0}. ' \
          ' Currently the stream has {1} elements in main memory. ' \
          ' We are now adding {2} more elements to main memory. '\
          ' The length of the buffer is only {3}. '.format(
              self.name, self.stop, len(value_list), len(self.recent))

        # Put value_list into the appropriate slice of self.recent and
        # update stop.
        self.recent[self.stop: self.stop+len(value_list)] = value_list
        self.stop = self.stop+len(value_list)
        # Inform subscribers that the stream has been modified.
        self.wakeup_subscribers()

    def set_name(self, name):
        self.name = name

    def print_recent(self):
        print('{0}  = {1}'.format(self.name, self.recent[:self.stop]))

    def set_start(self, reader, starting_value):
        """ The reader tells the stream that it is only accessing
        elements of the list, recent, with index start or higher.

        """
        self.start[reader] = starting_value
 
    def get_latest(self, default_for_empty_stream=0):
        """ Returns the latest element in the stream.
        The latest element is the most recent element put in
        the stream.
        If the stream is empty then it returns the default.

        """
        if self.stop == 0:
            return default_for_empty_stream
        else:
            return self.recent[self.stop - 1]
 
    def get_latest_index(self, default_for_empty_stream=-1):
        """ Returns the index of the latest element in the stream.
        The latest element is the most recent element put in
        the stream.
        If the stream is empty then it returns the default.

        """
        if self.stop == 0:
            return default_for_empty_stream
        else:
            return self.offset + self.stop - 1
 
    def get_earliest_index_in_memory(self, default_for_empty_stream=-1):
        """ Returns the index of the earliest element in the stream
        that is in main memory.
        If the stream is empty then it returns the default.

        """
        if self.stop == 0:
            return default_for_empty_stream
        else:
            return self.offset

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
        """
        return self.recent[max(self.stop-n, 0) : self.stop]
    
    def get_latest_n(self, n):
        """ Same as get_last_n()

        """
        return self.get_last_n(n)

    def len(self):
        """
        Returns: int
        -------
            Number of elements in the stream.

        """
        return self.stop + self.offset
        

    def is_empty(self):
        """
        Returns: boolean
        -------
            True if and only if this stream is empty,
            i.e., self.len == 0

        """
        return self.stop + self.offset == 0

    def get_elements_after_index(self, index):
        """
        Parameters
        ----------
        index: int
           index is a pointer to an element in the stream.
           (Example: stream has 38 elements, num_in_memory is
           10, and index is 35.)
        Returns
        -------
           (pointer, list)
           Case 1: if index is greater than the length of
           the stream the function returns the tuple:
             (length of stream, empty list)
           Case 2: index is less than or equal to the stream length.
           The function returns the tuple (p, l) where p
           is a pointer into the buffer, recent, and l is stream[p:].
           In the example where a stream s has 38 elements and
           index is 35, l is s[35:39].
           If this section of the stream is stored in recent[3:7] then
           p is 3.

        """
        assert isinstance(index, int)
        if index >= self.offset + self.stop:
            return (self.offset + self.stop,
                    self.recent[self.stop:self.stop])
        if index < self.offset:
            return (self.offset, self.recent[:self.stop])
        else:
            return (index, self.recent[index - self.offset: self.stop])

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
            print ('Error In Stream.py. In get_contents_after_column_value()')
            print ('column_number = {})'.format(column_number))
            print ('value =', {}).format(value)
            raise

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
            print ('Error in get_index_for_column_value in Stream.py')
            print ('column_number = {}'.format(column_number))
            print ('value =', {}).format(value)
            raise

    def _set_up_next_recent(self):
        """
        This step deletes elements of recent that are
        not accessed by any reader.
        
        """
        if self.start == {}:
            # If no agents are subscribed to this stream then
            # set min_start to the end of the stream. Doing so
            # says that all agents have read the entire stream.
            min_start = self.stop
        else:
            min_start = min(self.start.values())
        # We want to retain in self.recent the segment of the
        # stream from min_start to the end of the stream.
        # The number of elements that we are retaining is
        # num_retain_in_memory
        num_retain_in_memory = 1 + self.stop - min_start
        assert num_retain_in_memory > 0
        # If we want to retain more elements in memory than
        # there is space available, then we can only
        # retain elements that fill the space.
        if num_retain_in_memory > self.num_in_memory:
            num_retain_in_memory = self.num_in_memory 
        # Shift the most recent num_retain_in_memory elements in
        # the stream to start of the buffer.
        num_shift = self.stop - num_retain_in_memory
        self.recent[:num_retain_in_memory] = \
          self.recent[num_shift : self.stop]
        self.offset += num_shift
        self.stop = num_retain_in_memory
        # Zero out the unused part of self.recent. This step isn't
        # necessary; however, doing so helps in debugging. If an
        # agent reads a list of zeros then the agent is probably
        # reading an uninitialized part of the stream
        self.recent[self.stop:] = [0]*(len(self.recent) - self.stop)

        # A reader reading the value in a slot j in the old recent
        # will now read the same value in slot (j - num_shift) in the
        # next recent.
        for reader in self.start.keys():
            # Update self.start[reader] because of the downward shift
            # in values in the buffer, recent.
            self.start[reader] -= num_shift
            if self.start[reader] < 0:
                # This reader was too slow and so a part of the stream
                # that this reader hasn't yet read is deleted from the
                # buffer, recent. Update the number of elements lost
                # to this reader.
                self.num_elements_lost[reader] -= self.start[reader]
                self.start[reader] = 0
                
    # Operator overloading
    def operator_overload(self, another_stream, func):
        from ..agent_types.merge import zip_map
        output_stream = Stream()
        zip_map(func=func,
                in_streams=[self, another_stream],
                out_stream=output_stream)
        return output_stream

    # Overload stream operation for add
    def __add__(self, another_stream):
        def add_pair(pair): return pair[0] + pair[1]
        return self.operator_overload(another_stream, func=add_pair)

    # Overload stream operation for subtract
    def __sub__(self, another_stream):
        def subtract(pair): return pair[0] - pair[1]
        return self.operator_overload(another_stream, func=subtract)

    # Overload stream operation for multiply
    def __mul__(self, another_stream):
        def multiply(pair): return pair[0] * pair[1]
        return self.operator_overload(another_stream, func=multiply)

    # Overload stream operation for modulus.
    def __mod__(self, another_stream):
        def modulus(pair): return pair[0] % pair[1]
        return self.operator_overload(another_stream, func=modulus)

    def __div__(self, another_stream):
        def division(pair): return pair[0] / pair[1]
        return self.operator_overload(another_stream, func=division)

    def __floordiv__(self, another_stream):
        def floor_division(pair): return pair[0] // pair[1]
        return self.operator_overload(another_stream,
                                      func=floor_division)

    def __lt__(self, another_stream):
        def less_than(pair): return pair[0] < pair[1]
        return self.operator_overload(another_stream, func=less_than)

    def __le__(self, another_stream):
        def less_than_or_equal(pair): return pair[0] <= pair[1]
        return self.operator_overload(another_stream, func=less_than_or_equal)

    def __eq__(self, another_stream):
        def equality(pair): return pair[0] == pair[1]
        return self.operator_overload(another_stream, func=equality)

    def __ne__(self, another_stream):
        def inequality(pair): return pair[0] != pair[1]
        return self.operator_overload(another_stream, func=inequality)

    def __gt__(self, another_stream):
        def greater_than(pair): return pair[0] > pair[1]
        return self.operator_overload(another_stream, func=greater_than)

    def __le__(self, another_stream):
        def greater_than_or_equal(pair): return pair[0] >= pair[1]
        return self.operator_overload(another_stream, func=greater_than_or_equal)

    
#----------------------------------------------------------------------------------
#    NumPy Arrays
#----------------------------------------------------------------------------------
class StreamArray(Stream):
    def __init__(self, name="NoName",
                 dimension=0, dtype=float, initial_value=None,
                 num_in_memory=DEFAULT_NUM_IN_MEMORY):
        """
        A StreamArray is a version of Stream treated as a NumPy array.
        The buffer, recent, is a NumPy array.
        
        The parameters for StreamArray are the same as for Stream
        except that StreamArray has dimension and dtype (see below).

        Parameters
        ----------
        dimension: a nonnegative integer, or a non-empty tuple or a
            a non-empty list, or an array of positive integers.
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
            Think of the stream as an infinite 2-D array where the
            number of columns is dimension and the number of rows is
            unbounded.
            For example, if dimension is 10 and dtype is int32, then the
            stream is a 2-D NumPy array in which each row is:
            an array with 10 elements each of type 32-bit integer and
            the number of columns is arbitrarily large.
            An unbounded stream is stored in the buffer, self.recent, which
            is a 2-D array whose elements are of type dtype. The number of
            columns of self.recent is dimension and the number of rows is
            num_in_memory, and only the most recent num_in_memory elements
            of the stream are saved in main memory.
        If dimension is a tuple or list then:
            this tuple or list must be strictly positive integers.
            In this case, each element of the stream is an N-dimensional
            array where N is the length of the tuple.  The elements of
            the array are of type dtype. The size of the array is given by
            the tuple.
            For example, if dimension is (2, 2) and dtype is float, then
            each element of the stream is a 2 X 2 NumPy array of floats.

        """
        
        assert(isinstance(num_in_memory, int) and num_in_memory > 0)
        assert((isinstance(dimension, int) and dimension >=0) or
               ((isinstance(dimension, tuple) or
                isinstance(dimension, list) or
                isinstance(dimension, np.ndarray) and
                all(isinstance(v, int) and v > 0 for v in dimension)))
               )
        self.num_in_memory = num_in_memory
        self.name = name
        self.dimension = dimension
        self.dtype = dtype
        self.recent = self._create_recent(2*num_in_memory)
        self._begin = 0
        self.offset = 0
        self.stop = 0
        self.start = dict()
        self.num_elements_lost = dict()
        self.subscribers_set = set()
        if initial_value is not None:
            self.extend(initial_value)

    def _create_recent(self, size):
        """Returns an array of np.zeros of the appropriate type
        where the length of the array is size.

        """
        if self.dimension == 0:
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
            value: numpy array
               The value appended to the StreamArray

        Notes
        -----
            See self._create_recent() for a description of
            the elements of the stream.
            This function extends the stream by a single
            element, i.e, value.

        """
        # Reshape the appended value so that it fits the
        # shape of a row in the NumPy array, recent.
        new_shape = [1]
        new_shape.extend(value.shape)
        new_value = value.reshape(new_shape)
        self.extend(new_value)
        return

    def extend(self, output_array):
        """
        See extend() for the class Stream.
        Extend the stream by an numpy array.

        Parameters
        ----------
            output_array: np.array

        Notes
        -----
            See self._create_recent() for a description of
            the elements of the stream.

        """

        if len(output_array) == 0:
            return
        
        # output_array should be an array.
        if isinstance(output_array, list) or isinstance(output_array, tuple):
            output_array = remove_novalue_and_open_multivalue(output_array)
            output_array = np.array(output_array)

        assert(isinstance(output_array, np.ndarray)), 'Exending stream array, {0}, ' \
        ' with an object, {1}, that is not an array.'.format(
            self.name, output_array)

        # output_array has an arbitrary (positive) number of rows.
        # Each row must be of the same type as an element of this
        # StreamArray. Each row of output_array is inserted into
        # the StreamArray.

        #----------------------------------------------
        # Check types of the rows of output_array.
        assert(isinstance(output_array, np.ndarray)),\
          'Expect extension of a numpy stream, {0}, to be a numpy array,'\
          'not {1}'.format(self.name, output_array)

        # Check the type of the output array.
        assert(output_array.dtype  == self.dtype),\
          'StreamArray {0} of type {1} is being extended by {2}' \
          ' which has an incompatible type {3}'.format(
              self.name, self.dtype, output_array, output_array.dtype)

        # Check dimensions of the array.
        # If dimension is 0 then output_array must be a 1-D array. Equivalently
        # the number of "columns" of this array must be 1.
        #if self.dimension == 0:
        if self.dimension == 0 or self.dimension == 1:
            assert(len(output_array.shape) == 1),\
              'Extending StreamArray {0} which has shape (i.e. dimension) 0' \
              ' by an array with incompatible shape {1}'.\
              format(self.name, output_array.shape[1:])

        ## If dimension is a positive integer, then output_array must be a 2-D
        # If dimension is 2 or higher, then output_array must be a 2-D
        # numpy array, where the number of columns is dimension.
        if isinstance(self.dimension, int) and self.dimension > 1:
            # output_array.shape[1] is the number of columns in output_array.
            assert (len(output_array.shape) > 0), \
              'Extending StreamArray {0} which has shape (i.e. dimesion) {1}'\
                ' with an array with incompatible shape {2}'.\
                format(self.name, self.dimension, output_array.shape)
            assert (len(output_array.shape[1:]) > 0), \
              'Extending StreamArray {0} which has shape (i.e. dimesion) {1}'\
                ' with an array with incompatible shape {2}'.\
                format(self.name, self.dimension, output_array.shape[1])
            assert (output_array.shape[1:][0] == self.dimension),\
                'Extending StreamArray {0} which has shape (i.e. dimension) {1}'\
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
        if self.stop + len(output_array) >= len(self.recent):
            self._set_up_next_recent()
        self.recent[self.stop: self.stop+len(output_array)] = output_array
        self.stop += len(output_array)
        self.wakeup_subscribers()
        ## for subscriber in self.subscribers_set:
        ##     subscriber.next()

    def length(self):
        return self.offset + self.stop

    def get_contents_after_time(self, start_time):
        try:
            start_index = np.searchsorted(self.recent[:self.stop]['time'], start_time)
            if start_index >= self.stop:
                return np.zeros(0, dtype=self.dtype)
            else:
                return self.recent[start_index:self.stop]
        except:
            print ('start_time ='.format(start_time))
            print ('self.dtype ='.format(self.dtype))
            raise
        return

    # Operator overloading for addition, subtraction, multiplication.
    def operator_overload(self, another_stream, func):
        from ..agent_types.merge import merge_list
        assert another_stream.dimension == self.dimension, \
          'Both stream arrays must have the same dimension.' \
          'The dimensions are {0} and {1}'.format(
              self.dimension, another_stream.dimension)
        assert another_stream.dtype == self.dtype, \
          'Both stream arrays must have the same dtype. \n' \
          'self.dtype = {0}. \n' \
          'other_stream.dtype = {1}. \n' \
          'self.name = {2}. \n' \
          'other_stream.name = {3}' .format(
              self.dtype, another_stream.dtype, self.name, another_stream.name)
        output_stream = StreamArray(dimension=self.dimension, dtype=self.dtype)
        merge_list(func=func,
                in_streams=[self, another_stream],
                out_stream=output_stream)
        return output_stream
        
    def __add__(self, another_stream):
        def add_pair(pair): return pair[0] + pair[1]
        return self.operator_overload(another_stream, func=add_pair)

    def __sub__(self, another_stream):
        def sub_pair(pair): return pair[0] - pair[1]
        return self.operator_overload(another_stream, func=sub_pair)

    def __mul__(self, another_stream):
        def mul_pair(pair): return pair[0] * pair[1]
        return self.operator_overload(another_stream, func=mul_pair)


#------------------------------------------------------------------------------
def run(): Stream.scheduler.step()
#------------------------------------------------------------------------------
