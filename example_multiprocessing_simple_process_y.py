import json
import multiprocessing as mp
from stream import Stream
from example_operators import single_item

class Count(object):
    """
    Persistent integer used in callbacks.
    """
    
    def __init__(self, N):
        self.N = N
    def decrement(self):
        self.N -= 1
    def is_positive(self):
        return self.N > 0

def process_target_y(dict_queues):
    
    #-------------------------------------------
    # 1. SPECIFY INPUT QUEUES FOR THE PROCESSES
    #-------------------------------------------
    q_x = dict_queues['x']
    q_y = dict_queues['y']
    Stream.scheduler.input_queue = q_y
    
    #-------------------------------------------
    # 2. SPECIFY STREAMS IN THIS PROCESS
    #-------------------------------------------
    y = Stream(name='y')
    
    #-------------------------------------------
    # 3. SPECIFY CALLBACK FUNCTIONS IN THIS PROCESS
    #-------------------------------------------
    
    count = Count(3)
            
    def callback_y(stream_item, count):
        if not count.is_positive():
            json_data = json.dumps(('scheduler', 'halt'))
            q_x.put(json_data)
            Stream.scheduler.halted = True
            return
        print('message received by process y: ', stream_item)
        receiver_stream_name = 'x'
        message = (receiver_stream_name, [stream_item+1])
        json_message = json.dumps(message)
        q_x.put(json_message)
        count.decrement()
    
    #-------------------------------------------
    # 4. SPECIFY AGENTS IN THIS PROCESS
    #-------------------------------------------
    single_item(in_stream=y, func=callback_y, count = count)
    # Initiate computation by sending 1 on stream called 'x'
    q_x.put(json.dumps(('x', [1])))
    
    #-------------------------------------------
    # 5x. START SCHEDULER
    #-------------------------------------------
    Stream.scheduler.start()

    return
