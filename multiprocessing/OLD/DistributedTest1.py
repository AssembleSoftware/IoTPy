import sys
import os
import pika
import json
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
from stream import Stream
from Distributed import DistributedProcess

#===================================================================
# DEFINE PROCESS FUNCTION f1
#===================================================================
def f1():
    from sink import sink_element
    u = Stream('u')
    def f(x): print x
    sink_element(f, u)
    return [], [u], []
    #return sources, in_streams, out_streams

proc1 = DistributedProcess(f1, name='process_1')
proc1.connect_process()
proc1.start()
