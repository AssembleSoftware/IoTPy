"""
This module consists of sources. A source is a function that generates
a single stream. These functions are executed in separate threads. A
function returns the thread and the output stream that are generated.

Functions in the module:
   1. make_outstream_and_thread is a helper function used by the other
      functions in this module.   
   2. function_to_stream generates a stream whose values are specified
      by successive call to a function.
   3. file_to_stream generates a stream from a file specified by a
      file name.
   4. list_to_stream generates a stream from a list
   5. queue_to_stream generates a stream by waiting for messages to
      arrive on a queue and then appending the messages to a stream.

"""


import sys
import os
# sys.path.append(os.path.abspath("../"))

from ..agent import Agent, InList
from ..stream import Stream, StreamArray
from ..stream import _no_value, _multivalue, _close
from ..helper_functions.check_agent_parameter_types import *
from ..helper_functions.recent_values import recent_values
import random
import time
import threading
import multiprocessing

def make_outstream_and_thread(
        function, time_interval, stream_length, state,
        args, kwargs,
        run_infinite_stateless, run_infinite_stateful,
        run_finite_stateless, run_finite_stateful,
        run_push_stateless, run_push_stateful,
        out_stream=None, push=False
        ):
    """
    Helper function called by the other functions.
    Parameters
    ----------
        function: function
          This function is applied to each line read from the source and
          the result of this function is appended to the output stream.
        time_interval: float or int, time in seconds
          An element is placed on an output stream every time_interval
          seconds. (See the functions that call this one for out_stream.)
        stream_length: int (optional)
          The source terminates after stream_length values are placed
          on the output stream.
          If stream_length is None then the source function terminates
          when an exception is raised or the source has no more data.
        state: object (optional)
          The state of the function. This is a parameter of function
        args: list
          list of positional arguments of function
        kwargs: dict
          dict of keywork arguments of function
        run_infinite_stateless, run_infinite_stateful: functions
        run_finite_stateless, run_finite_stateful: functions
        run_push_stateless, run_push_stateful: functions
          Target functions of threads
        out_stream: Stream
          The output stream (default is None)
        push: boolean
          Whether the source will push values to the stream (default is False)


    This function structures creates threads and varies the target
    function for the threads for the following 6 cases:
    1. stream_length and state are None and push is False:
       target is run_infinite_stateless
    2. stream_length is None and state is not None and push is False:
       target is run_infinite_stateful
    3. stream_length is not None and state is None and push is False:
       target is run_finite_stateless
    4. stream_length is not None and state is not None and push is False:
       target is run_finite_stateful
    5. push is True and state is None:
       target is run_push_stateless
    6. push is True and state is not None:
       target is run_push_stateful


    """
    if not out_stream:
        out_stream = Stream()

    if push:
        if state == None:
            thread = threading.Thread(
                target=run_push_stateless,
                args=(out_stream, function, args, kwargs))
        else:
            thread = threading.Thread(
                target=run_push_stateful,
                args=(out_stream, function, state, args, kwargs))

    elif stream_length == None:
        if state == None:
            thread = threading.Thread(
                target=run_infinite_stateless,
                args=(out_stream, function, time_interval, args, kwargs))
        else:
            thread = threading.Thread(
                target=run_infinite_stateful,
                args=(out_stream, function, time_interval, state, args, kwargs))
        thread.daemon = True
    else:
        if state == None:
            thread = threading.Thread(
                target=run_finite_stateless,
                args=(out_stream, function, time_interval, stream_length, args, kwargs))
        else:
            thread = threading.Thread(
                target=run_finite_stateful,
                args=(out_stream, function, time_interval, stream_length, state, args, kwargs))
        thread.daemon = True
    return thread, out_stream
    

def function_to_stream(function, time_interval=0, stream_length=None,
           state=None, out_stream=None, push=False, *args, **kwargs):
    """
    Calls a function and places returned values on a stream called
    out_stream. 
    
    Parameters
    ----------
        function: function
          This function is called and the result of this function is
          appended to the output stream.
        time_interval: float or int (optional), time in seconds
          An element is placed on the output stream every time_interval
          seconds.
        stream_length: int (optional)
          function_to_stream terminates after stream_length values are
          placed on the output stream.
          If stream_length is None then function_to_stream terminates
          only when an exception is raised.
        state: object (optional)
          The state of the function; an argument of function.
        out_stream: Stream (optional)
          The output stream
        push: boolean (optional)
          Whether the source will push values to the stream
        args: list
          Positional arguments of function
        kwargs: dict
          Keyword arguments of function

    Returns: thread, out_stream
    -------
          thread: Thread.thread
             The thread created by this function. The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.
          out_stream: Stream
             The stream created by this function.

    """
    def run_infinite_stateless(out_stream, function, time_interval, args, kwargs):
        while True:
            try:
                output_increment = function(*args, **kwargs)
            except:
                break
            out_stream.append(output_increment)
            time.sleep(time_interval)
        return

    def run_infinite_stateful(out_stream, function, time_interval,
                              state, args, kwargs): 
        while True:
            try:
                output_increment, state = function(
                    state, *args, **kwargs) 
            except:
                break
            out_stream.append(output_increment)
            time.sleep(time_interval)
        return

    def run_finite_stateless(out_stream, function, time_interval, stream_length, args, kwargs):
        for _ in range(stream_length):
            try:
                output_increment = function(*args, **kwargs)
            except:
                break
            out_stream.append(output_increment)
            time.sleep(time_interval)
        return

    def run_finite_stateful(
            out_stream, function, time_interval, stream_length,
            state, args, kwargs):
        for _ in range(stream_length):
            try:
                output_increment, state = function(
                    state, *args, **kwargs) 
            except:
                print 'run_finite_stateful exception'
                break
            out_stream.append(output_increment)
            time.sleep(time_interval)
        return
    
    def run_push_stateful(out_stream, function, state, args, kwargs):
        function(out_stream, state, *args, **kwargs)
        return

    def run_push_stateless(out_stream, function, args, kwargs):
        function(out_stream, *args, **kwargs)
        return

    return make_outstream_and_thread(
        function, time_interval, stream_length, state, args, kwargs,
        run_infinite_stateless, run_infinite_stateful,
        run_finite_stateless, run_finite_stateful,
        run_push_stateless, run_push_stateful,
        out_stream, push)

            
