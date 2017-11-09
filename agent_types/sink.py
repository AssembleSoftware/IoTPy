"""
This module consist of sink functions. A sink is a function that reads
a single stream and that carries out operations on an actuator or other
object such as a list, file, queue, circular buffer, printer or
display. The function typically returns None.

Functions in the module:
   1. sink_element
   2. sink: identical to sink_element
   3. stream_to_list
   4. stream_to_file
   5. stream_to_queue
   6. stream_to_buffer
   7. sink_window
   8. sink_list


Uses:
stream_to_list, stream_to_file, stream_to_queue use sink.
sink uses sink_element

"""
import sys
import os
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../helper_functions"))

from agent import Agent
from stream import Stream, _multivalue
from check_agent_parameter_types import *

from agent import Agent, InList
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from Buffer import Buffer

#-----------------------------------------------------------------------
# SINK: SINGLE INPUT STREAM, NO OUTPUT
#-----------------------------------------------------------------------
def sink_element(
        func, in_stream, state=None, call_streams=None, name=None,
        *args, **kwargs):
    """
    This agent applies func to an element of its single input stream,
    in_stream. func has no output streams. Typically, func has the
    side effect of modifying an actuator.

    Parameters
    ----------
        func: function
           function from an element of the in_stream and args and kwargs
           to None (no return).
        in_stream: Stream
           The single input stream of this agent
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_streams. A new value in any stream in this
           list causes a state transition of this agent.
        name: Str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    check_sink_agent_arguments(func, in_stream, call_streams, name)
    #check_num_args_in_func(state, name, func, args, kwargs)

    # The transition function for this agent.
    def transition(in_lists, state):
        num_in_streams = 1
        check_in_lists_type(name, in_lists, num_in_streams)
        in_list = in_lists[0]
        input_list = in_list.list[in_list.start:in_list.stop]
        # If the new input data is empty then return an empty list for
        # the single output stream, and leave the state and the starting
        # point for the single input stream unchanged.
        if input_list is None or len(input_list) == 0:
            return ([], state, [in_list.start])

        if state is None:
            for element in input_list:
                func(element, *args, **kwargs)
        else:
            for element in input_list:
                state = func(element, state, *args, **kwargs)
        return ([], state, [in_list.start+len(input_list)])
    # Finished transition

    # Create agent
    return Agent([in_stream], [], transition, state, call_streams, name)

# -------------------------------------------
# sink and sink_element are identical.
# Using sink is shorter.
sink = sink_element

# -----------------------------
def stream_to_list(in_stream, target_list,
                   element_function=None, state=None,
                   **kwargs):
    """
    Parameters
    ----------
    in_stream: Stream
       The input stream. This stream is copied to target_list. If the
       stream grows too large, target_list may grow too large for the
       available memory.
    target_list: list
    element_function: function (optional)
       If element_function is None the input stream is copied to
       target_list. If element_function is not None then it is applied
       to each element of the input stream and the result is copied to
       target_list.
    state: object (optional)
       The state, if any, of element_function.
    kwargs: key word arguments of element_function.

    Returns
    -------
       None

    """
    
    def simple_append(element, target_list):
        target_list.append(element)
    def function_stateless_append(
            element, target_list, element_function, **kw):
        target_list.append(element_function(element, **kw))
    def function_stateful_append(
            element, state, target_list, element_function, **kw):
        next_output, next_state = element_function(
            element, state, **kw) 
        target_list.append(next_output)
        return next_state

    if element_function is None:
        sink(simple_append, in_stream, target_list=target_list)
    elif state is None:
        ext_kw = kwargs
        ext_kw['target_list'] = target_list
        ext_kw['element_function'] = element_function
        sink(function_stateless_append, in_stream, **ext_kw)  
    else:
        # function and state are both non None
        ext_kw = kwargs
        ext_kw['target_list'] = target_list
        ext_kw['element_function'] = element_function
        sink(function_stateful_append, in_stream, state, **ext_kw) 

# -----------------------------
def stream_to_file(
        in_stream, filename, element_function=None, state=None,
        **kwargs):
    """
    Same as stream_to_list except that the target is the file,
    specified by filename, rather than a list.

    Parameters
    ----------
    in_stream: Stream
       The input stream. This stream is copied to the file with name
       filename. 
    filename: str
       Name of the target file.
    element_function: function (optional)
       If element_function is None the input stream is copied to
       target file. If element_function is not None then it is applied
       to each element of the input stream and the result is copied to
       the target file.
    state: object (optional)
       The state, if any, of element_function.
    kwargs: key word arguments of element_function.

    Returns
    -------
       None


    """
    def simple_append(element, filename):
        with open(filename, 'a') as the_file:
            the_file.write(str(element) + '\n')
    def function_stateless_append(
            element, filename, element_function, **kw):
        with open(filename, 'a') as the_file:
            the_file.write(str(element_function(element, **kw)) + '\n')
    def function_stateful_append(
            element, state, filename, element_function, **kw):
        next_output, next_state = element_function(element, state, **kw)
        with open(filename, 'a') as the_file:
            the_file.write(str(next_output) + '\n')
        return next_state

    if element_function is None:
        sink(simple_append, in_stream, filename=filename)
    elif state is None:
        ext_kw = kwargs
        ext_kw['filename'] = filename
        ext_kw['element_function'] = element_function
        sink(function_stateless_append, in_stream, **ext_kw) 
    else:
        # function and state are both non None
        ext_kw = kwargs
        ext_kw['filename'] = filename
        ext_kw['element_function'] = element_function
        sink(function_stateful_append, in_stream, state, **ext_kw)

#----------------------------------------------------
def stream_to_queue(
        in_stream, queue, element_function=None, state=None,
        **kwargs):
    """
    Same as stream_to_list except that the target is a queue rather
    than a list. 

    Parameters
    ----------
    in_stream: Stream
       The input stream. This stream is copied to the file with name
       filename. 
    queue: Queue.Queue or multiprocessing.Queue
       The target queue
    element_function: function (optional)
       If element_function is None the input stream is copied to
       target queue. If element_function is not None then it is applied
       to each element of the input stream and the result is put in
       the target queue.
    state: object (optional)
       The state, if any, of element_function.
    kwargs: key word arguments of element_function.

    Returns
    -------
       None


    """
    def simple_append(element, queue):
        queue.put(element)
    def function_stateless_append(
            element, queue, element_function, **kw):
        queue.put(element_function(element, **kw))

    def function_stateful_append(
            element, state, queue, element_function, **kw):
        next_output, next_state = element_function(element, state, **kw)
        queue.put(next_output)
        return next_state

    if element_function is None:
        sink(simple_append, in_stream, queue=queue)
    elif state is None:
        ext_kw = kwargs
        ext_kw['queue'] = queue
        ext_kw['element_function'] = element_function
        sink(function_stateless_append, in_stream, **ext_kw) 
    else:
        # function and state are both non None
        ext_kw = kwargs
        ext_kw['queue'] = queue
        ext_kw['element_function'] = element_function
        sink(function_stateful_append, in_stream, state, **ext_kw)

def stream_to_buffer(in_stream, target_buffer):
    """
    Copies in_stream to target_buffer which is a circular buffer with
    a specifed size. If the buffer gets full, older values are
    discarded.

    Parameters
    ----------
    in_stream: Stream
       The input stream
    target_buffer: Buffer (multiprocessing/Buffer)

    Returns
    -------
       None

    """
    def append_target_buffer(element):
        target_buffer.append(element)
    sink(append_target_buffer, in_stream)
    return

def sink_window(func, in_stream,
                window_size, step_size=1,
                state=None, call_streams=None, name=None,
                *args, **kwargs):
    """
    Executes func on windows into in_stream. Typically, func has side
    effects which modify actuators

    Parameters
    ----------
        func: function
           function on a window of the input stream that
           returns None and has a side effect such as writing a
           file or appending to a queue.
        in_stream: Stream
           The single input stream of this agent
           (This function has no out_streams.)
        window_size: int
           Positive integer. The size of the moving window
        step_size: int
           Positive integer. The step size of the moving window
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_streams. A new value in any stream in this
           list causes a state transition of this agent.
        name: Str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    check_window_and_step_sizes(name, window_size, step_size)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_in_streams = 1

    # The transition function for the map agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
        # The map agent has a single input stream. So, the transition
        # operates on a single in_list.
        in_list = in_lists[0]
        # The map agent has no output stream. So, the transition
        # outputs nothng, i.e., output_list is [].
        list_length = in_list.stop - in_list.start
        if window_size > list_length:
            # No changes are made.
            # return output_list, next state, starting indexes.
            return ([], state, [in_list.start])

        # There is enough input data for at least one step.
        num_steps = int(1+(list_length - window_size)/step_size)
        for i in range(num_steps):
            window = in_list.list[
                in_list.start+i*step_size : in_list.start+i*step_size+window_size]
            if state is None:
                func(window, *args, **kwargs)
            else:
                func(window, state, *args, **kwargs)
        # return output_list which is empty, next state, new starting indexes.
        return ([], state, [in_list.start+num_steps*step_size])
    # Finished transition

    # Create agent
    # This agent has no output streams, and so out_streams is [].
    return Agent([in_stream], [], transition, state, call_streams,
                 name) 

