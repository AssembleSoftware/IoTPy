"""
This code implements the count min sketch algorithm for identifying frequent items described in the paper -
 G. Cormode and S. Muthukrishnan. An improved data stream summary: The count-min sketch and its applications. Journal of
Algorithms, 55(1):58-75, 2005. Conference version in Proceedings of Latin American Theoretical Informatics (LATIN), 2004.
Initial Technical Report published as DIMACS 2003-20, June 2003.
"""



import sys
import os
import random
import numpy as np
import pickle as p
import heapq

sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../timing"))

# multicore is in ../../IoTPy/multiprocessing
from multicore import shared_memory_process, Multiprocess

# stream is in ../../IoTPy/core
from stream import Stream

# op, sink, source, merge are in ../../IoTPy/agent_types
from op import map_element
from source import source_list
from source import source_list_to_stream
from sink import sink_window, sink_element

from recent_values import recent_values




# CREATE SOURCE THREADS.
# This thread generates the original stream from the stream list.
# Note that a finite stream should end with 'eof'
def source(out_stream):
    return source_list_to_stream(source_list, out_stream)


# FUNCTION TO MAKE AND RUN THE SHARED MEMORY PROCESS
def make_and_run_process(compute_func):
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc')
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()

#------------------------------------------------------------------
#THE COUNT MIN SKETCH ALGORITHM
#------------------------------------------------------------------

def count_min_sketch(n = 5,b = 5, k= 3, printer = 1000):


    """
    The count_sketch function runs the count_sketch 
    algorithm on the given stream.

     Attributes
    ----------
    n: int
        Specifies the number of hash functions
    b: int
        Specifies the number of bins in each hash function
    k: int
        Specifies the number of heavy hitter elements
    printer: int
        Spcifies the frequency at which the counter is to be printed
    """
    
    counter = np.zeros((n,b))

    #DEFINE HELPER FUNCTIONS TO MAKE A PSEUDO 2-WISE HASH FUNCTION

    def isprime(k):
        for i in range(3,int(k**0.5)+2,2):
            if k%i == 0:
                return False
            
        return True

    def gen_prime_no(m):
        mod = m%2
        for p in range(m+1+mod, 2*m+2, 2):
            if (isprime(p)):
                return p
            
    

    
    p = gen_prime_no(b)
     
    h = []


    #DEFINE HASH FUNCTION
    for i in range(n):  
        
        h2 = random.randint(1,p-1)
        h1 = random.randint(1,p-1)
        h0 = random.randint(0,p-1)
        t = (h2,h1,h0)
        h.append(t)
        
        
        state = [counter,0,[]]


    # DEFINE THE COMPUTATIONAL FUNCTION
    # Define the computational function for count min sketch
    def compute_func(in_streams, out_streams):
        # IDENTIFY INPUT AND OUTPUT STREAMS.
        # Original stream list = in_streams[0]

        # CREATE INTERNAL STREAMS.
        # Internal Stream - out 
        #                   It is used to output the top-k items and their counts after fixed intervals
        #                   Each element of the stream is a list of 2-sized tuples where,
        #                   tuple[1] = item
        #                   tuple[0] = its count
        #                      


        out = Stream()


        def count(counter,h,p,v):
            """
            Given the counter and the hash functions, this function returns the count of the item 

            Attributes
            ----------
            counter: 2-d array
                Stores the hash bucket values
            h: 2-dimensional list of ints
                defines the hash function used to decide which bucket the count of v should be added to 
            p: int
                the prime number used to create both the hash functions  
            v: int
                An element of the stream  

            Returns
            --------

            co: int
                Count of the input item       

            """


            co = -1
            for i in range(counter.shape[0]):
                v_bin = (v**2)*h[i][0] + v*h[i][1] + h[i][2]
                v_bin = v_bin%p%b

                temp = counter[i][v_bin]

                if co == -1 or temp<co:
                    co = temp

            return int(co)


        #DEFINE THE COUNTER UPDATER
        #Updates the counter for every value in the stream

        def counter_update(v, state, h,p,k):

            """
            This function updates the counter for a given value.
            If it sees the end of a finite stream it writes (pickles) the heap of top-k items
            into the file CMS.dat.

            Attributes
            ----------
            v: int
                An element of the stream
            state: multidimensional list
                state stores the hash bucket (called counter), number of elements seen and the heap containing the top-k elements
                counter = state[0]: 2-d array 
                number of elements = state[1]: int
                heap: = state[2]: array of 2-element tuples
            h: 2-dimensional list of ints
                defines the hash function used to decide which bucket the count of v should be added to 
            p: int
                the prime number used to create both the hash functions 
            k: int
                Specifies the number of heavy hitter elements   
            """


            counter = state[0]
            heap = state[2]
            

            if v == 'eof':
                heap = np.array(heap)
                
                np.savetxt("CMS.dat", heap)
                return state[2], state

            state[1] += 1

            for i in range(counter.shape[0]):
                v_bin = (v**2)*h[i][0] + v*h[i][1] + h[i][2]
                v_bin = v_bin%p%b

                counter[i][v_bin] += 1



            v_count = count(counter, h,p,v)

            if v_count >= state[1]/k:

                    for i in range(len(heap)):
                        if v == heap[i][1]:
                            heap[i] = (v_count,v)
                            heapq.heapify(heap)
                            break
                    else:
                        heapq.heappush(heap,(v_count,v))

            while len(heap) > k:
                heapq.heappop(heap)


            state[0] = counter
            state[2] = heap

            return  state[2], state

        def regular_print(v):  
            """ This function prints the last value of a window of the input stream
            """
            print v[-1]

        
        # CREATE AGENTS
        # Make the agent that applies the counter update
        # function to the input stream
        map_element(func = counter_update, in_stream = in_streams[0],out_stream = out, state = state, h=h, p=p, k=k)


        #Make the agent which prints the counter stream at regular intervals
        sink_window(func = regular_print, in_stream = out, window_size = printer , step_size = printer)

        

    # MAKE AND RUN THE SHARED MEMORY PROCESS    
    make_and_run_process(compute_func)

    

#-----------------------------------------------------------------------
#            TESTS
#-----------------------------------------------------------------------


if __name__ == '__main__':
    
    print('Running the reverberation test ... ')
    source_list = [1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,1,2,3,4,5,6,7, 'eof']
    count_min_sketch(printer = 10)
    print('reverb done')







