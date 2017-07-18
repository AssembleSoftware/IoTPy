""" This module contains the Stream class. The
Stream and Agent classes are the building blocks
of PythonStreams.
(Version 1.3 July 11, 2017. Created by: Mani Chandy)
"""

from system_parameters import DEFAULT_NUM_IN_MEMORY
import numpy as np
from collections import namedtuple
import Queue
import logging.handlers
import threading
from compute_engine import compute_engine

# TimeAndValue is used for timed messages.
# When using NumPy arrays, use an array whose first column
# is a timestamp, and don't use TimeAndValue.
TimeAndValue = namedtuple('TimeAndValue', ['time', 'value'])

class _no_value(object):
    """
    _no_value is the message sent on a stream to indicate that no
    value is sent on the stream at that point. _no_value is used
    instead of None because you may want an agent to send a message
    with value None and for the agent receiving that message to
    take some specific action.

    """
    def __init__(self):
        pass


class _multivalue(object):
    """
    When _multivalue([x1, x2, x3,...]) is sent on a stream, the
    actual values sent are the messages x1, then x2, then x3,....
    as opposed to a single instance of the class _multivalue.
    See examples_element_wrapper for examples using _multivalue.

    """
    def __init__(self, lst):
        self.lst = lst
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

    Any number of agents can read, write or subscribe
    to the same stream. An agent can reade, write and
    subscribe to the same stream. An agent may subscribe
    to a stream without reading the stream's values; for
    example the agent may subscribe to a clock stream
    so that the agent is woken up whenever the clock
    stream has a new value.

    The most recent values of a stream are stored either
    in a list or a NumPy array. For the array case see
    the class StreamArray.

    Parameters
    ----------
    name : str, optional
          name of the stream. Though the name is optional
          a name helps with debugging.
          default : 'NoName'
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

    Attributes
    ----------
    recent : list or NumPy array.
          A list or array whose elements up to stop contain
          the most recent elements of the stream.
          recent is a buffer that is written and read by
          agents.
          recent[:stop] contains the most recent elements of
          the stream. The elements of recent[stop:] are garbage.
          The length of recent is: 2*num_in_memory
          Twice num_in_memory is used for reasons explained
          in the implementation.
    stop : int
          index into the list recent.
                     0 <= s.stop < len(s.recent)
          s.recent[:s.stop] contains the s.stop most recent
          values of stream s.
          s.recent[s.stop:] contains arbitrary (garbage) values.
          The length of a stream is the number of elements in it.
          If the length of stream s is more than num_in_memory
          then:   s.stop >= s.num_in_memory
          else s.stop is the length of the stream.
    offset: int (nonnegative)
          recent is a list or array of a given length whereas
          a stream can grow to an arbitrary length.
          offset maps a value in a stream to a value in recent.
          For a stream s:
                   s.recent[i] = s[i + s.offset]
                      for i in range(s.stop)
          The length of a stream s (i.e. the number of elements in
          it) is s.offset + s.stop.
    start : dict
            key = reader
            value = start index of the reader
            The next element of stream s that reader r will read is
            in: 
                     s.recent[s.start[r]]
            The usual case is that a reader r starts reading a stream s
            when the stream is created, and reads at a rate that keeps
            up with the rate that the stream is written. In this case
            r will have read s.offset + s.start[r] elements.
            If r reads s at a rate that is so slow that the size of the
            buffer, recent, is too small, then r may miss reading some
            elements.
    num_elements_lost : dict
            key = reader
            value = int
            The value is the number of elements in the stream that the
            reader missed reading because it read slower than the stream
            was being written. If the buffer, recent, gets full
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
                   s.reader(r)
    An agent r deletes its registration for reading s
    by executing:
                   s.delete_reader(r)

    In most (but not all) cases, a reader r of a stream
    s wants to be woken up when s is modified. So, the
    default case is when a reader of a stream is woken
    up when the stream is modified. In some cases, however,
    a reader of a stream does not want to be woken up when
    the stream is modified, but wants to be woken up only
    when some other event - such as the next clock tick -
    occurs.
    
    An agent that reads a stream is also a subscriber to
    that stream unless the agent has a call-stream. 
    Default: an agent has no call-stream.
      In this case the agent is woken up whenever any of
      its input streams is modified.
    Case: the agent has one or more call streams.
      The agent is woken up only when one of its call
      streams is modified. 

    An agent r registered to read a stream s can read
    the stream from its next value at index s.start[r]
    to the end of the stream at index s.stop.

    Reader r informs stream s that it will only
    read values with indexes greater than or
    equal to j in the list, recent,  by executing
                  s.set_start(r, j)
    which causes s.start[r] to be set to j.


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


    """
    def __init__(self, name="NoName", 
                 initial_value=[],
                 num_in_memory=DEFAULT_NUM_IN_MEMORY):
        self.lock = threading.RLock()
        self.name = name
        self.num_in_memory = num_in_memory
        self._begin = 0
        self.offset = 0
        self.stop = 0
        # Initially the stream is open and has no readers or subscribers.
        self.start = dict()
        self.num_elements_lost = dict()
        self.subscribers_set = set()
        # The length of recent is twice num_in_memory because of the
        # way data in recent is compacted. See _set_up_next_recent()
        self.recent = [0] * (2*self.num_in_memory)
        self.extend(initial_value)
        

    def register_reader(self, r, start_index=0):
        """
        A newly registered reader starts reading recent
        from index start, i.e., reads  recent[start_index:s.stop]
        If reader has already been registered with this stream
        its start value is updated to start_index.
        
        """
        self.start[r] = start_index
        self.num_elements_lost[r] = 0

    def delete_reader(self, reader):
        """
        Delete this reader from this stream.
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

    def wakeup_subscribers(self):
        # Put subscribers into the compute_engine's
        # queue. The agents in this queue will
        # be woken up later.
        for subscriber in self.subscribers_set:
            compute_engine.put(subscriber)

    def append(self, value):
        """
        Append a single value to the end of the
        stream.
        """
        self.recent[self.stop] = value
        self.stop += 1
        # If the buffer, self.recent, becomes full
        # then compact the buffer.
        if self.stop >= len(self.recent):
            self._set_up_next_recent()
        # Inform subscribers that the stream has been modified.
        self.wakeup_subscribers()

    
    def extend(self, value_list):
        """
        Extend the stream by value_list.

        Parameters
        ----------
            value_list: list
        """
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

        # Make a new version of self.recent if the space in
        # self.recent is insufficient.
        # This operation changes self.recent, self.stop and self.start.
        if self.stop + len(value_list) >= len(self.recent):
            self._set_up_next_recent()

        assert(self.stop+len(value_list) < len(self.recent)), \
          'num_in_memory is too small to store the stream, {0}. ' \
          ' Currently the stream has {1} elements in main memory. ' \
          ' We are now adding {2} more elements to main memory. '\
          ' The length of the buffer, recent, is only {3}. '.format(
              self.name, self.stop, len(value_list), len(self.recent))

        # Put value_list into the appropriate slice of self.recent.
        self.recent[self.stop: self.stop+len(value_list)] = value_list
        self.stop = self.stop+len(value_list)
        # Inform subscribers that the stream has been modified.
        self.wakeup_subscribers()

    def set_name(self, name):
        self.name = name

    def print_recent(self):
        print self.name, '=', self.recent[:self.stop]

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
        return self.stop + self.offset == 0

    def get_elements_after_index(self, index):
        """
        index is a pointer to an element in the stream.
        (Example: stream has 38 elements, num_in_memory is
        10, and index is 35.)
        Case 1: if index is greater than the length of
        the stream the function returns the tuple:
          (length of stream, empty list)
        Case 2: index is at most the stream length.
        The function returns the tuple (p, l) where p
        is a pointer into the stream and l is stream[p:].
        p is the max of index and the index of the earliest
        element of the stream in main memory.

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
            print 'Error In Stream.py. In get_contents_after_column_value()'
            print 'column_number =', column_number
            print 'value =', value
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
            print 'Error in get_index_for_column_value in Stream.py'
            print 'column_number =', column_number
            print 'value =', value
            raise

    def _set_up_next_recent(self):
        """
        This step deletes elements of recent that are
        not accessed by any reader.
        
        """
        # Shift the self.num_in_memory latest elements to the
        # beginning of self.recent.
        assert self.stop >= self.num_in_memory
        self.recent[:self.num_in_memory] = \
            self.recent[self.stop - self.num_in_memory : self.stop]
        self.stop = self.num_in_memory
        self.offset += self.num_in_memory

        # A reader reading the value in a slot j in the old recent
        # will now read the same value in slot (j - num_in_memory) in the
        # next recent. A reader who is slower than writers of
        # the stream and is reading more than num_in_memory elements 
        # behind the last element written will miss some elements.
        for reader in self.start.iterkeys():
            self.start[reader] -= self.num_in_memory
            if self.start[reader] < 0:
                self.num_elements_lost[reader] -= self.start[reader]
                self.start[reader] = 0


    
##########################################################
##########################################################
class StreamArray(Stream):
    def __init__(self, name="NoName",
                 dimension=0, dtype=float, initial_value=None,
                 num_in_memory=DEFAULT_NUM_IN_MEMORY):
        """ A StreamArray is a version of Stream in which recent
        is a NumPy array. The parameters are the same as for Stream
        except for dimension and dtype (see below).

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
            In this case, self.recent is a 2-D array whose elements are of
            type dtype, and the number of columns of self.recent is dimension
            and the number of rows is num_in_memory.
            We think of the stream as an infinite 2-D array where the
            number of columns is dimension and the number of rows is
            unbounded.
            For example, if dimension is 3 and dtype is float, then the
            stream is a 2-D NumPy array in which each row is:
            (float, float, float)
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
        assert((isinstance(dimension, int) and dimension >=0) or
               ((isinstance(dimension, tuple) or
                isinstance(dimension, list) or
                isinstance(dimension, np.ndarray) and
                all(isinstance(v, int) and v > 0 for v in dimension)))
               )
        self.lock = threading.RLock()
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
            value: numpy array
               The value appended to the StreamArray

        Notes
        -----
            See self._create_recent() for a description of
            the elements of the stream.

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
        Extend the stream by an numpy ndarray.

        Parameters
        ----------
            output_array: np.ndarray

        Notes
        -----
            See self._create_recent() for a description of
            the elements of the stream.

        """
        # output_array should be an array.
        if isinstance(output_array, list) or isinstance(output_array, tuple):
            output_array = remove_novalue_and_open_multivalue(output_array)
            output_array = np.array(output_array)

        assert(isinstance(output_array, np.ndarray)), 'Exending stream array, {0}, ' \
        ' with an object, {1}, that is not an array.'.format(
            self.name, output_array)

        if len(output_array) == 0:
            return

        # output_array has an arbitrary (positive) number of rows.
        # Each row must be of the same type as an element of this
        # StreamArray. Each row of output_array is inserted into
        # the StreamArray.

        #----------------------------------------------
        # Check types of the rows of output_array.
        assert(isinstance(output_array, np.ndarray)),\
          'Expect extension of a numpy stream, {0}, to be a numpy ndarray,'\
          'not {1}'.format(self.name, output_array)

        # Check the type of the output array.
        assert(output_array.dtype  == self.dtype),\
          'StreamArray {0} of type {1} is being extended by {2}' \
          ' which has an incompatible type {3}'.format(
              self.name, self.dtype, output_array, output_array.dtype)

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
            print 'start_time =', start_time
            print 'self.dtype =', self.dtype
            raise

        return



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

    #------------------------------------------
    # Test helper functions: get_contents_after_column_value()
    y = StreamArray(name='y', dimension=0, dtype=txyz_dtype,
                    num_in_memory=64)
    
    # Test data for StreamArray with user-defined data type.
    test_data = np.zeros(128, dtype=txyz_dtype)
    import random
    for i in range(len(test_data)):
        test_data[i]['time']= random.randint(0, 1000)
        for j in range(3):
            test_data[i]['data'][j] = random.randint(2000, 9999)
    ordered_test_data = np.copy(test_data)
    for i in range(len(ordered_test_data)):
        ordered_test_data[i]['time'] = i
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
    # TESTING regular Stream class
    x = Stream(name='x', num_in_memory=8)
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

    #------------------------------------------
    # Test helper functions
    assert(x.get_last_n(n=2) == [4, 5])

if __name__ == '__main__':
    main()