def sink_list(func, in_stream, state=None,
              call_streams=None, name=None, *args, **kwargs):
    """
    This agent applies func to a list in its single input stream. It
    has no output streams. 

    Parameters
    ----------
        func: function
           function from a list (a slice of the in_stream) to None (no
           output). 
        in_stream: Stream
           The single input stream of this agent
        state: object
           The state of the agent
        name: Str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    # Check the arguments and output error messages if argument types
    # and numbers are incorrect.
    check_sink_agent_arguments(func, in_stream, call_streams, name)
    check_num_args_in_func(state, name, func, args, kwargs)

    # The transition function for this agent.
    def transition(in_lists, state):
        num_in_streams = 1
        # Check the types of the input lists for the transition.
        check_in_lists_type(name, in_lists, num_in_streams)
        # This agent has only one input stream. Get its only in_list.
        in_list = in_lists[0]
        # input_list is the slice of the input stream that this agent
        # is working on.
        # in_list is an object of type InList, and it consists of an
        # arbitrarily long list (in_list.list), and pointers to where
        # this agent is starting to read the list (in_list.start), and
        # where the list ends (in_list.stop). 
        input_list = in_list.list[in_list.start:in_list.stop]
        # If the new input data is empty then return an empty list for
        # the single output stream, and leave the state and the starting
        # point for the single input stream unchanged. Normally, the
        # null transition occurs when the agent is invoked by a call
        # stream. 
        if not input_list or len(input_list) == 0:
            return ([[]], state, [in_list.start])

        # Compute the output generated by this transition.
        if state is None:
            func(input_list, *args, **kwargs)
        else:
            state = func(input_list, state, *args, **kwargs)

        # Return: (1) the list of outputs, one per output stream.
        #         sink agent has no output; its output list is [].
        #         (2) the new state and
        #         (3) the new starting pointer into this stream for
        #             this agent. Since this agent has read the entire
        #             input_list, move its starting pointer forward by
        #             the length of the input list.
        return ([], state, [in_list.start+len(input_list)])
    
    # Finished transition

    # Create agent with the following parameters:
    # 1. list of input streams. sink has a single input stream.
    # 2. list of output streams. sink has no output.
    # 3. transition function
    # 4. new state
    # 5. list of calling streams
    # 6. Agent name
    return Agent([in_stream], [], transition, state, call_streams, name)
