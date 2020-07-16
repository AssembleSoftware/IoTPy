"""
This module has targets for threads in a multithreaded application.

"""
import queue
import threading
from ..core.stream import run
# run is in ../core/stream.py
def thread_target_appending(q_in, list_q_out, in_streams, finished='_finished'):
    """
    The target of a thread running IoTPy code. The thread waits for values to be
    put into it input queue, q_in. These elements are 2-tuples:
    (stream_name, stream_element). It finds the stream with the specified
    stream_name from a dictionary, and then appends the stream with the
    stream_element.

    If it gets a finished message from the queue then it puts finished
    messages in all its output queues.

    Parameters
    ----------
    q_in: queue.Queue()
       An element put into q_in is a pair with the form:
       (stream_name, stream_element.)
    list_q_out: list of queue.Queue()
    in_streams: list of Stream
    finished: object
       Any object to signal that the computation is over.
       A convention (though not required) is to use '_finished'.


    """
    name_to_stream = {}
    for s in in_streams:
        name_to_stream[s.name] = s

    while True:
        v = q_in.get()
        if v == finished:
            for q_out in list_q_out:
                q_out.put(finished)
            break
        stream_name, stream_element = v
        stream = name_to_stream[stream_name]
        stream.append(stream_element)
        run()

def thread_target_extending(q_in, list_q_out, in_streams, finished='_finished'):
    """
    Same as thread_target_appending except that elements put
    into q_in are pairs of the form (stream_name, stream_segment)
    where stream_segment is a list of elements of the stream.
    So, a stream is EXTENDED with the stream_segment.

    Parameters
    ----------
    q_in: queue.Queue()
       An element put into q_in is a pair with the form:
       (stream_name, stream_element.)
    list_q_out: list of queue.Queue()
    in_streams: list of Stream
    finished: object
       Any object to signal that the computation is over.
       A convention (though not required) is to use _close from
       IoTPy/IoTPy/core/helper_control.py


    """
    name_to_stream = {}
    for s in in_streams:
        name_to_stream[s.name] = s

    while True:
        v = q_in.get()
        if v == finished:
            for q_out in list_q_out:
                q_out.put(finished)
            break
        stream_name, stream_segment = v
        stream = name_to_stream[stream_name]
        stream.extend(stream_segment)
        run()
    return

class iThread(object):
    def __init__(self, in_streams, output_queues):
        self.in_streams = in_streams
        self.output_queues = output_queues
        self.q = queue.Queue()
        self.name_to_stream = {}
        for in_stream in in_streams:
            self.name_to_stream[in_stream.name] = in_stream
        self.thread = threading.Thread(
            target=self.thread_target)

    def extend(self, in_stream_name, list_of_elements):
        assert type(list_of_elements) == list
        assert in_stream_name in self.name_to_stream.keys()
        self.q.put((in_stream_name,list_of_elements))

    def append(self, in_stream_name, element):
        self.extend(in_stream_name, list_of_elements=[element])

    def finished(self):
        self.q.put('_finished')

    def thread_target(self):
        while True:
            v = self.q.get()
            if v == '_finished':
                for output_queue in self.output_queues:
                    output_queue.put('_finished')
                break
            in_stream_name, stream_segment = v
            in_stream = self.name_to_stream[in_stream_name]
            in_stream.extend(stream_segment)
            run()

    def start(self):
        self.thread.start()

    def join(self):
        self.thread.join()
        
    
        
        
        
