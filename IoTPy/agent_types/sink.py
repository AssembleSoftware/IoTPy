"""
This module consist of sink functions. A sink is a function that reads a
single stream and that carries out operations on an actuator or other
object such as a list, file, queue, circular buffer, printer or display.

Functions in the module:
   1. sink_element
   2. signal_sink
   3. sink: same as sink_element. Used for convenience.
   4. stream_to_list
   5. stream_to_file
   6. stream_to_queue
   7. stream_to_buffer
   8. sink_window
   9. sink_list
   10. sink_list_f

Agents:
   1. sink_element is the agent used by sink.
   2. signal_sink is an agent that takes a step when signaled by its
      input stream. 

Sink functions:
   1. sink has input arguments: function, input stream, state, and
      positional and keyword arguments. It applies the function to
      each element of the input stream. Typically, this function has
      the side effect of modifying some object such as an actuator.
   2. stream_to_list has input arguments: function, input stream,
      target list and state. It applies the function to each element
      of the input stream and puts the result of the function call on
      the target list.
   3. stream_to_file: has arguments function, input stream, filename,
      and state. It applies the function to each element of the input
      stream and puts the result of the function call on the file
      called filename.
   4. stream_to_queue: has arguments function, input stream, queue,
      and state. It applies the function to each element of the input
      stream and puts the result of the function call on the queue.
   5. sink_conditional

Agents:
   1. sink_element is the agent used by sink.

Uses:
stream_to_list, stream_to_file, stream_to_queue use sink.
sink uses sink_element

"""
from ..core.stream import Stream, StreamArray
from ..core.agent import Agent, InList
from ..core.helper_control import _no_value, _multivalue

# agent, stream, helper_control are ../core
from ..helper_functions.recent_values import recent_values
# recent_values are in ../helper_functions
from .check_agent_parameter_types import *
# check_agent_parameter_types is in the current directory

# json is used in stream_to_json
import json

#-----------------------------------------------------------------------
# SINK: SINGLE INPUT STREAM, NO OUTPUT
#-----------------------------------------------------------------------
def sink_element(
        func, in_stream, state=None, call_streams=None, name=None,
        *args, **kwargs):
    """
    This agent applies func to its single input stream. It has no output streams.

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

#-----------------------------------------------------------------------
def sink_conditional(
        func, in_stream, state=None, call_streams=None, name=None,
        *args, **kwargs):
    """
    This agent applies func to its single input stream. It has no output streams.

    Parameters
    ----------
        func: function
           function from an element of the in_stream and args and kwargs
           The function returns a boolean. If the return value is True then the
           agent moves on to the next element in the stream. If the return value
           is False then the agent remains at the same element of the stream, and
           waits to be woken up again. Usually, the waking up is done with a call
           stream.
        in_stream: Stream
           The single input stream of this agent
        state: object 
           The state of the agent could be None.
           If the state is not None then func must return a 2-tuple, a boolean and
           a state.
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
            # num_succeeded is the number of elements in input_list that
            # have been processed successfully
            num_succeeded = 0
            for element in input_list:
                # success is a boolean which indicates whether func
                # succeeded in processing element
                success = func(element, *args, **kwargs)
                if success:
                    num_succeeded += 1
                else:
                    return ([], state, [in_list.start+num_succeeded])
        else:
            for element in input_list:
                success, state = func(element, state, *args, **kwargs)
                if success:
                    num_succeeded += 1
                else:
                    return ([], state, [in_list.start+num_succeeded])
        return ([], state, [in_list.start+len(input_list)])
    # Finished transition

    # Create agent
    return Agent([in_stream], [], transition, state, call_streams, name)


#-----------------------------------------------------------------------
def signal_sink(
        func, in_stream, state=None, name=None,
        *args, **kwargs):
    """
    This agent executes func when it reads a value on input_stream. It
    has no output streams. This agent does not operate on values of
    in_stream. The input stream, in_stream, is used purely as a
    signaling mechanism that tells this agent to take a step.

    Parameters
    ----------
        func: function
           function that operates on kwargs. func (typically) has side
           effects. If func operates on a state then it returns the
           state. If func has no state then it returns nothing.
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
    call_streams=None
    check_sink_agent_arguments(func, in_stream, call_streams, name)

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
            func(*args, **kwargs)
        else:
            state = func(state, *args, **kwargs)
        return ([], state, [in_list.start+len(input_list)])
    # Finished transition

    # Create agent
    return Agent([in_stream], [], transition, state, call_streams, name)



def sink(func, in_stream, state=None, *args, **kwargs):
    sink_element(func, in_stream, state, *args, **kwargs)

    
# -----------------------------
def stream_to_list(
        in_stream, target_list, element_function=None, state=None,
        **kwargs):
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
def stream_to_json(in_stream, filename):
    def simple_append(element, filename):
        with open(filename, 'a') as the_file:
            json.dump(element, the_file)
    sink(simple_append, in_stream, filename=filename)

    
# -----------------------------
def stream_to_file(
        in_stream, filename, element_function=None, state=None,
        **kwargs):
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
    def append_target_buffer(element):
        target_buffer.append(element)
    sink(append_target_buffer, in_stream)
    return

def sink_window(func, in_stream,
                window_size, step_size=1,
                state=None, call_streams=None, name=None,
                *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function on a single element of the input stream that
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
    return Agent([in_stream], [], transition, state, call_streams, name)

def sink_list(func, in_stream, state=None,
                    call_streams=None, name=None,
                    *args, **kwargs):
    """
    This agent applies func to its single input stream. It has no output streams.

    Parameters
    ----------
        func: function
           function from a list (a slice of the in_stream)  to None (no output).
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
        if input_list is None or len(input_list) == 0:
            return ([], state, [in_list.start])

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

def sink_list_f(func, in_stream, state=None, *args, **kwargs):
    out_stream = Stream(func.__name__+in_stream.name)
    sink_list(func, in_stream, state, None, None,
                   *args, **kwargs)
    return out_stream

def print_from_queue(q):
    while True:
        try:
            v = q.get(timeout=0.5)
        except:
            return
        print(v)

def queue_to_file(q, filename, timeout):
    with open(filename, 'a') as the_file:
        while True:
            try:
                v = q.get(timeout=1.0)
            except:
                return
            the_file.write(str(v) + '\n')
            
        



