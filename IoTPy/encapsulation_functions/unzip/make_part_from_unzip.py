from IoTPy.code.stream import Stream
from IoTPy.code.agents.split import unzip_agent

x = Stream('x')
y = Stream('y')


def f(v): return 2 * v


def g(v, state): return v + state, v + state


def h(v, state, arg_0): return v + state + arg_0, v + state


def ff(v, arg_0): return v * arg_0


def make_part_from_unzip(params):
    """
    Makes a part from the unzip template given its arguments.

    Parameters
    ----------
    template_arguments: str
       A JSON string that specifies the values of the parameters of
       the unzip template. The parameters are:
       in: a Stream
       out: list of Stream

    Returns
    -------
       The part that was made.

    """
    in_stream = params["in"]
    out_streams = params["out"]

    unzip_agent(
        in_stream=in_stream,
        out_streams=out_streams)

    return unzip_agent
