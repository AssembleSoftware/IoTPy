from IoTPy.code.stream import Stream
from IoTPy.code.agents.sink import element_sink_agent

x = Stream('x')
y = Stream('y')


def f(v): return 2 * v


def g(v, state): return v + state, v + state


def h(v, state, arg_0): return v + state + arg_0, v + state


def ff(v, arg_0): return v * arg_0


def make_part_from_sink(params):
    """
    Makes a part from the sink template given its arguments.

    Parameters
    ----------
    template_arguments: str
       A JSON string that specifies the values of the parameters of
       the sink template. The parameters are:
       in: a Stream
       function: a Python function
       initial_state: (optional) arbitrary
       parameters: (optional) list of arguments of function

    Returns
    -------
       The part that was made.

    """
    in_stream = params["in"]
    func = params["function"]

    initial_state = params["initial_state"]
    parameters = params["parameters"]

    sink_agent = element_sink_agent(
        func,
        in_stream,
        initial_state,
        None,
        None,
        *parameters)

    return sink_agent
