import multiprocessing as mp

import example_multiprocessing_simple_process_x_pickle
import example_multiprocessing_simple_process_y_pickle

if __name__ == '__main__':

    # dict_queues passed to processes x and y
    q_x, q_y = mp.Queue(), mp.Queue()
    dict_queues = {'x': q_x, 'y': q_y}

    # Create processes x and y
    process_x = mp.Process(
        target=\
        example_multiprocessing_simple_process_x_pickle.process_target_x,
        args=(dict_queues,))

    process_y = mp.Process(
        target=\
        example_multiprocessing_simple_process_y_pickle.process_target_y,
        args=(dict_queues,))

    # Start; join; terminate processes x and y
    process_x.daemon = True
    process_y.daemon = True

    process_x.start()
    process_y.start()

    process_x.join()
    process_y.join()
    
    process_x.terminate()
    process_y.terminate()



    
