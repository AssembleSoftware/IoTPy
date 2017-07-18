"""
This module consists of sources. A source is a function that generates
a single stream. These functions are executed in separate threads. A
function returns the thread and the output stream that are generated.

Functions in the module:  
   1. function_to_stream generates a stream whose values are specified
      by successive call to a function.
   2. file_to_stream generates a stream from a file specified by a
      file name.
   3. list_to_stream generates a stream from a list
   4. queue_to_stream generates a stream by waiting for messages to
      arrive on a queue and then appending the messages to a stream.

Agents in the module:  
   1. function_source is the agent that returns function_to_stream.
   2. file_source is the agent that returns file_to_stream
   3. list_source is the agent that returns list_to_stream
   4. queue_source is the agent that returns queue_to_stream
"""


import sys
import os
sys.path.append(os.path.abspath("../"))

from agent import Agent, InList
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from helper_functions.check_agent_parameter_types import *
from helper_functions.recent_values import recent_values
from sink import stream_to_list

import random
import time
import threading
import multiprocessing
from compute_engine import source_queue, _stop_compute_engine, compute_engine


def function_source(
        function, out_stream, time_interval=0, num_steps=None, window_size=1,
        state=None, *args, **kwargs):

    """
    Calls a function and places values returned by the function on the stream
    out_stream. 
    
    Parameters
    ----------
       function: function
          This function is called and the result of this function is
          appended to the out_stream.
       out_stream: Stream
          The output stream to which elements are appended.
       time_interval: float or int (optional), time in seconds
          An element is placed on the output stream every time_interval
          seconds.
       num_steps: int (optional)
          function_to_stream terminates after num_steps number of steps.
          At each step a window_size number of elements is placed on the
          out_stream.
          If num_steps is None then function_to_stream terminates
          only when an exception is raised.
       window_size: int (optional)
          At each step a window_size number of elements is placed on the
          out_stream.
       state: object (optional)
          The state of the function; an argument of the parameter function
          of function_source.
       args: list
          Positional arguments of function
       kwargs: dict
          Keyword arguments of function

    Returns: thread
    -------
          thread: Thread.thread
             The thread created by this function. The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.


    """

    def thread_target(
            function, out_stream, time_interval, num_steps, window_size,
            state, args, kwargs):
        """
        This is the function executed by the thread.
        """

        #-----------------------------------------------------------------
        def get_output_list_and_next_state(state):
            """
            This function returns a list of length window_size and the
            next state.

            Parameters
            ----------
               state is the current state of the agent.
            Returns
            -------
               output_list: list
                 list of length window_size
               next_state: object
                 The next state after output_list is created.

            """
            output_list = []
            next_state = state
            # Compute the output list of length window_size
            for _ in range(window_size):
                if next_state is not None:
                    try:
                        output_increment, next_state = function(
                                next_state, *args, **kwargs)
                    except:
                        raise RuntimeError(
                            'function {0} with state {1}, positional args {2}, and keyword args {3}'.format(
                                function.__name__, next_state, args, kwargs))
                else:
                    try:
                        output_increment = function(*args, **kwargs)
                        next_state = None
                    except:
                        raise RuntimeError(
                            'function {0} with positional args {1}, and keyword args {2}'.format(
                                function.__name__, args, kwargs))
                output_list.append(output_increment)
            # Finished computing output_list of length window_size
            return output_list, next_state
        #-----------------------------------------------------------------

        if num_steps is None:
            while True:
                output_list, state = get_output_list_and_next_state(state)
                source_queue.put((out_stream, output_list))
                time.sleep(time_interval)
        else:
            for _ in range(num_steps):
                output_list, state = get_output_list_and_next_state(state)
                source_queue.put((out_stream, output_list))
                time.sleep(time_interval)
        return

    return threading.Thread(
        target=thread_target,
        args=(function, out_stream, time_interval, num_steps,
              window_size, state, args, kwargs))



