
import sys
import os
import pika
import json
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
from stream import Stream
from Distributed import DistributedProcess
#===================================================================
# DEFINE PROCESS FUNCTION f0
#===================================================================
def f0():
    from source import source_function
    from op import map_element
    import random
    s = Stream('s')
    t = Stream('t')
    def f(): return random.random()
    def g(x): return {'h':int(100*x), 't':int(10*x)}
    map_element(g, s, t)
    random_source = source_function(
        func=f, stream_name='s', time_interval=0.1, num_steps=10)
    return [random_source], [s], [t]
    #return sources, in_streams, out_streams

proc0 = DistributedProcess(f0, name='process_0')

proc0.attach_remote_stream(
    sending_stream_name='t',
    receiving_process_name='process_1',
    receiving_stream_name='u')

proc0.connect_process()
proc0.start()