def file_to_stream(
        function, filename, time_interval=None, stream_length=None,
        state=None, *args, **kwargs):
    
    """
    Places lines in a file on a stream.
    
    Parameters
    ----------
       function: function
          This function is applied to each line read from the file and
          the result of this function is appended to the output stream.
       filename: str
          The name of the file that is read.
       time_interval: float or int (optional)
          The next line of the file is read every time_interval seconds.
       stream_length: int (optional)
          file_to_stream terminates after stream_length values are
          placed on the output stream.
          If stream_length is None then the
          file_to_stream terminates when the entire file is read.
       state: object (optional)
          The state of the function; an argument of function.
       args: list
          Positional arguments of function
       kwargs: dict
          Keyword arguments of function

    Returns: thread, out_stream
    -------
          thread: Thread.thread
             The thread created by this function. The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.
          out_stream: Stream
             The stream created by this function.

    """
    def run_infinite_stateless(out_stream, function, time_interval,
                               args, kwargs):
        with open(filename, 'r') as input_file:
            for line in input_file:
                out_stream.append(function(line, *args, **kwargs))
                time.sleep(time_interval)
        return

    def run_infinite_stateful(out_stream, function, time_interval,
                              state, args, kwargs):
        with open(filename, 'r') as input_file:
            for line in input_file:
                out_stream.append(
                    function(line, state, *args, **kwargs)) 
                time.sleep(time_interval)
        return

    def run_finite_stateless(out_stream, function, time_interval,
                             stream_length, args, kwargs):
        num_lines_read = 0
        with open(filename, 'r') as input_file:
            for line in input_file:
                out_stream.append(function(line, *args, **kwargs))
                num_lines_read += 1
                if num_lines_read >= stream_length:
                    break
                time.sleep(time_interval)
        return

    def run_finite_stateful(out_stream, function, time_interval,
                            stream_length, state, args, kwargs):
        num_lines_read = 0
        with open(filename, 'r') as input_file:
            for line in input_file:
                out_stream.append(
                    function(line, state, *args, **kwargs))
                num_lines_read += 1
                if num_lines_read >= stream_length:
                    break
                time.sleep(time_interval)
        return

    return make_outstream_and_thread(
        function, time_interval, stream_length, state, args, kwargs,
        run_infinite_stateless, run_infinite_stateful, 
        run_finite_stateless, run_finite_stateful)
        



def list_to_stream(function, in_list, time_interval=None,
        stream_length=None, state=None, *args, **kwargs):
    """
    Places elements in a list on a stream.
    
    Parameters
    ----------
       function: function
          This function is applied to each element in the list and
          the result of this function is appended to the output stream.
       in_list: list
          The list that is read.
       out_stream: Stream
          The output stream on which messages are placed.
       time_interval: float or int (optional)
          The next line of the file is read every time_interval seconds.
       stream_length: int (optional)
          file_to_stream terminates after stream_length values are
          placed on the output stream.
          If stream_length is None then the
          file_to_stream terminates when the entire file is read.
       state: object (optional)
          The state of the function; an argument of function.
       args: list
          Positional arguments of function
       kwargs: dict
          Keyword arguments of function

    Returns: thread, out_stream
    -------
          thread: Thread.thread
             The thread created by this function. The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.
          out_stream: Stream
             The stream created by this function.

    """

    def run_infinite_stateless(out_stream, function, time_interval,
                               args, kwargs):
        for element in in_list:
            out_stream.append(function(element, *args, **kwargs))
            time.sleep(time_interval)
        return

    def run_infinite_stateful(out_stream, function, time_interval,
                              state, args, kwargs):
        for element in in_list:
            out_stream.append(
                function(element, state, *args, **kwargs)) 
            time.sleep(time_interval)
        return

    def run_finite_stateless(out_stream, function, time_interval,
                             stream_length, args, kwargs):
        num_elements_read = 0
        for element in in_list:
            out_stream.append(function(element, *args, **kwargs))
            if num_elements_read >= stream_length:
                break
            time.sleep(time_interval)
        return

    def run_finite_stateful(out_stream, function, time_interval,
                            stream_length, state, args, kwargs):
        num_elements_read = 0
        for element in in_list:
            out_stream.append(
                function(element, state, *args, **kwargs))
            if num_elements_read >= stream_length:
                break
            time.sleep(time_interval)
        return

    return make_outstream_and_thread(
        function, time_interval, stream_length, state, args, kwargs,
        run_infinite_stateless, run_infinite_stateful,
        run_finite_stateless, run_finite_stateful)


