""" This module contains CallbackQueue and Stream classes.

"""
import numpy as np
from multiprocessing import Queue
import threading
import json
import queue

DEFAULT_NUM_IN_MEMORY = 64000

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# ----------------------------- CallbackQueue ---------------------------------
#------------------------------------------------------------------------------

class Scheduler(object):
    """
    Manages the queue of callback functions scheduled for execution,
    and the input queue which feeds data to streams.
    The queue of callback functions is the same as SimpleQueue except 
    that this class has a set, 
         scheduled_callbacks
    in addition to the queue of callback functions; the set
    scheduled_callbacks is used to ensure that a callback function 
    appears at most once in the queue of callback functions.

    The data input queue is fed by external sources such as sensors.
    Each item in the data input queue is a pair 
               (stream_name, stream_item)
    This stream_item is appended to the stream with name stream_name.
    The scheduler gets data from the data input queue until the queue
    becomes empty at which point the scheduler executes step() which
    continues calling all executable callback functions until none
    remain. Then the scheduler gets more data from the data input
    queue. 

    The scheduler halts if the attribute halted is set to True.

    Attributes
    ----------
    q_callbacks: queue.SimpleQueue()
       The queue of callback functions scheduled to be called.
    scheduled_callbacks: Set of functions
       A callback function is in the set if and only if it is
       in the queue, q_callbacks. This set is used to ensure
       that each callback function appears at most once in the queue.
    name_to_stream: dict
       key: stream_name
       value: stream
    input_queue: multiprocessing.Queue
       queue of input data for streams.
    halted: Boolean
       Initially False.
       Scheduler stops after halted becomes True

    """
    def __init__(self, halting_signal=None, **kwargs):
        self.q_callbacks = queue.SimpleQueue()
        self.scheduled_callbacks = set()
        self.name_to_stream = dict()
        self.halted = False
        self.input_queue = Queue()
        self.halting_signal = halting_signal
        self.kwargs = kwargs
        
    def schedule_subscriber(self, f):
        """
       Schedules execution of function f if not already scheduled.

        """
        if f not in self.scheduled_callbacks:
            self.scheduled_callbacks.add(f)
            self.q_callbacks.put(f)

    def register_stream(self, stream_name, stream):
        self.name_to_stream[stream_name] = stream
        
    def step(self):
        """
        Continues calling callback functions until there are
        none left. 

        """
        while self.scheduled_callbacks:
            f = self.q_callbacks.get()
            # Call f unless it has been deleted by delete_subscriber().
            if f in self.scheduled_callbacks:
                self.scheduled_callbacks.discard(f)
                f()


    def start(self):
        while not self.halted:
            data = json.loads(self.input_queue.get())
            stream_name, stream_item = data
            if stream_item == ['__halt__']:
                self.halted = True
                if self.halting_signal:
                    self.halting_signal(**self.kwargs)
                return
            stream = self.name_to_stream[stream_name]
            stream.extend(stream_item)
            self.step()


#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# ----------------------------- STREAM -----------------------------------------
#------------------------------------------------------------------------------

