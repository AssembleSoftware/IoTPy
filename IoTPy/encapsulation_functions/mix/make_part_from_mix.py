from IoTPy.code.stream import Stream
from IoTPy.code.agents.merge import asynch_merge

x = Stream('x')
y = Stream('y')


def f(v): return 2 * v


def g(v, state): return v + state, v + state


def h(v, state, arg_0): return v + state + arg_0, v + state


def ff(v, arg_0): return v * arg_0


def make_part_from_mix(params):
    """
    Makes a part from the mix template given its arguments.

    Parameters
    ----------
    template_arguments: str
       A JSON string that specifies the values of the parameters of
       the mix template. The parameters are:
       in: list of Stream
       out: a Stream

    Returns
    -------
       The part that was made.

    """
    in_streams = params["in"]
    out_stream = params["out"]

    mix_agent = asynch_merge(
        in_streams=in_streams,
        out_stream=out_stream)

    return mix_agent
