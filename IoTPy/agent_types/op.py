"""
This module consists of functions that operate on a single input stream
to produce a single output stream. These stream-functions encapsulate
functions that operate on standard data types such as integers. 

Agents in the module:
   1. map_element
   2. signal_element
   3. filter_element
   4. map_list
   5. map_window
   6. map_window_list
   7. timed_window

In addition functions that return streams are:
   map_element_f (version of map_element)
   filter_element_f (version of filter_element)
   map_window_f (version of map_window)
   map_list_f (version of map_list)
   map_array_f (stream array version of map_list)
   timed_window_f (version of timed_window)

"""
from ..core.stream import StreamArray, Stream 
from ..core.agent import Agent
from ..core.helper_control import _multivalue

# stream, agent, helper_control are in ../cores
from .check_agent_parameter_types import *
# check_agent_parameter_types is in this folder.

def make_out_stream(in_stream):
    if isinstance(in_stream, Stream):
        return Stream()
    if isinstance(in_stream, StreamArray):
        return StreamArray(dimension=in_stream.dimension, dtype=in_stream.dtype)
#------------------------------------------------------------------------------------
def map_element(
        func, in_stream, out_stream,
        state=None, call_streams=None, name=None,
        *args, **kwargs):
    """
    This agent maps the function func from its single input stream to its
    single output stream.

    Parameters
    ----------
        func: function
           function from an element of the in_stream to an element of
           the out_stream. func may also have state and kwargs.
        in_stream: Stream or StreamArray
           The single input stream of this agent
        out_stream: Stream or StreamArray
           The single output stream of the agent
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_streams. A new value in any stream in this
           list causes a state transition of this agent.
        name: Str
           Name of the agent created by this function.
        *args, **kwargs:
           Positional and keyword parameters, if any, for func.
    Returns
    -------
        Agent.
         The agent created by this function.
    Uses
    ----
       * Agent
       * check_map_agent_arguments
       * check_num_args_in_func
    Used by
    -------
        map_element_f
    Examples
    --------
    With
    map_element(func=lambda x:2*x, in_stream=u, out_stream=v)
    then:
        v[i] = 2*u[i], for all i in streams u, v

    With
    def f(x, state): return 2*x+state, state+10
    map_element(func=f, in_stream=u, out_stream=v, state=0)
    then:
       state[i] = 10*i
       v[i] = 2*u[i] + state[i]


    """
    check_map_agent_arguments(func, in_stream, out_stream, call_streams, name)
    check_num_args_in_func(state, name, func, args, kwargs)

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
            return ([[]], state, [in_list.start])

        if state is None:
            output_list = [func(v, *args, **kwargs) for v in input_list]
        else:
            output_list = [[]]*len(input_list)
            for i in range(len(input_list)):
                output_list[i], state = func(input_list[i], state, *args, **kwargs)
                
        return ([output_list], state, [in_list.start+len(input_list)])
    # Finished transition

    # Create agent
    return Agent([in_stream], [out_stream], transition, state, call_streams, name)


#------------------------------------------------------------------------------------
def signal_element(
        func, in_stream, out_stream,
        state=None, name=None,
        *args, **kwargs):
    """
    This agent executes func when it reads a new value on
    in_stream. The function func operates on kwargs and possibly
    a state. Note that func does not operate on elements of in_stream.
    This is because in_stream serves merely as a signaling mechanism
    that informs this agent that it needs to execute a step, i.e.,
    call func.

    Parameters
    ----------
        func: function
           function that operates on kwargs and possibly the state.
        in_stream: Stream or StreamArray
           The single input stream of this agent
        out_stream: Stream or StreamArray
           The single output stream of the agent
        state: object
           The state of the agent
        name: Str
           Name of the agent created by this function.
        *args, **kwargs:
           Positional and keyword parameters, if any, for func.
    Returns
    -------
        Agent.
         The agent created by this function.
    Uses
    ----
       * Agent
       * check_map_agent_arguments

    """
    call_streams=None
    check_map_agent_arguments(func, in_stream, out_stream, call_streams, name)

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
            return ([[]], state, [in_list.start])
        # In the following output is (typically) _no_value if the
        # variables listed in kwargs do not change, and is any other
        # value if any variable does change.
        else:
            if state is None:
                output = func(*args, **kwargs)
            else:
                output, state = func(state, *args, **kwargs)

        return ([[output]], state, [in_list.start+len(input_list)])
    # Finished transition

    # Create agent
    return Agent([in_stream], [out_stream], transition, state, call_streams, name)


