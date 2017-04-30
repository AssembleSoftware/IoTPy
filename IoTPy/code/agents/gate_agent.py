import sys
import os

from ..agent import Agent, InList
from ..stream import Stream, StreamArray
from ..stream import _no_value, _multivalue, _close
from element_agent import element_map_agent
import types
import inspect
import random

#-----------------------------------------------------------------------
# GATE: SINGLE INPUT STREAM, SINGLE OUTPUT STREAM
#-----------------------------------------------------------------------
def gate_agent(in_stream, out_stream, call_streams, name=None):
    """
    Parameters
    ----------
        in_stream: Stream
           The single input stream of the agent
        out_stream: Stream
           The single output stream of the agent
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
    def f(lst): return lst
    
    element_map_agent(func=f, in_stream=in_stream, out_stream=out_stream, call_streams=call_streams, name=name)

#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#                                     GATE AGENT TESTS
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
def test_gate_agents():
    s = Stream('s')
    u = Stream('u')
    v = Stream('v')
    x = Stream('x')

    # ------------------------------------
    # Test gate
    d = gate_agent(in_stream=x, out_stream=s, call_streams=[u, v], name='d')


    x.extend([1,2,3])
    assert s.stop == 0

    u.extend([1])
    assert s.stop == 3
    assert s.recent[:3] == [1, 2, 3]

    v.extend([2])
    assert s.stop == 3
    assert s.recent[:3] == [1, 2, 3]

    x.extend([4])
    assert s.stop == 3
    assert s.recent[:3] == [1, 2, 3]

    u.extend([3,4])
    assert s.stop == 4
    assert s.recent[:4] == [1, 2, 3, 4]

    
    return
    
if __name__ == '__main__':
    test_gate_agents()
    
    
    
    
    

