import sys
import os
sys.path.append(os.path.abspath("../multiprocessing"))
sys.path.append(os.path.abspath("../core"))

from Multicore import StreamProcess, single_process_single_source
from Multicore import single_process_multiple_sources
from stream import Stream
from merge import zip_stream

#===================================================================
# TESTS
#===================================================================
    
def test_1():
    
    #===================================================================
    #  DEFINE FUNCTIONS TO BE ENCAPSULATED
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
            func=gg, stream=s,
            time_interval=0.1, num_steps=10, state=0, window_size=1,
            name='source')
        print 'ss is ', ss
        #return sources, in_streams, out_streams
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
    print "CREATE PROCESS"
    pqgs = StreamProcess(g_function, name='g')
    pqfs = StreamProcess(f_function, name='f')

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
        from source import source_function
        from op import map_element
        import random
        s = Stream('s')
        t = Stream('t')
        def f(): return random.random()
        def g(x): return {'h':int(100*x), 't':int(10*x)}
        map_element(func=g, in_stream=s, out_stream=t)
        random_source = source_function(
            func=f, stream=s, time_interval=0.1, num_steps=10)
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
    proc0 = StreamProcess(f0, name='process 0')
    proc1 = StreamProcess(f1, name='process 1')

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

    
def test_0():

    def h(s):
        from op import map_element
        from sink import stream_to_file
        
        def ff(x): return x*10

        t = Stream()
            
        map_element(
            func=ff, in_stream=s, out_stream=t)
        stream_to_file(in_stream=t, filename='test.dat')

    def gg(state):
        return state+1, state+1

    def source_input(stream):
        from source import source_function
        return source_function(
            func=gg, stream=stream,
            time_interval=0.1, num_steps=10, state=0, window_size=1)
    
    #===================================================================
    #  DEFINE FUNCTIONS TO BE ENCAPSULATED
    #===================================================================
    def f_function():
        
        s = Stream('s')
        
        h(s)
        
        #return sources, in_streams, out_streams
        return [source_input(stream=s)], [s], []

    
    #===================================================================
    #===================================================================
    #  5 STEPS TO CREATE AND CONNECT PROCESSES
    #===================================================================
    #===================================================================
    
    #===================================================================
    # 1. CREATE PROCESSES
    #===================================================================
    pqfs = StreamProcess(f_function, name='f')

    #===================================================================
    # 2. ATTACH STREAMS
    #===================================================================

    #===================================================================
    # 3. CONNECT PROCESSES
    #===================================================================
    pqfs.connect_process()
    
    #===================================================================
    # 4. START PROCESSES
    #===================================================================
    pqfs.start()
    
    #===================================================================
    # 5. JOIN PROCESSES
    #===================================================================
    pqfs.join()

    return

def encapsulation(source_f, compute_f):
    
    def g():
        s = Stream('s')
        compute_f(s)
        return [source_f(s)], [s],[]
    pqfs = StreamProcess(g)
    pqfs.connect_process()
    pqfs.start()
    pqfs.join()
        
def test_single_process_single_source():

    def g(s):
        # A simple source which outputs 0, 1, 2, 3,.. on
        # stream s.
        def generate_sequence(state): return state+1, state+1

        # Return a thread object which takes 10 steps, and
        # sleeps for 0.1 seconds between successive steps, and
        # puts the next element of the sequence in stream s,
        # and starts the sequence with value 0.
        from source import source_function
        return source_function(
            func=generate_sequence, stream=s,
            time_interval=0.1, num_steps=10, state=0)

    def h(s):
        # A trivial example of a network of agents consisting
        # of two agents where the network has a single input
        # stream: s.
        # The first agent applies function f to each element 
        # of the input stream, s, and puts the result in its
        # output stream t.
        # The second agent puts values in its input stream t
        # on a file called test.dat.
        from op import map_element
        from sink import stream_to_file
        
        def f(x): return x*10
        t = Stream()
        map_element(
            func=f, in_stream=s, out_stream=t)
        stream_to_file(in_stream=t, filename='test.dat')

    # Create a process with two threads: a source thread and
    # a compute thread. The source thread executes the function
    # g, and the compute thread executes function h.
    single_process_single_source(source_f=g, compute_f=h)

def test_single_process_multiple_sources():
    from source import source_function
    import random

    def g_0(s):
        # A simple source which outputs 0, 1, 2, 3,.. on
        # stream s.
        def generate_sequence(state):
            return state+1, state+1

        # Return a thread object which takes 10 steps, and
        # sleeps for 0.1 seconds between successive steps, and
        # puts the next element of the sequence in stream s,
        # and starts the sequence with value 0.
        
        return source_function(
            func=generate_sequence, stream=s,
            time_interval=0.1, num_steps=10, state=0)

    def g_1(s):
        # A simple source which outputs random numbers
        # stream s.

        # Return a thread object which takes 12 steps, and
        # sleeps for 0.05 seconds between successive steps, and
        # puts the next element of the sequence in stream s.
        return source_function(
            func=random.random, stream=s,
            time_interval=0.05, num_steps=12)

    def h(list_of_two_streams):
        # A trivial example of a network of agents consisting
        # of two agents where the network has a single input
        # stream: s.
        # The first agent zips the two input streams and puts
        # the result on stream t.
        # The second agent puts values in its input stream t
        # on a file called output.dat.
        from sink import stream_to_file
        t = Stream()
        zip_stream(in_streams=list_of_two_streams, out_stream=t)
        stream_to_file(in_stream=t, filename='output.dat')

    # Create a process with three threads: two source threads and
    # a compute thread. The source threads execute the functions
    # g_0 and g_1, and the compute thread executes function h.
    single_process_multiple_sources(list_source_f=[g_0, g_1], compute_f=h)

if __name__ == '__main__':
    
    ## print 'test_single_process_multiple_sources'
    ## print
    ## test_single_process_multiple_sources()
    
    print 'test_single_process_single_source'
    print
    test_single_process_single_source()
    
    ## print "STARTING test_0"
    ## print
    ## test_0()
    
    ## print "STARTING test_1"
    ## print
    ## test_1()

    ## print "STARTING test_2"
    ## test_2()