#------------------------------------------------------------------------------------
def filter_element(
        func, in_stream, out_stream,
        state=None, call_streams=None, name=None,
        *args, **kwargs):
    """
    This agent uses the boolean function func to filter its single input stream
    to produce a single output stream.

    Parameters
    ----------
        func: function
           function from an element of the in_stream to Boolean.
        in_stream: Stream
           The single input stream of this agent
        out_stream: Stream
           The single output stream of the agent
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
    Uses
    ----
       * Agent
       * check_map_agent_arguments
       * check_num_args_in_func
    
    Used by
    -------
        filter_element_f
    Example
    -------
    With
    filter_element(func=lambda x: x % 2, in_stream=u, out_stream=v)
    then:
        stream v consists of the elements of stream u that are odd.
        The even elements are filtered out.

    """
    check_map_agent_arguments(func, in_stream, out_stream, call_streams, name)
    check_num_args_in_func(state, name, func, args, kwargs)

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
            return ([[]], state, [in_list.start])

        if state is None:
            output_list = [v for v in input_list if func(v, *args, **kwargs) ]
        else:
            output_list = []
            for i in range(len(input_list)):
                boole, state = func(input_list[i], state, *args, **kwargs)
                if boole: output_list.append(input_list[i])
                
        return ([output_list], state, [in_list.start+len(input_list)])
    # Finished transition

    # Create agent
    return Agent([in_stream], [out_stream], transition, state, call_streams, name)


#------------------------------------------------------------------------------------
def map_element_f(func, in_stream, state=None, *args, **kwargs):
    """
    map_element_f returns out_stream, a stream obtained by applying function to each
    element of the input stream, in_stream.

    Parameters
    ----------
        func: function
           function from an element of the in_stream to an element of the out_stream.
        in_stream: Stream
           The single input stream of this agent
        state: object
           function operates on a state, args, and kwargs
    Returns
    -------
        out_stream: Stream
           The output stream generated by map_element_f
    Uses
    -------
        * map_element


    """
    
    out_stream = make_out_stream(in_stream)
    map_element(func, in_stream, out_stream, state,
                      None, None,
                      *args, **kwargs)
    return out_stream


#------------------------------------------------------------------------------------
def filter_element_f(func, in_stream, state=None, *args, **kwargs):
    """
    filter_element_f returns out_stream, a stream obtained by applying the filter function
    to the input stream, in_stream.

    Parameters
    ----------
        func: function
           function from an element of the in_stream to Boolean.
        in_stream: Stream
           The single input stream of this agent
        state: object
           function operates on a state, args, and kwargs
    Returns
    -------
        out_stream: Stream
           The output stream generated by map_element_f
    Uses
    ----
        filter_element
    Used by
    -------
        map_element_f

    """
    out_stream = Stream(func.__name__+in_stream.name)
    filter_element(func, in_stream, out_stream, state, *args,
                         **kwargs)
    return out_stream

#------------------------------------------------------------------------------------
def map_list(func, in_stream, out_stream, state=None,
                   call_streams=None, name=None,
                   *args, **kwargs):
    """
    This is the same as map_element except that in map_list
    func is from a list to a list whereas in map_element
    func is from an element to an element.

    Parameters
    ----------
        func: function
           function from a list (a slice of the in_stream) to
           a list (a slice of the out_stream).
        in_stream: Stream
           The single input stream of this agent
        out_stream: Stream
           The single output streams of the agent
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_streams. A new value in any stream in this
           list causes a state transition of this agent.
        name: str
           Name of the agent created by this function.

    Returns
    -------
        Agent.
         The agent created by this function.

    """
    # Check the arguments and output error messages if argument types
    # and numbers are incorrect.
    check_map_agent_arguments(func, in_stream, out_stream, call_streams, name)
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
        # point for the single input stream unchanged. This is the
        # null transition. Normally, the null transition occurs when
        # the agent is invoked by a call stream.
        if len(input_list) == 0:
            return ([[]], state, [in_list.start])

        # Compute the output generated by this transition.
        if state is None:
            output_list = func(input_list, *args, **kwargs)
        else:
            output_list, state = func(input_list, state, *args, **kwargs)

        # Return: (1) the list of outputs, one per output stream,
        #         (2) the new state and
        #         (3) the new starting pointer into this stream for
        #             this agent. Since this agent has read the entire
        #             input_list, move its starting pointer forward by
        #             the length of the input list.
        return ([output_list], state, [in_list.start+len(input_list)])
    
    # Finished transition

    # Create agent with parameters:
    # 1. list of input streams. map has a single input
    # 2. list of output streams. map has a single output.
    # 3. transition function
    # 4. new state
    # 5. list of calling streams
    # 6. Agent name
    return Agent([in_stream], [out_stream], transition, state,
                 call_streams, name)

