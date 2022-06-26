from stream import Stream
from example_operators import join_synch

class Count(object):
    def __init__(self, n):
        self.n = n

def process_target_merge(dict_queues):
    
    #-------------------------------------------
    # 1. SPECIFY INPUT QUEUES FOR THE PROCESSES
    #-------------------------------------------
    # Specify that the input stream for THIS process
    # is dict_queues['q_root']
    Stream.scheduler.input_queue = dict_queues['q_root']
    
    #-------------------------------------------
    # 2. SPECIFY STREAMS IN THIS PROCESS
    #-------------------------------------------
    x, y = Stream('x'), Stream('y')
    
    #-------------------------------------------
    # 3. SPECIFY EXTERNAL STREAMS 
    #-------------------------------------------
    # This process does not modify external streams.
    
    #-------------------------------------------
    # 4. SPECIFY CALLBACK FUNCTIONS IN THIS PROCESS
    #-------------------------------------------
    def callback(alist, count):
        print ('merge ', sum(alist))
        count.n -= 1
        if count.n <= 0:
            Stream.scheduler.halted = True
        
    #-------------------------------------------
    # 5. SPECIFY AGENTS IN THIS PROCESS
    #-------------------------------------------
    join_synch(in_streams=[x, y], func=callback, count=Count(4))
    
    #-------------------------------------------
    # 6. START SCHEDULER AND THUS START THIS PROCESS
    #-------------------------------------------
    Stream.scheduler.start()

    
    
