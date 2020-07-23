"""
This module has targets for threads in a multithreaded application.

"""
import queue
import threading
from ..core.stream import run

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
        self.terminated_streams = {}
        for in_stream in in_streams:
            self.terminated_streams[in_stream.name] = False

    def extend(self, in_stream_name, list_of_elements):
        assert type(list_of_elements) == list
        assert in_stream_name in self.name_to_stream.keys()
        self.q.put((in_stream_name,list_of_elements))

    def append(self, in_stream_name, element):
        self.extend(in_stream_name, list_of_elements=[element])

    def terminate(self, in_stream_name):
        self.terminated_streams[in_stream_name] = True
        if all(self.terminated_streams.values()):
            self.finished()

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
        
    
        
        
        