def queue_to_stream(function, queue, stop_message=None, state=None,
                    *args, **kwargs):
    """
    Reads queue and places messages it receives from the queue on a
    stream called out_stream.
    
    Parameters
    ----------
       function: function
          This function is applied to each element read from the queue
          and  the result of this function is appended to the output
          stream. 
       queue: multiprocessing.Queue or Queue.Queue
          The queue from which messages are obtained.
       stop_message: object
          When a stop_message is received from the queue the thread
          terminates execution.
       state: object (optional)
          The state of the function; an argument of function.
       args: list
          Positional arguments of function
       kwargs: dict
          Keyword arguments of function
        

    Returns: thread, out_stream
    -------
          thread: Thread.thread
             The thread created by this function. The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.
          out_stream: Stream
             The stream created by this function.

    """
    out_stream = Stream('queue to stream')
    def queue_to_stream_stateless_run(
            function, queue, out_stream, stop_message, args, kwargs):
        no_stop_message_received = True
        while no_stop_message_received:
            while not queue.empty():
                message = queue.get()
                if stop_message is not None: 
                    if message == stop_message:
                        no_stop_message_received = False
                        break
                out_stream.append(
                    function(message, *args, **kwargs))
        return
    def queue_to_stream_stateful_run(
            function, queue, out_stream, stop_message, state,
            args, kwargs): 
        no_stop_message_received = True
        while no_stop_message_received:
            while not queue.empty():
                message = queue.get()
                if stop_message is not None:
                    if message == stop_message:
                        no_stop_message_received = False
                        break
                output_element, state = function(
                    message, state, *args, **kwargs)
                out_stream.append(output_element)
        return

    if state is None:
        thread = threading.Thread(
                    target=queue_to_stream_stateless_run,
                    args=(function, queue, out_stream, stop_message,
                          args, kwargs))
    else:
        thread = threading.Thread(
                    target=queue_to_stream_stateful_run,
                    args=(function, queue, out_stream, stop_message,
                          state, args, kwargs))
    return thread, out_stream

#------------------------------------------------------------------------------------------------
#                                     TESTS
#------------------------------------------------------------------------------------------------

def test():

    # Test function_to_stream
    def clock_ticks(state, max_value=2**30):
        return state, (state+1)%max_value
    # In the following call, state = 0 and max_value = 4
    clock_thread, clock = function_to_stream(
        clock_ticks, 0.001, 16, 0, max_value=4)
    clock_thread.start()
    clock_thread.join()
    rrrr = range(4)
    for _ in range(3):
        rrrr.extend(range(4))
    assert recent_values(clock) == rrrr

    # Test file_to_stream
    with open('test_file.txt', 'a') as the_file:
        mm = 4
        for i in range(mm):
            the_file.write(str(i) + '\n')
    file_thread, file_stream = file_to_stream(
        function=int, filename='test_file.txt', time_interval=0.01)
    file_thread.start()
    file_thread.join()
    assert recent_values(file_stream) == range(mm)
    with open('test_file.txt', 'w'): pass

    def f(v, addend): return int(v)+addend
    add_constant=10
    mm = 4
    with open('test_file.txt', 'a') as the_file:
        for i in range(mm):
            the_file.write(str(i) + '\n')
    file_addend_thread, file_addend_stream = file_to_stream(
        function=f, filename='test_file.txt', time_interval=0.01, addend=add_constant)
    file_addend_thread.start()
    file_addend_thread.join()
    assert recent_values(file_addend_stream) == [
        v+add_constant for v in range(mm)]
    with open('test_file.txt', 'w'): pass

    # Test list_to_stream
    list_thread, list_stream = list_to_stream(
        function=f, in_list=range(mm), time_interval=0.01,
        addend=add_constant)
    list_thread.start()
    list_thread.join()
    assert recent_values(file_addend_stream) == recent_values(list_stream)

    # Test queue_to_stream
    import Queue
    queue = Queue.Queue()
    for i in range(mm):
        queue.put(i)
    queue.put('stop')
    queue_thread, queue_out_stream = queue_to_stream(
        function=f, queue=queue, stop_message='stop', addend=add_constant)
    queue_thread.start()
    queue_thread.join()
    assert recent_values(queue_out_stream) == recent_values(file_addend_stream)
    return

    
if __name__ == '__main__':
    test()
    
    
    
    
    

