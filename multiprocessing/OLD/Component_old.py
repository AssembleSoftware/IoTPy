import sys
import os
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../helper_functions"))
from sink import stream_to_queue
from source import q_to_streams, source_function
from compute_engine import ComputeEngine
from stream import Stream
from recent_values import recent_values
import multiprocessing
import threading
import time



#===================================================================
# CORE MULTIPROCESSING CODE
#===================================================================

def connect_outputs(out_streams, out_to_in):
    """
    Parameters
    ----------
    out_streams: list of Stream
            list of out_streams
    out_to_in: dict
       key: str
            Name of an out_stream
       value: name_and_queue_list
              list of pairs where each pair is:
              (1) name: pickled object,
                    e.g. str: the name of the target stream,
                    or
                    e.g. pair (str, int) where str is the name
                    of an array of target streams and int
                    is an index into the array. 
              (2) queue: Queue. or multiprocessing.Queue
                      The target queue
               
    Notes
    -----
    Creates an agent that does the following:
    for each element of each stream in out_to_in.keys(), the
    agent puts the tuple (stream name, element) on to each queue
    in name_and_queue_list.

    """
    # name_to_stream is a dict: sending_stream_name -> sending_stream
    name_to_stream = {s.name: s for s in out_streams}
    for sending_stream_name, name_and_queue_list in out_to_in.items():
        # name_and_queue list is a list of pairs, where each pair is:
        # (receiving stream name, receiving queue)
        for name_and_queue in name_and_queue_list:
            receiver_stream_name, receiver_queue = name_and_queue
            sending_stream = name_to_stream[sending_stream_name]
            # stream_to_queue is an agent that puts tuples on the 
            # receiving queue where each tuple is:
            # (receiver stream name, element of the sending stream)
            stream_to_queue(
                sending_stream, receiver_queue, lambda x: [receiver_stream_name, x],
                name='stream_to_queue_'+ sending_stream_name + receiver_stream_name)

def connect(in_queue, in_streams, out_streams, out_to_in,
            q_thread_name='connect_q_thread'):
    connect_outputs(out_streams, out_to_in)
    ## return q_to_streams(in_queue, in_streams, q_thread_name) \
    ##   if in_queue is not None \
    ##   else (None, None)
    # name_to_stream is a dict: sending_stream_name -> sending_stream
    

def target_of_make_process(
        func, in_queue, out_to_in):
    sources, in_streams, out_streams = func()
    print 'in target_of_make_process. in_streams is '
    for stream in in_streams: print stream.name
    # Connect to other processes
    #q_thread, q_thread_ready = connect(in_queue, in_streams, out_streams, out_to_in)
    connect(in_queue, in_streams, out_streams, out_to_in)
    #connect_outputs(out_streams, out_to_in)

    for ss in sources:
        ss_thread, ss_ready = ss
        ss_thread.start()

    ## if q_thread:
    ##     q_thread.start()

    print 'started sources'
    for ss in sources:
        ss_thread, ss_ready = ss
        ss_ready.wait()

    print 'finished wait'
    for ss in sources:
        ss_thread, ss_ready = ss
        ss_thread.join()
    print 'finished source join'

    ## if q_thread_ready:
    ##     q_thread_ready.wait()

    print 'FINISHED SOURCES'

    ## if q_thread:
    ##     q_thread.join()
    
    Stream.scheduler.start()
    print 'Started scheduler'
    Stream.scheduler.join()
    print 'Joined scheduler'

def make_process(func, in_queue, out_to_in):
    return multiprocessing.Process(
        target=target_of_make_process,
        kwargs={
            'func': func,
            'in_queue': in_queue,
            'out_to_in': out_to_in
            }
        )


#===================================================================
# TESTS
#===================================================================
    
def test():
    import sys
    import os
    sys.path.append(os.path.abspath("../agent_types"))
    sys.path.append(os.path.abspath("../core"))
    sys.path.append(os.path.abspath("../helper_functions"))
    from sink import stream_to_queue
    from source import q_to_streams, source_function
    from compute_engine import ComputeEngine
    from stream import Stream
    from recent_values import recent_values
    import multiprocessing
    import threading
    import time
    import random
    from op import map_element
    from sink import sink_element
    from source import source_to_stream

    #===================================================================
    # DEFINE QUEUES
    #===================================================================
    queue_f = multiprocessing.Queue()
    queue_g = multiprocessing.Queue()

    #===================================================================
    # DEFINE PROCESS FUNCTION f
    #===================================================================
    

    def f_function():
        xxx = range(100)
        cd = ComputeEngine("cd")
        print 'Stream.scheduler in f_function is ', cd
        print 'Stream scheduler name is ', cd.name
        Stream.scheduler = cd
        Stream.scheduler.input_queue = queue_f
        print
        s = Stream('s')
        t = Stream('t')
        
        def ff(x):
            return x*10
        def gg(state):
            return state+1, state+1

        map_element(
            func=ff, in_stream=s, out_stream=t, name='aaaa')
        ss = source_function(
            func=gg, stream_name='s',
            time_interval=0.1, num_steps=10, state=0, window_size=1,
            name='source')
        sources = [ss]
        in_streams = [s]
        out_streams = [t]
        name_to_stream = {s.name: s for s in in_streams}
        print '================================================'
        print 'in connect'
        print 'Stream.scheduler is ', Stream.scheduler
        print 'name_to_stream is ', name_to_stream
        print
        Stream.scheduler.name_to_stream = name_to_stream
        return sources, in_streams, out_streams


    #===================================================================
    # DEFINE PROCESS FUNCTION g
    #===================================================================
    
    
    def g_function():
        import sys
        import os
        sys.path.append(os.path.abspath("../agent_types"))
        sys.path.append(os.path.abspath("../core"))
        sys.path.append(os.path.abspath("../helper_functions"))
        from sink import stream_to_queue
        from source import q_to_streams, source_function
        from compute_engine import ComputeEngine
        from stream import Stream
        from recent_values import recent_values
        import multiprocessing
        import threading
        import time
        import random
        ce = ComputeEngine("ce")
        print 'Stream.scheduler in g_function is ', ce
        print 'Stream scheduler name is ', ce.name
        Stream.scheduler = ce
        Stream.scheduler.input_queue = queue_g
        print
        t = Stream('t')
        u = Stream('u')
        t1 = Stream('t1')
        def g_print(y):
            print 'in g_print. y is ', y
            return y*2
        def gg_print(y):
            print 'In g_function. gg_print() y is', y
            return 100*y
        map_element(
            func=g_print, in_stream=t, out_stream=t1, name='b')
        map_element(
            func=gg_print, in_stream=t1, out_stream=u, name='b1')
        sources = []
        in_streams = [t]
        out_streams = [u]
        
        name_to_stream = {s.name: s for s in in_streams}
        print '================================================'
        print 'Stream.scheduler is ', Stream.scheduler
        print 'name_to_stream is ', name_to_stream
        print
        Stream.scheduler.name_to_stream = name_to_stream
    
        return sources, in_streams, out_streams

    
    

    #===================================================================
    # DEFINE PROCESSES
    #===================================================================
    pqg = make_process(g_function, queue_g, {})
    pqf = make_process(f_function, queue_f, {'t': [('t', queue_g)]})
    
    
    #===================================================================
    # START AND JOIN PROCESSES
    #===================================================================
    pqf.start()
    pqg.start()

    pqf.join()
    pqg.join()
    ## print 'MULTIPROCESSOR TEST IS SUCCESSFUL'


if __name__ == '__main__':
    test()
