import sys
import os
import threading
import random
sys.path.append(os.path.abspath("../multiprocessing"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../../examples/timing"))

from multicore import StreamProcess, single_process_single_source
from multicore import single_process_multiple_sources
from multicore import make_process, run_multiprocess
from distributed import DistributedProcess
from stream import Stream
from op import map_element, map_window
from merge import zip_stream, blend
from source import source_func_to_stream, source_function, source_list
from sink import stream_to_file
from timing import offsets_from_ntp_server
from print_stream import print_stream

def test_1():
    
    #===================================================================
    #  DEFINE FUNCTIONS TO BE ENCAPSULATED
    #===================================================================
    def f_function():
        from source import source_func_to_stream
        from op import map_element
        s = Stream('s')
        t = Stream('t')
        
        def ff(x):
            return x*10
        def gg(state):
            return state+1, state+1

        map_element(
            func=ff, in_stream=s, out_stream=t, name='aaaa')
        ss = source_func_to_stream(
            func=gg, out_stream=s, time_interval=0.1, num_steps=10,
            window_size=1, state=0, name='source')
        # return sources, in_streams, out_streams
        return [ss], [s], [t]

    def g_function():
        from op import map_element
        t = Stream('t')
        u = Stream('u')
        t1 = Stream('t1')
        def g_print(y):
            return y*2
        def gg_print(y):
            print 'gg_print: y is', y
            return 100*y
        map_element(
            func=g_print, in_stream=t, out_stream=t1, name='b')
        map_element(
            func=gg_print, in_stream=t1, out_stream=u, name='b1')
        stream_to_file(u, 'test.dat')
        #return sources, in_streams, out_streams
        return [], [t], [u]

    #===================================================================
    #===================================================================
    #  5 STEPS TO CREATE AND CONNECT PROCESSES
    #===================================================================
    #===================================================================
    
    #===================================================================
    # 1. CREATE PROCESSES
    #===================================================================
    pqgs = DistributedProcess(func=g_function, name='g')
    pqfs = DistributedProcess(func=f_function, name='f')

    #===================================================================
    # 2. ATTACH STREAMS
    #===================================================================
    pqfs.attach_stream(
        sending_stream_name='t',
        receiving_process=pqgs,
        receiving_stream_name='t'
        )

    #===================================================================
    # 3. CONNECT PROCESSES
    #===================================================================
    pqgs.connect_process()
    pqfs.connect_process()
    
    #===================================================================
    # 4. START PROCESSES
    #===================================================================
    pqfs.start()
    pqgs.start()
    
    #===================================================================
    # 5. JOIN PROCESSES
    #===================================================================
    pqfs.join()
    pqgs.join()
    return

#======================================================================
def test_2():
#======================================================================

    #===================================================================
    # DEFINE PROCESS FUNCTION f0
    #===================================================================
    def f0():
        from source import source_func_to_stream
        from op import map_element
        import random
        s = Stream('s')
        t = Stream('t')
        def f(): return random.random()
        def g(x): return {'h':int(100*x), 't':int(10*x)}
        map_element(g, s, t)
        random_source = source_func_to_stream(
            func=f, out_stream=s, time_interval=0.1, num_steps=10)
        return [random_source], [s], [t]
        #return sources, in_streams, out_streams

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

    #===================================================================
    #===================================================================
    #  5 STEPS TO CREATE AND CONNECT PROCESSES
    #===================================================================
    #===================================================================


    #===================================================================
    # 1. CREATE PROCESSES
    #===================================================================
    proc0 = DistributedProcess(f0, name='process 0')
    proc1 = DistributedProcess(f1, name='process 1')

    #===================================================================
    # 2. ATTACH STREAMS
    #===================================================================
    proc0.attach_stream(
        sending_stream_name='t',
        receiving_process=proc1,
        receiving_stream_name='u'
        )

    #===================================================================
    # 3. CONNECT PROCESSES
    #===================================================================
    proc0.connect_process()
    proc1.connect_process()
    
    #===================================================================
    # 4. START PROCESSES
    #===================================================================
    proc0.start()
    proc1.start()
    print 'started'

    #===================================================================
    # 5. JOIN PROCESSES
    #===================================================================
    proc0.join()
    proc1.join()
    return

    print 'MULTIPROCESSOR TEST FINISHED'

if __name__ == '__main__':
    test_1()
    test_2()

