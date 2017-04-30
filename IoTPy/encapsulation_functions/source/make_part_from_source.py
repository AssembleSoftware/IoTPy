from IoTPy.code.stream import Stream
from IoTPy.code.agents.source import function_to_stream

x = Stream('x')
y = Stream('y')


def f(v): return 2 * v


def g(v, state): return v + state, v + state


def h(v, state, arg_0): return v + state + arg_0, v + state


def ff(v, arg_0): return v * arg_0


def make_part_from_source(params):
    """
    Makes a part from the source template given its arguments.

    Parameters
    ----------
    template_arguments: str
       A JSON string that specifies the values of the parameters of
       the source template. The parameters are:
       out: a Stream
       function: a Python function
       initial_state: (optional) arbitrary
       parameters: (optional) list of arguments of function

    """
    out_stream = params["out"]
    func = params["function"]

    initial_state = params["initial_state"]
    parameters = params["parameters"]
    if parameters is None:
        parameters = []

    push = params["push"]
    time_interval = params["time_interval"]
    if time_interval is None:
        time_interval = 0

    stream_length = params["stream_length"]

    thread, out_stream = function_to_stream(func, time_interval, stream_length,
                                            initial_state, out_stream, push,
                                            *parameters)
    # thread.daemon = True
    thread.start()
