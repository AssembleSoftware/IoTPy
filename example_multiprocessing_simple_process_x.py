import json
import multiprocessing as mp
from stream import Stream
from example_operators import single_item
    
def process_target_x(dict_queues):
    
    #-------------------------------------------
    # 1. SPECIFY INPUT QUEUES FOR THE PROCESSES
    #-------------------------------------------
    q_x = dict_queues['x']
    q_y = dict_queues['y']
    # Specify that the input stream for THIS process
    # is q_x
    Stream.scheduler.input_queue = q_x
    
    #-------------------------------------------
    # 2. SPECIFY STREAMS IN THIS PROCESS
    #-------------------------------------------
    x = Stream(name='x')
    
    #-------------------------------------------
    # 3. SPECIFY CALLBACK FUNCTIONS IN THIS PROCESS
    #-------------------------------------------
    def callback_x(stream_item):
        """
        Send stream_item to the stream called 'y' in
        process_y
        """
        receiver_stream_name = 'y'
        print('message received by process x: ', stream_item)
        message = (receiver_stream_name, [stream_item+1])
        json_message = json.dumps(message)
        # Send message to process_y by putting it process_y's
        # input queue
        q_y.put(json_message)
    
    #-------------------------------------------
    # 4. SPECIFY AGENTS IN THIS PROCESS
    #-------------------------------------------
        
    single_item(in_stream=x, func=callback_x)
    
    #-------------------------------------------
    # 5. START SCHEDULER AND THUS START THIS PROCESS
    #-------------------------------------------
    Stream.scheduler.start()

    return
