from stream import Stream, ExternalStream
from example_operators import single_item

class Count(object):
    """
    Persistent integer used in callbacks.
    """
    
    def __init__(self, n):  self.n = n

def process_target_y(dict_queues):
    
    #-------------------------------------------
    # 1. SPECIFY INPUT QUEUES FOR THE PROCESSES
    #-------------------------------------------
    Stream.scheduler.input_queue = dict_queues['y']
    
    #-------------------------------------------
    # 2. SPECIFY STREAMS IN THIS PROCESS
    #-------------------------------------------
    y = Stream(name='y')
    
    #-------------------------------------------
    # 3. SPECIFY EXTERNAL STREAMS 
    #-------------------------------------------
    x = ExternalStream(name='x', queue=dict_queues['x'])
    
    #-------------------------------------------
    # 4. SPECIFY CALLBACK FUNCTIONS IN THIS PROCESS
    #-------------------------------------------
    
    count = Count(3)
            
    def callback_y(stream_item, count):
        if not count.n > 0:
            x.append('__halt__')
            Stream.scheduler.halted = True
            return
        print('message received by process y: ', stream_item)
        x.append(stream_item+1)
        count.n -= 1
    
    #-------------------------------------------
    # 5. SPECIFY AGENTS IN THIS PROCESS
    #-------------------------------------------
    single_item(in_stream=y, func=callback_y, count = count)
    # Initiate computation by sending 1 on external stream x
    x.append(1)
    
    #-------------------------------------------
    # 6. START SCHEDULER
    #-------------------------------------------
    Stream.scheduler.start()
