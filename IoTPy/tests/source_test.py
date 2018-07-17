"""
This module tests source.py

"""

import sys
import os
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))

from agent import Agent
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from source import *

def test_source():
    import random
    import multiprocessing
    import time

    scheduler = Stream.scheduler
    from op import map_element, map_list
    from merge import zip_stream, zip_stream_f

    # Function created by the source agent
    test_list = []
    def random_integer(test_list, a, b):
        return_value = random.randint(a, b)
        test_list.append(return_value)
        return return_value
    def read_list(state, in_list):
        return in_list[state], state+1

    a = Stream('a')
    q = Stream('q')
    r = Stream('r')
    s = Stream('s')
    t = Stream('t')
    u = Stream('u')
    sb = Stream('sb')
    sc = Stream('sc')

    filename = 'test.dat'
    with open(filename, 'w') as output_file:
        for i in range(10):
            output_file.write(str(i) + '\n')

    scheduler.name_to_stream = {'s': s, 'r':r, 'a':a}
    vv = source_function(
        func=random_integer, out_stream=s, num_steps=5,
        name='random', window_size=2,
        test_list=test_list, a=10, b=20)
    
    ww = source_list(
        in_list=range(10), out_stream=r, num_steps=5,
        name='read list', window_size=2)
        
    xx = source_file(
        func=lambda x: 2*int(x), out_stream=a, filename='test.dat',
        time_interval=0.5, num_steps=None)
    

    map_element(lambda x: 2*x, s, t)
    def f(lst):
        return [10*v for v in lst]
    map_list(f, t, u)
    map_element(lambda x: x*x, r, q)
    p = zip_stream_f([u,q])

    map_element(lambda x: x*x, sb, sc)

    import Queue
    que = Queue.Queue()
    test_list_source_to_queue = []
    def sqf():
        return random_integer(test_list_source_to_queue, 1, 10)
    sqq = func_to_q(func=sqf, q=que, state=None, sleep_time=0.1, num_steps=5,
                name='source_to_q')
    q_to_streams_queue = Queue.Queue()
    q_to_streams_test_list = range(5)
    q_to_streams_test_list_0 = []
    q_to_streams_test_list_1 = []
    for v in q_to_streams_test_list:
        if v%2:
            q_to_streams_queue.put(('q2s_0', v))
            q_to_streams_test_list_0.append(v)
        else:
            q_to_streams_queue.put(('q2s_1', v))
            q_to_streams_test_list_1.append(v)
    q_to_streams_queue.put('_close')
    q2s_0 = Stream('q2s_0')
    q2s_1 = Stream('q2s_1')
    q2sss = q_to_streams(q=q_to_streams_queue, out_streams=[q2s_0, q2s_1])

    q2s_general_queue = Queue.Queue()
    q2s_test_list = range(5)
    
    
    random_thread, random_thread_ready = vv
    list_thread,list_thread_ready = ww
    file_thread, file_thread_ready = xx
    q_thread, q_thread_ready = sqq
    q2s_thread, q2s_thread_ready = q2sss
    
    random_thread.start()
    list_thread.start()
    file_thread.start()
    q_thread.start()
    q2s_thread.start()

    
    random_thread_ready.wait()
    list_thread_ready.wait()
    file_thread_ready.wait()
    q_thread_ready.wait()
    q2s_thread_ready.wait()
    
    sb.extend(range(5))
    
    #random_thread.join()
    list_thread.join()
    file_thread.join()
    q_thread.join()
    q2s_thread.join()

    scheduler.start()
    random_thread.join()
    scheduler.join()

    assert recent_values(s) == test_list
    assert recent_values(r) ==  range(10)
    assert recent_values(a) == [v*2 for v in range(10)]
    assert recent_values(t) == [v*2 for v in recent_values(s)]
    assert recent_values(u) == [v*10 for v in recent_values(t)]
    assert recent_values(q) == [v*v for v in recent_values(r)]
    assert recent_values(p) == zip(*[recent_values(u), recent_values(q)])
    assert recent_values(sc) == [x*x for x in range(5)]

    que_contents = []
    while not que.empty():
        que_contents.append(que.get())
    assert test_list_source_to_queue == que_contents
    assert recent_values(q2s_0) == q_to_streams_test_list_0
    assert recent_values(q2s_1) == q_to_streams_test_list_1
    print 'SOURCE TEST IS SUCCESSFUL!'

if __name__ == '__main__':
    test_source()