#------------------------------------------------------------------------------------
def map_list_f(func, in_stream, state=None, *args, **kwargs):
    out_stream = Stream(func.__name__+in_stream.name)
    map_list(func, in_stream, out_stream, state, None, None,
                   *args, **kwargs)
    return out_stream

#------------------------------------------------------------------------------------
def chunk(func, in_stream, out_stream, state=None,
          call_streams=None, name=None,
          *args, **kwargs):
    """
    Identical to map_list except that instead of returning
    a list of values that extends the output stream it
    returns a single value. For example, func can be a sum
    of the list of the new values that extend in_stream.
    Used in multicore applications to copy chunks from one
    process to another.

    Parameters
    ----------
        func: function
           function from a list (a slice of the in_stream) to
           a list (a slice of the out_stream).
        in_stream: Stream
           The single input stream of this agent
        out_stream: Stream
           The single output streams of the agent
        state: object
           The state of the agent
        call_streams: list of Stream
           The list of call_streams. A new value in any stream in this
           list causes a state transition of this agent.
        name: str
           Name of the agent created by this function.

    Returns
    -------
        Agent.
         The agent created by this function.

    """
    # Check the arguments and output error messages if argument types
    # and numbers are incorrect.
    check_map_agent_arguments(func, in_stream, out_stream, call_streams, name)
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
        # point for the single input stream unchanged. This is the
        # null transition. Normally, the null transition occurs when
        # the agent is invoked by a call stream.
        if len(input_list) == 0:
            return ([[]], state, [in_list.start])

        # Compute the output generated by this transition.
        if state is None:
            # Note: for map_list this statement is:
            # output_list = func(input_list, *args, **kwargs)
            output = func(input_list, *args, **kwargs)
        else:
            output, state = func(input_list, state, *args, **kwargs)

        # Return: (1) the list of outputs, one per output stream,
        #         (2) the new state and
        #         (3) the new starting pointer into this stream for
        #             this agent. Since this agent has read the entire
        #             input_list, move its starting pointer forward by
        #             the length of the input list.
        # Note: for map_list the return statement is:
        # return ([output_list], state, [in_list.start+len(input_list)])
        return ([[output]], state, [in_list.start+len(input_list)])
    
    # Finished transition

    # Create agent with parameters:
    # 1. list of input streams. map has a single input
    # 2. list of output streams. map has a single output.
    # 3. transition function
    # 4. new state
    # 5. list of calling streams
    # 6. Agent name
    return Agent([in_stream], [out_stream], transition, state,
                 call_streams, name)


#------------------------------------------------------------------------------------
def map_array_f(func, in_stream, state=None, *args, **kwargs):
    out_stream = StreamArray(func.__name__+in_stream.name)
    map_list(func, in_stream, out_stream, state, None, None,
                   *args, **kwargs)
    return out_stream

