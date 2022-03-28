"""
This module consist of simple functions that are sufficient for
writing streaming applications; however, the other files in
this folder (agent_types) has more powerful functions.

Functions in the module:
   1. f_item
   2. f_window
   3. join_synch
   4. join_asynch
   5. join_timed

Calls:
  1. sink_element: same as f_item
  2. sink_window: same as f_window
  3. zip_map_sink: same as join_synch

"""
from ..core.stream import Stream, StreamArray
from ..core.agent import Agent, InList
from ..core.helper_control import _no_value, _multivalue

# agent, stream, helper_control are ../core
from ..helper_functions.recent_values import recent_values
# recent_values are in ../helper_functions
from .check_agent_parameter_types import *
# check_agent_parameter_types is in the current directory

from .sink import sink_element, sink_window
from .merge import zip_map_sink, timed_zip

#-----------------------------------------------------------------------
# SINK: SINGLE INPUT STREAM, NO OUTPUT
#-----------------------------------------------------------------------

def f_item(
        func, in_stream, state=None, call_streams=None, name=None,
        *args, **kwargs):
    sink_element(func, in_stream, state=None, call_streams=None,
                     name=None, *args, **kwargs)

#------------------------------------------------------------------
def f_window(func, in_stream, window_size, step_size=1,
                state=None, call_streams=None, name=None,
                *args, **kwargs):
    sink_window(func, in_stream, window_size, step_size=1,
                    state=None, call_streams=None, name=None,
                    *args, **kwargs)
    
#------------------------------------------------------------------
def join_synch(
        func, in_streams, state=None, call_streams=None,
        name='join_synch', *args, **kwargs):
    zip_map_sink(
        func, in_streams,
        state=None, call_streams=None, name='zip_map_sink',
        *args, **kwargs)


#----------------------------------------------------------------------------
def join_asynch(
        func, in_streams, state=None, call_streams=None, name='f_join_asynch',
        **kwargs):
    """
    Parameters
    ----------
        func: function
           function on elements of ANY input stream
        in_streams: list of Stream
           The list of input streams of the agent
        out_stream=None
        state=None
        name: str
           Name of the agent created by this function.
    Returns
    -------
        Agent.
         The agent created by this function.

    """
    def transition(in_lists, state):
        for v in in_lists:
            # loop through each in_stream with one in_list
            # per in_stream
            if v.stop > v.start:
                # In the following, input_list is the list of new 
                # values on an in_stream
                input_list = v.list[v.start:v.stop]
        
        # If the input data is empty, i.e., if v.stop == v.start for all
        # v in in_lists, then return empty lists for  each output stream, 
        # and leave the state and the starting point for each input
        # stream unchanged.
        if all(v.stop <= v.start for v in in_lists):
            return ([], state, [v.start for v in in_lists])

        # Assert at least one input stream has unprocessed data.
        for stream_number, v in enumerate(in_lists):
            # if v.stop <= v.start then skip this input stream
            # because no new messages have arrived on this stream.
            if v.stop > v.start:
                # In the following,input_list is the list of new values
                # on the input stream with index stream_number
                input_list = v.list[v.start:v.stop]

                if state is None:
                    for element in input_list:
                        func((stream_number, element), **kwargs)
                else:
                    for element in input_list:
                        state = func((stream_number, element), state, **kwargs)

        return ([], state, [v.stop for v in in_lists])

    # Create agent
    return Agent(in_streams, [], transition, state, call_streams, name)


def join_timed(
        func, in_streams, state=None, call_streams=None, name=None,
        **kwargs):
    temp_stream = Stream()
    timed_zip(in_streams=in_streams, out_stream=temp_stream)
    sink_element(func=func, in_stream=temp_stream, state=None, call_streams=None,
                     name=None, **kwargs)
        