def function_to_stream(
        function, time_interval=0, num_steps=None, window_size=1,
        state=None, *args, **kwargs):
    """
    Calls function and places returned values on an output stream
    created by function_to_stream.
    function_to_stream is the same as function_source except that
    function_to_stream creates and returns out_stream whereas
    out_stream is an input parameter of function_source.
    
    Parameters
    ----------
       function: function
          This function is called and the result of this function is
          appended to the out_stream.
       time_interval: float or int (optional), time in seconds
          An element is placed on the output stream every time_interval
          seconds.
       num_steps: int (optional)
          function_to_stream terminates after num_steps number of steps.
          At each step a window_size number of elements is placed on the
          out_stream.
          If num_steps is None then function_to_stream terminates
          only when an exception is raised.
       window_size: int (optional)
          At each step a window_size number of elements is placed on the
          out_stream.
       state: object (optional)
          The state of the function; an argument of the parameter function
          of function_source.
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
             The stream of values returned by calling function.


    """
    out_stream = Stream('function_to_stream')
    thread = function_source(
        function, out_stream, time_interval, num_steps, window_size,
        state, *args, **kwargs)
    return thread, out_stream


            
def file_source(
        function, out_stream, filename, time_interval=0,
        num_steps=None, window_size=1,
        state=None, *args, **kwargs):
    
    """
    Places lines in a file on a stream.
    
    Parameters
    ----------
       function: function
          This function is applied to each line read from the file and
          the result of this function is appended to the output stream.
       out_stream: Stream
          The output stream to which elements are appended.
       filename: str
          The name of the file that is read.
       time_interval: float or int (optional)
          The next line of the file is read every time_interval seconds.
       num_steps: int (optional)
          file_to_stream terminates after num_steps taken.
          If num_steps is None then the
          file_to_stream terminates when the entire file is read.
        window_size: int (optional)
          At each step, window_size number of lines are read from the
          file and placed on out_stream after function is applied to them.
       state: object (optional)
          The state of the function; an argument of function.
       args: list
          Positional arguments of function
       kwargs: dict
          Keyword arguments of function

    Returns: thread
    -------
          thread: Thread.thread
             The thread created by this function. The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.

    """

        #-----------------------------------------------------------------

    def thread_target(function, out_stream, filename, time_interval,
                      num_steps, window_size, state, args, kwargs):
        """
        This is the function executed by the thread.
        
        """
        num_lines_read_in_current_window = 0
        num_steps_taken = 0
        output_list_for_current_window = []
        with open(filename, 'r') as input_file:
            for line in input_file:
                # Append to the output list for the current window
                # the incremental output returned by a function call.
                # The function is passed the current line from the
                # file as an argument and the function returns the
                # increment and the next state.
                if state is not None:
                    output_increment, state = function(line, state, *args, **kwargs)
                else:
                    output_increment = function(line, *args, **kwargs)
                output_list_for_current_window.append(output_increment)
                num_lines_read_in_current_window += 1
                if num_lines_read_in_current_window >= window_size:
                    # Extend out_stream with the entire window and
                    # then re-initialize the window, and finally sleep.
                    source_queue.put((out_stream, output_list_for_current_window))
                    num_lines_read_in_current_window = 0
                    output_list_for_current_window = []
                    time.sleep(time_interval)
                    num_steps_taken += 1
                if num_steps is not None and num_steps_taken >= num_steps:
                    break
        return
    thread = threading.Thread(
        target=thread_target,
        args=(function, out_stream, filename, time_interval,
                      num_steps, window_size, state, args, kwargs))
    return thread
        
def file_to_stream(
        function, filename, time_interval=0, num_steps=None, window_size=1,
        state=None, *args, **kwargs):
    out_stream = Stream('function_to_stream')
    thread = file_source(
        function, out_stream, filename, time_interval, num_steps, window_size,
        state, *args, **kwargs)
    return thread, out_stream


