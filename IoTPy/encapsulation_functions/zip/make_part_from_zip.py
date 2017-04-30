from IoTPy.code.stream import Stream
from IoTPy.code.agents.merge import zip_agent

x = Stream('x')
y = Stream('y')


def f(v): return 2 * v


def g(v, state): return v + state, v + state


def h(v, state, arg_0): return v + state + arg_0, v + state


def ff(v, arg_0): return v * arg_0


def make_part_from_zip(params):
    """
    Makes a part from the zip template given its arguments.

    Parameters
    ----------
    template_arguments: str
       A JSON string that specifies the values of the parameters of
       the zip template. The parameters are:
       in: a Stream
       out: list of Stream

    Returns
    -------
       The part that was made.

    """
    in_streams = params['in']
    out_stream = params['out']
    zip_agent(
        in_streams=in_streams,
        out_stream=out_stream)

    return zip_agent
