import sys

from IoTPy.code.stream import Stream
from IoTPy.code.agents.window_agent import dynamic_window_agent

x = Stream('x')
y = Stream('y')


def f(v): return 2 * v


def g(v, state): return v + state, v + state


def h(v, state, arg_0): return v + state + arg_0, v + state


def ff(v, arg_0): return v * arg_0


def make_part_from_dynamic_window(params):
    """
    Makes a part from the dynamic window template given its arguments.

    Parameters
    ----------
    template_arguments: str
       A JSON string that specifies the values of the parameters of
       the dynamic window template. The parameters are:
       in: a Stream
       out: a Stream
       function: a Python function
       min_window_size : int
       max_window_size : int
       step_size : int
       initial_state: (optional) arbitrary
       parameters : (optional) list

    Returns
    -------
       The part that was made.

    """
    in_stream = params["in"]
    out_stream = params["out"]
    func = params["function"]

    min_window_size = params["min_window_size"]
    max_window_size = params["max_window_size"]
    step_size = params["step_size"]
    initial_state = params["initial_state"]
    parameters = params["parameters"]

    if parameters is None:
        parameters = []
    if initial_state is None:
        initial_state = []

    state = [0, False, False] + initial_state

    window_agent = dynamic_window_agent(
        func=func,
        in_stream=in_stream,
        out_stream=out_stream,
        state=state,
        args=parameters,
        min_window_size=min_window_size,
        max_window_size=max_window_size,
        step_size=step_size)

    return window_agent