def list_source(function, out_stream, in_list, time_interval=None,
                num_steps=None, window_size=1, state=None, *args, **kwargs):
    
    """
    Places elements in the list, in_list, on the stream, out_stream.
    
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
       num_steps: int (optional)
          file_to_stream terminates after num_steps values are
          placed on the output stream.
          If num_steps is None then the
          file_to_stream terminates when the entire file is read.
       state: object (optional)
          The state of the function; an argument of function.
       args: list
          Positional arguments of function
       kwargs: dict
          Keyword arguments of function

    Returns: thread
    -------
          thread: Thread.thread
             The thread created by this function. The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.

    """
    def thread_target(
            function, out_stream, in_list, time_interval,
            num_steps, window_size, state, args, kwargs):

        num_elements_read_in_current_window = 0
        num_steps_taken = 0
        output_list_for_current_window = []
        for element in in_list:
            # Append to the output list for the current window
            # the incremental output returned by a function call.
            # The function is passed the current element from
            # in_list as an argument and the function returns the
            # increment and the next state.
            if state is not None:
                output_increment, state = function(element, state, *args, **kwargs)
            else:
                output_increment = function(element, *args, **kwargs)
            output_list_for_current_window.append(output_increment)
            num_elements_read_in_current_window += 1
            if num_elements_read_in_current_window >= window_size:
                # Extend out_stream with the entire window and
                # then re-initialize the window, and finally sleep.
                source_queue.put((out_stream, output_list_for_current_window))
                num_elements_read_in_current_window = 0
                output_list_for_current_window = []
                if time_interval is not None:
                    time.sleep(time_interval)       
                num_steps_taken += 1
            if num_steps is not None and num_steps_taken >= num_steps:
                break
        return

    return threading.Thread(
        target=thread_target,
        args=(function, out_stream, in_list, time_interval,
              num_steps, window_size, state, args, kwargs))


