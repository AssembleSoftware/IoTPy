import types
import inspect
from ..stream import *
from ..agent import InList

def check_list_of_streams_type(list_of_streams, agent_name, parameter_name):
    """ Helper function to check the types of streams used by an agent.
    Used by: check_agent_arguments()
    
    """
    assert list_of_streams is None or \
           isinstance(list_of_streams, list) or \
           isinstance(list_of_streams, tuple,\
           'Call to create agent named, {0}, has parameter, {1},'\
           ' with an argument, {2}, which is not a list or tuple'.\
           format(agent_name, parameter_name, list_of_streams))
    if list_of_streams is None:
        list_of_streams = []
    for stream in list_of_streams:
        assert isinstance(stream, Stream) or isinstance(stream, StreamArray), \
          'Call to create agent named, {0}, has parameter, {1},'\
          ' with an argument, {2}, which is not a Stream'.\
          format(agent_name, parameter_name, stream)

def check_num_args_in_func(state, name, func, func_args, func_kwargs):
    if state is None:
        check_num_args_in_func_no_state(name, func, func_args, func_kwargs)
    else:
        check_num_args_in_func_with_state(name, func, func_args, func_kwargs)

def check_function_type(name, func):
    assert (isinstance(func, types.FunctionType) or
            isinstance(func, types.BuiltinFunctionType)), \
            'Call to create agent named, {0}, has a parameter func, {1}, which is not a function'.\
            format(name, func)

def check_stream_type(name, in_or_out_stream_str, stream):
    assert isinstance(stream, Stream) or isinstance(stream, StreamArray), \
      'Agent named {0} was created with a parameter, {1}, whose argument {2}'\
      ' is not a single stream.'.\
      format(name, in_or_out_stream_str, stream)

def check_in_lists_type(name, in_lists, num_in_streams):
    assert isinstance(in_lists, list) or isinstance(in_lists, tuple), \
      'Error in transition of agent named {0}. in_lists {1} is not a list.'\
      .format(name, in_lists)
    assert len(in_lists) == num_in_streams, \
      'Error in transition of agent named {0}. The length of in_lists {1} is'\
      ' equal to the number {2} of input streams'.\
      format(name, in_lists, num_in_streams)
    assert all([isinstance(in_list, InList) for in_list in in_lists]), \
      'Error in transition of agent named {0}. An element in in_lists {1} is'\
      ' not of type InList'.format(name, in_lists)

def check_num_args_in_func_no_state(name, func, func_args=[], func_kwargs={}):
    if isinstance(func, types.FunctionType):
        args_and_defaults = inspect.getargspec(func)
        args = args_and_defaults.args
        defaults = args_and_defaults.defaults
        if defaults is None:
            assert len(args)  == 1+len(func_args)+len(func_kwargs), \
              'Error in window_map_agent for agent named {0}.'\
              ' State is None; so func, {1}, should have EXACTLY 1 argument,'\
              ' in addition to func_args and func_kwargs, but args for func are {2}.'\
              ' func_args is {3} and func_kwargs is {4}'.\
              format(name, func.__name__, args, func_args, func_kwargs)

def check_num_args_in_func_with_state(name, func, func_args=[], func_kwargs={}):
    assert isinstance(func, types.FunctionType)
    args_and_defaults = inspect.getargspec(func)
    args = args_and_defaults.args
    defaults = args_and_defaults.defaults
    assert len(args) == 2+len(func_args)+len(func_kwargs), \
      'Error in window_map_agent for agent named {0}.'\
      ' State is not None; so func, {1}, should have EXACTLY 2 arguments,'\
      ' (1) an element and (2) the state, '\
      ' in addition to func_args and func_kwargs,'\
      ' but args for func are {2}'.format(name, func.__name__, args)

def check_func_output_for_multiple_streams(
        func, name, num_out_streams, output_snapshots):
    assert all([isinstance(snapshot, list) or isinstance(snapshot, tuple)
                for snapshot in output_snapshots]), \
                'Error in transition function of agent called {0}.'\
                ' All members of the first return value of func, {1}, must be either a list'\
                ' or a tuple. Here function, {2}, returns {3}'.\
                format(name, func.__name__, func.__name__, output_snapshots)
    assert all([len(snapshot) == num_out_streams for snapshot in output_snapshots]), \
      'Error in transition function of agent named, {0}.'\
      'Function, {1}, must return a list or tuple whose length'\
      ' is equal to the number of output streams, {2}, '\
      ' and a state if state is not None. '\
      ' Function, {3}, returned {4}'.\
      format(name, func.__name__, num_out_streams, func.__name__, output_snapshots)


def check_map_agent_arguments(func, in_stream, out_stream, call_streams, name):
    check_function_type(name, func)
    check_stream_type(name, 'in_stream', in_stream)
    check_stream_type(name, 'out_stream', out_stream)
    check_list_of_streams_type(list_of_streams=call_streams,
                          agent_name=name, parameter_name='call_streams')

def check_sink_agent_arguments(func, in_stream, call_streams, name):
    check_function_type(name, func)
    check_stream_type(name, 'in_stream', in_stream)
    check_list_of_streams_type(list_of_streams=call_streams,
                          agent_name=name, parameter_name='call_streams')

def check_merge_agent_arguments(func, in_streams, out_stream, call_streams, name):
    check_function_type(name, func)
    check_list_of_streams_type(list_of_streams=in_streams,
                          agent_name=name, parameter_name='in_streams')
    check_stream_type(name, 'out_stream', out_stream)
    check_list_of_streams_type(list_of_streams=call_streams,
                          agent_name=name, parameter_name='call_streams')

def check_zip_agent_arguments(in_streams, out_stream, name):
    check_list_of_streams_type(list_of_streams=in_streams,
                          agent_name=name, parameter_name='in_streams')
    check_stream_type(name, 'out_stream', out_stream)

def check_split_agent_arguments(func, in_stream, out_streams, call_streams, name):
    check_function_type(name, func)
    check_stream_type(name, 'in_stream', in_stream)
    check_list_of_streams_type(list_of_streams=out_streams,
                          agent_name=name, parameter_name='out_streams')
    check_list_of_streams_type(list_of_streams=call_streams,
                          agent_name=name, parameter_name='call_streams')

def check_many_agent_arguments(func, in_streams, out_streams, call_streams, name):
    """ Checks the types of arguments used by an agent.

    """
    
    check_function_type(name, func)

    check_list_of_streams_type(list_of_streams=in_streams,
                          agent_name=name, parameter_name='in_streams')
    check_list_of_streams_type(list_of_streams=out_streams,
                          agent_name=name, parameter_name='out_streams')
    check_list_of_streams_type(list_of_streams=call_streams,
                          agent_name=name, parameter_name='call_streams')

def check_window_and_step_sizes(name, window_size, step_size):
    assert isinstance(window_size, int), \
      'window_map_agent {0} created with window_size {1} that is not an int'.format(
          name, window_size)
    assert isinstance(step_size, int), \
      'window_map_agent {0} created with step_size {1} that is not an int'.format(
          name, step_size)
    assert window_size > 0, \
      'window_map_agent {0} created with window_size {1} that is not positive'.format(
          name, window_size)
    assert step_size > 0, \
      'window_map_agent {0} created with step_size {1} that is not positive'.format(
          name, step_size)


