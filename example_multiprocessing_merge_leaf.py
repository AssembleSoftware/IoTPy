import json
import multiprocessing as mp
from stream import Stream, ExternalStream
from example_operators import join_synch, single_item
import random

def process_target_leaf(num_messages, dict_queues, stream_name,
                            random_start, random_end):
    stream_to_root = ExternalStream(name=stream_name, queue=dict_queues['q_root'])

    for i in range(num_messages):
        stream_item = random.randrange(random_start, random_end)
        print (stream_name, stream_item)
        stream_to_root.append(stream_item)
