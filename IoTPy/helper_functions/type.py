from ..core.agent import Agent, InList
from ..core.stream import StreamArray, Stream, _no_value, _multivalue
from ..agent_types.op import map_element
from .recent_values import recent_values

def dtype_float(stream):
    s = StreamArray(dtype=float)
    map_element(func=lambda v: float(v), in_stream=stream, out_stream=s)
    return s

def dtype_int(stream):
    s = StreamArray(dtype=int)
    map_element(func=lambda v: int(v), in_stream=stream, out_stream=s)
    return s

def dtype_double(stream):
    s = StreamArray(dtype=double)
    map_element(func=lambda v: double(v), in_stream=stream, out_stream=s)
    return s



