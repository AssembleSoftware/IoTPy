import multiprocessing as mp

# import files containing target functions of 
# processes x, y.
# The target functions are in separate files because of
# features of iPython and Jupyter notebooks.
import example_multiprocessing_simple_process_x
import example_multiprocessing_simple_process_y

if __name__ == '__main__':

    # Put the input queues into a dict that is passed to processes x, y.
    # Don't pass queues directly to external files.
    q_x, q_y = mp.Queue(), mp.Queue()
    dict_queues = {'x': q_x, 'y': q_y}

    # Create processes x and y
    process_x = mp.Process(
        target=\
        example_multiprocessing_simple_process_x.process_target_x,
        args=(dict_queues,),
        name='process_x')

    process_y = mp.Process(
        target=\
        example_multiprocessing_simple_process_y.process_target_y,
        args=(dict_queues,),
        name='process_y')

    # Start; join; terminate processes x and y
    process_x.daemon = True
    process_y.daemon = True

    process_x.start()
    process_y.start()

    process_x.join()
    process_y.join()
    
    process_x.terminate()
    process_y.terminate()



    