#------------------------------------------------------------------------------------
def map_window(
        func, in_stream, out_stream,
        window_size, step_size=1,
        state=None, initial_value=None,
        call_streams=None, name=None,
        *args, **kwargs):
    """

    Parameters
    ----------
        func: function
           function from a single element of the input stream to a
           single element of the output stream
        in_stream: Stream
           The single input stream of this agent
        out_stream: Stream
           The single output streams of the agent
        window_size: int
           Positive integer. The size of the moving window
        step_size: int
           Positive integer. The step size of the moving window
        state: object
           The state of the agent
        initial_value: None or object
           If initial_value is None then the output stream starts
           after its first window is full. Otherwise, the output
           stream starts with window_size elements of initial_value.
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
    check_map_agent_arguments(func, in_stream, out_stream, call_streams, name)
    check_window_and_step_sizes(name, window_size, step_size)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_in_streams = 1
    num_out_streams = 1

    if initial_value is not None:
        out_stream.extend([initial_value for _ in range(window_size)])

    # The transition function for the map agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
        # The map agent has a single input stream. So, the transition
        # operates on a single in_list.
        in_list = in_lists[0]
        # The map agent has a single output stream. So, the transition
        # outputs a single list.
        output_list = []
        list_length = in_list.stop - in_list.start
        if window_size > list_length:
            # No changes are made.
            return ([output_list], state, [in_list.start])

        # There is enough input data for at least one step.
        num_steps = int(1+(list_length - window_size)//step_size)
        output_list = [[]]*num_steps
        for i in range(num_steps):
            window = in_list.list[
                in_list.start+i*step_size : in_list.start+i*step_size+window_size]
            if state is None:
                output_list[i] = func(window, *args, **kwargs)
            else:
                output_list[i], state = func(window, state, *args, **kwargs)
        
        return ([output_list], state, [in_list.start+num_steps*step_size])
    # Finished transition

    # Create agent
    return Agent([in_stream], [out_stream], transition, state, call_streams, name)

#------------------------------------------------------------------------------------
def map_window_f(
        func, in_stream,
        window_size, step_size, state=None,
        *args, **kwargs):
    out_stream = Stream(func.__name__+in_stream.name)
    map_window(func, in_stream, out_stream, window_size, step_size,
                     state, None, None, *args, **kwargs)
    return out_stream


#------------------------------------------------------------------------------------
def map_window_list(
        func, in_stream, out_stream,
        window_size, step_size=1,
        state=None, call_streams=None, name=None, *args, **kwargs):
    """
    Same as map_window except that func in map_window_list returns a list
    and the out_stream is extended (not appended) with the list.

    """
    check_map_agent_arguments(func, in_stream, out_stream, call_streams, name)
    check_window_and_step_sizes(name, window_size, step_size)
    check_num_args_in_func(state, name, func, args, kwargs)
    num_in_streams = 1
    num_out_streams = 1

    # The transition function for the map agent.
    def transition(in_lists, state):
        check_in_lists_type(name, in_lists, num_in_streams)
        # The map agent has a single input stream. So, the transition
        # operates on a single in_list.
        in_list = in_lists[0]
        # The map agent has a single output stream. So, the transition
        # outputs a single list.
        output_list = []
        list_length = in_list.stop - in_list.start
        if window_size > list_length:
            # No changes are made.
            return ([output_list], state, [in_list.start])

        # There is enough input data for at least one step.
        num_steps = int(1+(list_length - window_size)//step_size)
        output_list = [[]]*num_steps
        for i in range(num_steps):
            window = in_list.list[
                in_list.start+i*step_size : in_list.start+i*step_size+window_size]
            if state is None:
                output_list[i] = _multivalue(func(window, *args, **kwargs))
            else:
                multivalue_output, next_state = func(window, state, *args, **kwargs)
                output_list[i], state = \
                  _multivalue(multivalue_output), next_state
        
        return ([output_list], state, [in_list.start+num_steps*step_size])
    # Finished transition

    # Create agent
    return Agent([in_stream], [out_stream], transition, state, call_streams, name)


#------------------------------------------------------------------------------------
def map_window_list_f(
        func, in_stream,
        window_size, step_size, state=None,
        *args, **kwargs):
    out_stream = Stream(func.__name__+in_stream.name)
    map_window_list(func, in_stream, out_stream, window_size, step_size,
                     state, None, None, *args, **kwargs)
    return out_stream

#------------------------------------------------------------------------------------
def timed_window(
        func, in_stream, out_stream,
        window_duration, step_time, window_start_time=0,
        state=None, call_streams=None, name=None,
        *args, **kwargs):
    """
    Parameters
    ----------
        func: function
           function from a window (list) of timed elements
           of the input timed stream to a single timed
           element of the output stream
        in_stream: Stream
           The single timed input stream
        out_stream: Stream
           The single timed output stream
        window_duration: number (int or float)
           The duration, in units of time, of this window
        step_time: number (int or float)
           The length of time that the window is moved forward
           at each step.
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
    

    # All windows with start times earlier than window_start_time
    # have already been processed.
    # state is the state of the underlying agent.
    # Augment the state with the start time of the
    # window.
    state = (window_start_time, state)

    def transition(in_lists, state):
        # The map agent has a single input stream. So, the transition
        # operates on a single in_list.
        in_list = in_lists[0]
        # The map agent has a single output stream. So, the transition
        # outputs a single list.
        output_list = []
        # input_list is the list extracted from in_list
        input_list = in_list.list[in_list.start:in_list.stop]
        if len(input_list) == 0:
            return ([output_list], state, [in_list.start])
        
        # Extract window start and the underlying state from the combined state.
        window_start_time, temp_state = state
        state = temp_state
        window_end_time = window_start_time + window_duration
        # last_element = input_list[-1]
        last_element_time = input_list[-1][0]
        # index is a pointer to input_list which starts at 0.
        timestamp_list = [timestamp_and_value[0] for timestamp_and_value in input_list]
        window_start_index = 0
        
        # Main loop    
        while window_end_time <= last_element_time:
            # Compute window_start_index which is the earliest index to an element
            # whose timestamp is greater than or equal to window_start_time
            while (window_start_index < len(input_list) and
                   timestamp_list[window_start_index] < window_start_time):
                window_start_index += 1

            if window_start_index >= len(input_list):
                # No element has timestamp greater than or equal to window_start_time.
                break

            # The timestamp corresponding to window_start_index may be much larger than
            # window_start_time. So, instead of moving the window start time in many steps,
            # move the window start time forward to match the window start index.
            # Then update the window end time to match the new window start time.
            # num_steps is the number of steps that the window is moved forward
            # so that the window includes window_start_index.
            if window_end_time > timestamp_list[window_start_index]:
                num_steps = 0
            else:
                num_steps = \
                  1 + int(timestamp_list[window_start_index] - window_end_time)// int(step_time)
            # Slide the start and end times forward by the number of steps.
            window_start_time += num_steps * step_time
            window_end_time = window_start_time + window_duration
 
            # If window end time exceeds the timestamp of the last element then
            # this time-window crosses the input list. So, we have to wait for
            # elements with higher timestamps before the end of the window can
            # be determined. In this case break from the main loop.
            if window_end_time > last_element_time:
                break

            # Compute window end index which is the first element whose timestamp
            # is greater than or equal to window_end_time.
            window_end_index = window_start_index
            while timestamp_list[window_end_index] < window_end_time:
                window_end_index += 1

            next_window = input_list[window_start_index : window_end_index]

            # Compute output_increment which is the output for
            # next_window.
            if state is None:
                output_increment = func(next_window)
            else:
                output_increment, state = func(next_window, state)

            # Append the output for this window to the output list.
            # The timestamp for this output is window_end_time.
            output_list.append((window_end_time,output_increment))
            # Move the window forward by one step.
            window_start_time += step_time
            window_end_time = window_start_time + window_duration
        # End main loop

        # RETURN OUTPUT LIST, NEW STATE, and NEW STARTING INDEX
        # Compute window_start_index which is the earliest index to an element
        # whose timestamp is greater than or equal to window_start_time
        while (window_start_index < len(timestamp_list) and
               timestamp_list[window_start_index] < window_start_time):
            window_start_index += 1
        state = (window_start_time, state)
        # Return the list of output messages, the new state, and the
        # new start value of the input stream.
        return ([output_list], state, [window_start_index+in_list.start])
    
    # Create agent
    return Agent([in_stream], [out_stream], transition, state, call_streams, name)


#------------------------------------------------------------------------------------
def timed_window_f(
        func, in_stream, window_duration, step_time, state=None, args=[], kwargs={}):
    out_stream = Stream(func.__name__+in_stream.name)
    timed_window(func, in_stream, out_stream, window_duration, step_time,
                    state=state, *args, **kwargs)
    return out_stream


def copy_stream(in_stream, out_stream):
    map_element(func=lambda x: x, in_stream=in_stream, out_stream=out_stream)


