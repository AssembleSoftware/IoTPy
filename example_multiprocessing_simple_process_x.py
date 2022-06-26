from stream import Stream, ExternalStream
from example_operators import single_item
    
def process_target_x(dict_queues):
    
    #-------------------------------------------
    # 1. SPECIFY INPUT QUEUES FOR THE PROCESSES
    #-------------------------------------------
    # Specify that the input stream for THIS process
    # is dict_queues['x']
    Stream.scheduler.input_queue = dict_queues['x']
    
    #-------------------------------------------
    # 2. SPECIFY STREAMS IN THIS PROCESS
    #-------------------------------------------
    x = Stream(name='x')
    
    #-------------------------------------------
    # 3. SPECIFY EXTERNAL STREAMS 
    #-------------------------------------------
    y = ExternalStream(name='y', queue=dict_queues['y'])
    
    #-------------------------------------------
    # 4. SPECIFY CALLBACK FUNCTIONS IN THIS PROCESS
    #-------------------------------------------
    def callback_x(stream_item):
        print('message received by process x: ', stream_item)
        y.append(stream_item+1)
        
    #-------------------------------------------
    # 5. SPECIFY AGENTS IN THIS PROCESS
    #-------------------------------------------
    single_item(in_stream=x, func=callback_x)
    
    #-------------------------------------------
    # 6. START SCHEDULER AND THUS START THIS PROCESS
    #-------------------------------------------
    Stream.scheduler.start()
