import multiprocessing as mp

import example_multiprocessing_merge_leaf
import example_multiprocessing_merge_root

if __name__ == '__main__':
    #----------------------------------------------------------- 
    # 1. CREATE DICT OF INPUT QUEUES OF PROCESSES FED BY EXTERNAL
    # STREAMS.
    #----------------------------------------------------------- 
    q_root = mp.Queue()
    dict_queues = {'q_root': q_root}
    
    #----------------------------------------------------------- 
    # 2. CREATE PROCESSES
    #----------------------------------------------------------- 
    num_messages = 4

    # PROCESS_X
    stream_name_x, random_start_x, random_end_x = 'x', 0, 10
    process_x = mp.Process(
        target=example_multiprocessing_merge_leaf.process_target_leaf,
        args=(num_messages, dict_queues, stream_name_x, random_start_x, random_end_x,),
        name='process_x')

    # PROCESS_Y
    stream_name_y, random_start_y, random_end_y = 'y', 100, 110
    process_y = mp.Process(
        target=\
        example_multiprocessing_merge_leaf.process_target_leaf,
        args=(num_messages, dict_queues, stream_name_y, random_start_y, random_end_y,), 
        name='process_y')

    # PROCESS_MERGE
    process_merge = mp.Process(
        target=\
        example_multiprocessing_merge_root.process_target_merge,
        args=(dict_queues,),
        name='process_merge')
    
    #----------------------------------------------------------- 
    # 3. START, JOIN, TERMINATE PROCESSES
    #----------------------------------------------------------- 
    process_x.daemon = True
    process_y.daemon = True
    process_merge.daemon = True

    process_x.start()
    process_y.start()
    process_merge.start()

    process_x.join()
    process_y.join()
    process_merge.join()
    
    process_x.terminate()
    process_y.terminate()
    process_merge.terminate()