class Stream(object):
    """
    A stream is a sequence of values. Items can be appended to 
    the tail of the stream, or the stream can be extended by a
    list of items.

    If a function f is subscribed to a stream s then f is called when
    s is extended. 

    Parameters
    ----------
    name : str, optional
          name of the stream. The name helps with debugging.
    initial_value : list or array, optional
          The list (or array) of initial values in the
          stream. 
          default : []
    num_in_memory: int (positive)
          Only the most recent num_in_memory elements of the stream
          are stored; older elements are lost.
          default: DEFAULT_NUM_IN_MEMORY

    Attributes
    ----------
    recent : list or NumPy array.
          A list or array whose elements up to self.stop contain
          the most recent elements of the stream.
          recent is a buffer that is written and read by
          functions.
          len(self.recent) = num_in_memory
          recent[:stop] contains the most recent elements of
          the stream.
    stop : int
          index into the list recent.
            0 <= stop < len(self.recent)
          recent[ : stop] contains the stop most recent
          values of this stream.
    start : dict
            key = function
            value = index into recent
            For a stream s and function f:  
                s.start[f] is an index into the list s.recent
                Function f only reads stream s after s.start[f]
    offset: int (nonnegative)
          offset is an arbitrarily large integer.
          For a stream s:
            len(s) = s.offset + s.stop.
            s.recent[i] = s[i + s.offset] for i in [0 : s.stop]
    subscribers_set: set
             the set of functions who have subscribed for this stream.
             functions in this set are notified when the stream is
             modified.

    Notes
    -----
    1. SUBSCRIBING TO A STREAM

    When a stream is modified, all functions that are subscribers
    of the stream are put on a queue called q_callbacks.
    Each function in this queue is called in turn.

    Notes
    -----
    The functionality of mapping an infinite
    stream on bounded memory is implemented
    as follows.
    
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

    A function r does not read elements of the stream
    before index self.start[r]. So, no function reads
    elements of the stream before:
         min_start = min(self.start.values()
    So, only the elements of recent with indices
    between min_start and stop need to be retained
    in self.recent. These elements are shifted down
    by _set_up_next_recent() elements.
    """
    # SCHEDULER
    # The scheduler is a Class attribute. It is not an
    # object instance attribute. All instances of Stream
    # use the same scheduler.
    scheduler = Scheduler()
    
    
    def __init__(self, name='None',
                 initial_value=[],
                 num_in_memory=DEFAULT_NUM_IN_MEMORY):
        self.name = name
        self.num_in_memory = num_in_memory
        self.offset = 0
        self.stop = 0
        # Initially the stream is open and has no functions or subscribers.
        self.start = dict()
        self.subscribers_set = set()
        # The length of recent is num_in_memory.
        self.recent = [0] * self.num_in_memory
        # Register stream with scheduler
        Stream.scheduler.register_stream(stream_name=name, stream=self)
        # Set up the initial value of the stream.
        self.extend(initial_value)
        
    def subscribe(self, f, start_index=0):
        """
        The callback_function, f, subscribes to this stream.
        f is called when this stream is extended.
        When f is called, it starts reading  this stream from the 
        index start_index.
        
        """
        self.start[f] = start_index
        self.subscribers_set.add(f)
        # Schedule f for execution. When f is called, if
        # start_index = 0 at that point, then f is a no-op.
        #self.scheduler.schedule_subscriber(f)

    def delete_subscriber(self, f):
        """
        Delete function f from the set of functions that are called
        when this stream is extended.
        """
        if f in self.start:
            del self.start[f]
            self.subscribers_set.discard(f)

    def wakeup_subscribers(self):
        # Put the callback functions in subscribers set into
        # scheduler queue so that they will be woken up.
        for subscriber in self.subscribers_set:
            self.scheduler.schedule_subscriber(subscriber)

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
          'value_list = {0}, \n' \
          'stream = {1}. \n' \
          'value_list is not a list'.format(value_list, self.name)

        if len(value_list) == 0:
            return

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

    def set_start(self, f, start_index):
        """ The function tells the stream that it is only accessing
        elements of the list, recent, with index start_index or higher.

        """
        self.start[f] = start_index

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

    def _create_recent(self, size):
        # Overloaded by StreamArray
        return [0]*size

    def _set_up_next_recent(self):
        """
        This step deletes elements of recent that are
        not accessed by any function.
        
        """
        if self.start == {}:
            # If no functions are subscribed to this stream then
            # set min_start to the end of the stream. Doing so
            # says that all functions have read the entire stream.
            min_start = self.stop
        else:
            min_start = min(self.start.values())
        # We want to retain in self.recent the segment of the
        # stream from min_start to the end of the stream.
        # The number of elements that we are retaining is
        # num_retain_in_memory
        num_retain_in_memory = 1 + self.stop - min_start

        # If we want to retain more elements in memory than
        # there is space available, then we can only
        # retain elements that fill the space.
        if num_retain_in_memory > self.num_in_memory:
            num_retain_in_memory = self.num_in_memory
            
        assert num_retain_in_memory > 0
        
        # Shift the most recent num_retain_in_memory elements in
        # the stream to start of the buffer.
        num_shift = self.stop - num_retain_in_memory
        self.recent[:num_retain_in_memory] = \
          self.recent[num_shift:self.stop]
        self.offset += num_shift
        self.stop = num_retain_in_memory
        # Zero out the unused part of self.recent. This step isn't
        # necessary; however, doing so helps in debugging. If an
        # function reads a list of zeros then the function is probably
        # reading an uninitialized part of the stream.
        # This step is overloaded in StreamArray.
        self.recent[self.stop:] = self._create_recent(len(self.recent)-self.stop)

        # A function reading the value in a slot j in the old recent
        # will now read the same value in slot (j - num_shift) in the
        # next recent.
        for function in self.start.keys():
            # Update self.start[function] because of the downward shift
            # in values in the buffer, recent.
            self.start[function] -= num_shift
            if self.start[function] < 0:
                # This function was too slow and so a part of the stream
                # that this function hasn't yet read is deleted from the
                # buffer, recent. Update the number of elements lost
                # to this function.
                self.num_elements_lost[function] -= self.start[function]
                self.start[function] = 0
                
    def recent_values(self): return self.recent[:self.stop]

    
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
        self.offset = 0
        self.stop = 0
        self.start = dict()
        self.subscribers_set = set()
        # Register stream with scheduler
        Stream.scheduler.register_stream(stream_name=name, stream=self)
        if initial_value is not None: self.extend(initial_value)

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
        self.recent[self.stop:] = [0]*(len(self.recent) - self.stop)
        
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

        if type(output_array) == np.ndarray:
            if output_array.size == 0: return
        elif type(output_array) == list:
            if len(output_array) == 0: return
        else:
            if len(list(output_array)) == 0: return
        
        # output_array should be an array.
        if isinstance(output_array, list) or isinstance(output_array, tuple):
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

#------------------------------------------------------------------------------
def run(): Stream.scheduler.step()
#------------------------------------------------------------------------------

class ExternalStream(object):
    def __init__(self, name, queue):
        self.name = name
        self.queue = queue
    def extend(self, list_of_items):
        message = (self.name, list_of_items)
        json_message = json.dumps(message)
        self.queue.put(json_message)
    def append(self, item):
        self.extend([item])
    def send_halt_signal(self):
        self.append(('scheduler', 'halt'))
