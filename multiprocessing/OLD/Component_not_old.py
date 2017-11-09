"""
This module consists of functions for making a multiprocess program
that runs on a multicore (shared-memory) computer. For distributed
computing, using APMQ, with multiple computers with different IP
addresses, see the module DistributedComputing.py.

Functions in the module:
1. connect_outputs: connects output streams of functions on a process
to input streams of functions on other processes
2. target_of_make_process: the target function for make process. This
function calls the encapsulated function func, and starts threads.
3. make_process: makes a process.

"""
import sys
import os
sys.path.append(os.path.abspath("../agent_types"))
sys.path.append(os.path.abspath("../core"))
from sink import stream_to_queue
from compute_engine import ComputeEngine
from stream import Stream
import multiprocessing



def connect_outputs(out_streams, out_to_in):
    """
    Parameters
    ----------
    out_streams: list of Stream
            list of output streams of the function.
            These output streams can be fed to queues in
            other processes. Each of these output streams
            must have a unique name.
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
                  This name is the name of the input stream
                  of a function in the receiver process. This
                  name may be different from the name of the 
                  stream in the sending process.
              (2) queue: multiprocessing.Queue
                      The queue in a receiver process.
               
    Notes
    -----
    Creates an agent that does the following:
    for each stream s with a name, s.name, in out_to_in.keys(),
    for each element v of stream s, the  agent obtains
    out_to_in[s.name] which is a name_and_queue_list.
    For each receiver_name, receiver_queue in name_and_queue_list,
    the agent puts [receiver_name, v] in receiver_queue.
    The receiving process then appends v to the stream in the
    receiving process with the name, receiver_name.

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
            # For help in debugging we give a name to this agent:
            # stream_to_queue, sending and receiving stream names.
            stream_to_queue(
                sending_stream, receiver_queue,
                lambda x: [receiver_stream_name, x],
                name=('stream_to_queue_'+ sending_stream_name +
                      receiver_stream_name)
                      )


def target_of_make_process(
        func, in_queue, out_to_in, name):
    """
    Parameters
    ----------
    func: function
       func is the function that is encapsulated by
       make_process.
       func has no arguments and returns:
       (1) sources: the source threads used to
       obtain data from sources in the function.
       (2) in_streams: the input streams of the
       function.
       (3) out_streams: the output streams of the
       function.
    in_queue: multiprocessing.Queue
       in_queue is the receiving queue of the process.
       Streams from other processes and from sources in
       this process are fed to in_queue.
    out_to_in: dict
       See connect_outputs()
       key: output stream name
       value: list of receiver stream names and receiver
       queues
    name: str (optional)
       name that is helpful in debugging.

    Returns
    -------
       None

    """
    # Create a new Stream.scheduler and set its input
    # queue to in_queue so that streams from other
    # processes that are fed to in_queue are operated
    # on by the scheduler.
    Stream.scheduler = ComputeEngine(name)
    Stream.scheduler.input_queue = in_queue
    # Obtain the externalities of func, i.e. its
    # source threads, and input and output streams.
    sources, in_streams, out_streams = func()
    name_to_stream = {s.name: s for s in in_streams}
    Stream.scheduler.name_to_stream = name_to_stream
    # Connect the output streams to other processes
    connect_outputs(out_streams, out_to_in)
    # Start the source threads and wait for the source
    # threads to be ready to execute
    for ss in sources:
        ss_thread, ss_ready = ss
        ss_thread.start()
    for ss in sources:
        ss_thread, ss_ready = ss
        ss_ready.wait()
    # Start the scheduler for this process
    Stream.scheduler.start()
    # Join the source threads. The source threads may
    # execute for ever in which case this join() will not
    # terminate.
    for ss in sources:
        ss_thread, ss_ready = ss
        ss_thread.join()
    # Join the scheduler for this process. The scheduler
    # may execute for ever, and so this join() may not
    # terminate. You can set the scheduler to run for a
    # fixed number of steps during debugging.
    Stream.scheduler.join()


def make_process(
        func, in_queue, out_to_in, name="process name"):
    """
    See target_of_make_process()

    """
    return multiprocessing.Process(
        target=target_of_make_process,
        kwargs={
            'func': func,
            'in_queue': in_queue,
            'out_to_in': out_to_in,
            'name': name
            }
        )


#===================================================================
# TESTS
#===================================================================
    
def test():
    
    #===================================================================
    # DEFINE QUEUES
    #===================================================================
    queue_f = multiprocessing.Queue()
    queue_g = multiprocessing.Queue()

    #===================================================================
    # DEFINE PROCESS FUNCTION f
    #===================================================================
    

    def f_function():
        from source import source_function
        from op import map_element
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

        return sources, in_streams, out_streams


    #===================================================================
    # DEFINE PROCESS FUNCTION g
    #===================================================================
    
    
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
        sources = []
        in_streams = [t]
        out_streams = [u]
    
        return sources, in_streams, out_streams

    
    

    #===================================================================
    # DEFINE PROCESSES
    #===================================================================
    pqg = make_process(g_function, queue_g, {}, name='g')
    pqf = make_process(f_function, queue_f, {'t': [('t', queue_g)]}, name='f')
    
    
    #===================================================================
    # START AND JOIN PROCESSES
    #===================================================================
    pqf.start()
    pqg.start()

    pqf.join()
    pqg.join()
    print 'MULTIPROCESSOR TEST FINISHED'
#======================================================================
def test_2():
#======================================================================
    
    #===================================================================
    # DEFINE QUEUES
    #===================================================================
    q0 = multiprocessing.Queue()
    q1 = multiprocessing.Queue()

    #===================================================================
    # DEFINE PROCESS FUNCTION f
    #===================================================================

    def f0():
        from source import source_function
        from op import map_element
        import random
        s = Stream('s')
        t = Stream('t')
        def f(): return random.random()
        def g(x): return int(100*x)
        map_element(g, s, t)
        random_source = source_function(
            func=f, stream_name='s', time_interval=0.1, num_steps=10)
        return [random_source], [s], [t]
        #return sources, in_streams, out_streams


    #===================================================================
    # DEFINE PROCESS FUNCTION g
    #===================================================================
    
    def f1():
        from sink import sink_element
        u = Stream('u')
        def f(x): print x
        sink_element(f, u)
        return [], [u], []
        #return sources, in_streams, out_streams


    #===================================================================
    # DEFINE PROCESSES
    #===================================================================
    proc0 = make_process(f0, q0, {'t': [('u',q1)]})
    proc1 = make_process(f1, q1, {})
    
    
    #===================================================================
    # START AND JOIN PROCESSES
    #===================================================================
    proc0.start()
    proc1.start()

    proc0.join()
    proc1.join()
    print 'MULTIPROCESSOR TEST FINISHED'

if __name__ == '__main__':
    test()
    test_2()