def list_to_stream(function, in_list, time_interval=None,
        num_steps=None, window_size=1, state=None, *args, **kwargs):
    """
    Places elements in a list on a stream.
    
    Parameters
    ----------
       function: function
          This function is applied to each element in the list and
          the result of this function is appended to the output stream.
       in_list: list
          The list that is read.
       time_interval: float or int (optional)
          The next line of the file is read every time_interval seconds.
       num_steps: int (optional)
          file_to_stream terminates after num_steps values are
          placed on the output stream.
          If num_steps is None then the
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
    out_stream = Stream('list_to_stream')
    thread = list_source(
        function, out_stream, in_list, time_interval,
        num_steps, window_size, state, *args, **kwargs)
    return thread, out_stream


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
                source_queue.put(
                    (out_stream, [function(message, *args, **kwargs)]))
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
                source_queue.put(
                    (out_stream, [output_element]))
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
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#                                     TESTS                                                     -
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------

def test_source_agents():
    import random

    MAX_VALUE=32
    NUM_STEPS=4
    WIN_SIZE=4
    
    #=====================================================================
    #=====================================================================
    #                 TEST FUNCTION_TO_STREAM
    #=====================================================================
    #=====================================================================

    #------------------------------------------------------------------
    #TEST FINITE EXECUTION, STATELESS
    #------------------------------------------------------------------
    # Function created by the source agent
    random_integer_stream_test_list = []
    def random_integer(random_integer_stream_test_list):
        return_value = random.randint(1, 10)
        random_integer_stream_test_list.append(return_value)
        return return_value

    # Create the source agent
    random_integer_thread, random_integer_stream = function_to_stream(
        function=random_integer, time_interval=0.01,
        num_steps=NUM_STEPS, window_size=WIN_SIZE,
        random_integer_stream_test_list = random_integer_stream_test_list)

    # Create the sink agent
    random_integer_stream_list = []
    stream_to_list(random_integer_stream, random_integer_stream_list)
    #------------------------------------------------------------------

    #------------------------------------------------------------------
    #TEST FINITE EXECUTION, STATEFUL
    #------------------------------------------------------------------
    # Function created by the source agent
    def clock_ticks(state, max_value=2**30):
        return state, (state+1)%max_value

    # Create the source agent
    window_clock_thread, window_clock = function_to_stream(
        function=clock_ticks, time_interval=0.01,
        num_steps=NUM_STEPS, window_size=WIN_SIZE,
        state=0, max_value=MAX_VALUE)

    # Create the sink agent
    clock_stream_list = []
    stream_to_list(window_clock, clock_stream_list)

    if NUM_STEPS*WIN_SIZE >= MAX_VALUE:
        clock_stream_test_list = \
          range(MAX_VALUE)*int((NUM_STEPS*WIN_SIZE)/MAX_VALUE)
    else:
        clock_stream_test_list = range(NUM_STEPS*WIN_SIZE)

    #=====================================================================    
    #=====================================================================
    # TEST FILE TO STREAM
    #=====================================================================
    #=====================================================================

    ## #------------------------------------------------------------------
    ## #TEST FINITE EXECUTION, STATELESS
    ## #------------------------------------------------------------------

    # Compute expected output for testing
    file_to_stream_test_list = range(NUM_STEPS*WIN_SIZE)
    
    # Empty the file and write test values into the file
    with open('test_file.txt', 'w'): pass
    with open('test_file.txt', 'a') as the_file:
        for i in file_to_stream_test_list:
            the_file.write(str(i) + '\n')

    # Create the source agent
    file_thread, file_stream = file_to_stream(
        function=int, filename='test_file.txt',
        num_steps=NUM_STEPS, window_size=WIN_SIZE,
        time_interval=0.001)

    # Create the sink agent
    file_stream_list = []
    stream_to_list(file_stream, file_stream_list)

    # STARTING UP -----------------------------------------
    # Start the compute engine and start its thread.
    compute_engine.start()
    # Start the source threads.
    random_integer_thread.start()
    window_clock_thread.start()
    file_thread.start()
    
    # SHUTTING DOWN ----------------------------------------
    # Join the source threads.
    random_integer_thread.join()
    window_clock_thread.join()
    file_thread.join()
    # Wait for some time so that the compute engine thread can run
    # then stop the compute engine and join its thread. 
    time.sleep(0.1)
    compute_engine.stop()

    # CHECK VALUES PUT INTO STREAMS BY SOURCES ------------
    assert random_integer_stream_list == random_integer_stream_test_list
    assert clock_stream_list == clock_stream_test_list
    assert file_stream_list == file_to_stream_test_list

    # Empty the file
    with open('test_file.txt', 'w'): pass


    ## #------------------------------------------------------------------
    ## # TEST FINITE EXECUTION, STATEFUL
    ## #------------------------------------------------------------------
    NUM_STEPS=16
    WINDOW_SIZE=2
    INITIAL_STATE=0

    # A stateful function
    def h(value, state):
        next_state = int(value)+state
        return next_state, next_state

    # Compute expected output for testing
    file_stream_2_test_list = []
    state = INITIAL_STATE
    for i in range(NUM_STEPS*WINDOW_SIZE):
        output_increment, state = h(i, state)
        file_stream_2_test_list.append(output_increment)
    
    # Empty the file and write values into the file
    with open('test_file.txt', 'w'): pass
    with open('test_file.txt', 'a') as the_file:
        for i in range(NUM_STEPS*WINDOW_SIZE):
            the_file.write(str(i) + '\n')

    # Create the source agent
    file_thread_2, file_stream_2 = file_to_stream(
        function=h, filename='test_file.txt',
        num_steps=NUM_STEPS, window_size=WINDOW_SIZE,
        state=INITIAL_STATE, time_interval=0.001)

    # Create the sink agent
    file_stream_2_list = []
    stream_to_list(file_stream_2, file_stream_2_list)

    # STARTING UP -----------------------------------------
    # Start the compute engine and start its thread.
    compute_engine.start()
    # Start the source threads.
    file_thread_2.start()

    # SHUTTING DOWN ----------------------------------------
    # Join the source threads.
    file_thread_2.join()
    # Wait for some time so that the compute engine thread can run
    # then stop the compute engine and join its thread. 
    time.sleep(0.1)
    compute_engine.stop()

    # CHECK VALUES PUT INTO STREAMS BY SOURCES ------------
    assert file_stream_2_list == file_stream_2_test_list

    # Empty the file
    with open('test_file.txt', 'w'): pass


    ## #------------------------------------------------------------------
    ## # TEST INFINITE EXECUTION, STATELESS
    ## #------------------------------------------------------------------
    NUM_STEPS=8
    WINDOW_SIZE=4

    # Compute expected output for testing
    file_stream_test_list = range(NUM_STEPS*WINDOW_SIZE)

    # Set up the file for the source
    # Empty the file and write values into the file
    with open('test_file.txt', 'w'): pass
    with open('test_file.txt', 'a') as the_file:
        mm = NUM_STEPS*WINDOW_SIZE
        for i in range(mm):
            the_file.write(str(i) + '\n')


    # Create source agent
    # This execution continues till the entire file
    # is read because no num_steps argument is passed
    # to the call to file_to_stream.
    file_thread_3, file_stream_3 = file_to_stream(
        function=int, filename='test_file.txt',
        window_size=WINDOW_SIZE,
        time_interval=0.01)

    # Create the sink agent
    file_stream_3_list = []
    stream_to_list(file_stream_3, file_stream_3_list)

    # STARTING UP -----------------------------------------
    # Start the compute engine and start its thread.
    compute_engine.start()
    # Start the source threads.
    file_thread_3.start()

    # SHUTTING DOWN ----------------------------------------
    # Join the source threads.
    file_thread_3.join()
    # Wait for some time so that the compute engine thread can run
    # then stop the compute engine and join its thread.
    time.sleep(0.1)
    compute_engine.stop()

    # CHECK VALUES PUT INTO STREAMS BY SOURCES ------------
    assert file_stream_3_list == file_stream_test_list

    # Empty the file
    with open('test_file.txt', 'w'): pass


    ## #------------------------------------------------------------------
    ## # TEST INFINITE EXECUTION, STATEFUL
    ## #------------------------------------------------------------------
    NUM_STEPS=16
    WINDOW_SIZE=2
    INITIAL_STATE=0

    # A stateful function
    def h(value, state):
        next_state = int(value)+state
        return next_state, next_state

    # Compute expected output for testing
    file_stream_4_test_list = []
    state = INITIAL_STATE
    for i in range(NUM_STEPS*WINDOW_SIZE):
        output_increment, state = h(i, state)
        file_stream_4_test_list.append(output_increment)
    
    # Empty the file and write values into the file
    with open('test_file.txt', 'w'): pass
    with open('test_file.txt', 'a') as the_file:
        mm = NUM_STEPS*WINDOW_SIZE
        for i in range(mm):
            the_file.write(str(i) + '\n')

    # Create source agent
    file_thread_4, file_stream_4 = file_to_stream(
        function=h, filename='test_file.txt',
        window_size=WINDOW_SIZE,
        state=INITIAL_STATE, time_interval=0.01)

    # Create the sink agent
    file_stream_4_list = []
    stream_to_list(file_stream_4, file_stream_4_list)

    # STARTING UP -----------------------------------------
    # Start the compute engine and start its thread.
    compute_engine.start()
    # Start the source threads.
    file_thread_4.start()

    # SHUTTING DOWN ----------------------------------------
    # Join the source threads.
    file_thread_4.join()
    # Wait for some time so that the compute engine thread can run
    # then stop the compute engine and join its thread.
    time.sleep(0.1)
    compute_engine.stop()

    # CHECK VALUES PUT INTO STREAMS BY SOURCES ------------
    assert recent_values(file_stream_4) == file_stream_4_test_list

    # Empty the file
    with open('test_file.txt', 'w'): pass

    #=====================================================================
    #=====================================================================
    # TEST LIST TO STREAM
    #=====================================================================
    #=====================================================================
    # Test stateless
    #Function encapsulated by list_source
    def f(v, multiplier):
        return multiplier*v
    
    test_list = range(32)
    MULTIPLIER = 2
    list_stream_test_list = [f(v, MULTIPLIER) for v in test_list]

    # Create source agent
    # This is a list_source agent and not the function list_to_stream.
    # So, the out_stream is an input parameter, and is not returned by
    # the function.
    list_stream = Stream('list_stream')
    list_thread  = list_source(
        function=f, out_stream=list_stream,
        in_list=test_list, time_interval=0.01,
        multiplier=MULTIPLIER)

    # Create the sink agent
    list_stream_list = []
    stream_to_list(list_stream, list_stream_list)

    # STARTING UP -----------------------------------------
    # Start the compute engine and start its thread.
    compute_engine.start()
    # Start the source threads.
    list_thread.start()

    # SHUTTING DOWN ----------------------------------------
    # Join the source threads.
    list_thread.join()
    # Wait for some time so that the compute engine thread can run
    # then stop the compute engine and join its thread.
    time.sleep(0.1)
    compute_engine.stop()

    # CHECK VALUES PUT INTO STREAMS BY SOURCES ------------
    assert list_stream_list == list_stream_test_list

    #---------------------------------------------------------------
    # Test stateful
    #---------------------------------------------------------------    
    #Function encapsulated by list_source
    def g(v, state, addend):
        return_value = v+state+addend
        state += 1
        return return_value, state

    test_list = range(8)

    # The expected output
    ADDEND=1
    list_stream_2_test_list = []
    state=0
    for v in test_list:
        list_stream_2_test_list.append(v+state+ADDEND)
        state += 1
    
    # Create source agent
    # This is a list_source agent and not the function list_to_stream.
    # So, the out_stream is an input parameter, and is not returned by
    # the function.
    list_stream_2 = Stream('list_stream_2')
    list_thread_2 = list_source(
        function=g, out_stream=list_stream_2,
        in_list=test_list, time_interval=0.01, state=0,
        addend=ADDEND)

    # Create the sink agent
    list_stream_2_list = []
    stream_to_list(list_stream_2, list_stream_2_list)

    # STARTING UP -----------------------------------------
    # Start the compute engine and start its thread.
    compute_engine.start()
    # Start the source threads.
    list_thread_2.start()

    # SHUTTING DOWN ----------------------------------------
    # Join the source threads.
    list_thread_2.join()
    # Wait for some time so that the compute engine thread can run
    # then stop the compute engine and join its thread.
    time.sleep(0.1)
    compute_engine.stop()

    # CHECK VALUES PUT INTO STREAMS BY SOURCES ------------
    assert list_stream_2_list == list_stream_2_test_list
    #=====================================================================
    #=====================================================================
    # TEST QUEUE TO STREAM
    #=====================================================================
    #=====================================================================
    import Queue
    queue = Queue.Queue()

    # Test stateless case

    queue_test_list = range(8)
    # Put data into the queue
    for i in queue_test_list:
        queue.put(i)
    queue.put('stop')

    def f(v, multiplier):
        return v*multiplier

    # The expected output
    MULTIPLIER=2
    queue_out_stream_test_list = [
        f(v, MULTIPLIER) for v in queue_test_list]
    
    # Create source agent
    queue_thread, queue_out_stream = queue_to_stream(
        function=f, queue=queue, stop_message='stop',
        multiplier=MULTIPLIER)

    # Create the sink agent
    queue_out_stream_list = []
    stream_to_list(queue_out_stream, queue_out_stream_list)

    # STARTING UP -----------------------------------------
    # Start the compute engine and start its thread.
    compute_engine.start()
    # Start the source threads.
    queue_thread.start()

    # SHUTTING DOWN ----------------------------------------
    # Join the source threads.
    queue_thread.join()
    # Wait for some time so that the compute engine thread can run
    # then stop the compute engine and join its thread.
    time.sleep(0.2)
    compute_engine.stop()

    # CHECK VALUES PUT INTO STREAMS BY SOURCES ------------
    assert queue_out_stream_list == queue_out_stream_test_list

    
    #-------------------------------------------------------------
    # Test stateful case
    #-------------------------------------------------------------
    queue_test_list = range(8)
    # Put data into the queue
    for i in queue_test_list:
        queue.put(i)
    queue.put('stop')

    def g(v, state, addend):
        return_value = v+state+addend
        state += 1
        return return_value, state

    # The expected output
    ADDEND=1
    queue_out_stream_2_test_list = []
    state=0
    for v in queue_test_list:
        queue_out_stream_2_test_list.append(v+state+ADDEND)
        state += 1
    
    # Create source agent
    queue_thread_2, queue_out_stream_2 = queue_to_stream(
        function=g, state=0, queue=queue, stop_message='stop',
        addend=ADDEND)

    # Create the sink agent
    queue_out_stream_2_list = []
    stream_to_list(queue_out_stream_2, queue_out_stream_2_list)

    # STARTING UP -----------------------------------------
    # Start the compute engine and start its thread.
    compute_engine.start()
    # Start the source threads.
    queue_thread_2.start()

    # SHUTTING DOWN ----------------------------------------
    # Join the source threads.
    queue_thread_2.join()
    # Wait for some time so that the compute engine thread can run
    # then stop the compute engine and join its thread.
    time.sleep(0.2)
    compute_engine.stop()

    # CHECK VALUES PUT INTO STREAMS BY SOURCES ------------
    assert queue_out_stream_2_list == queue_out_stream_2_test_list
    return
    
if __name__ == '__main__':
    test_source_agents()
    
    
    
    
    

