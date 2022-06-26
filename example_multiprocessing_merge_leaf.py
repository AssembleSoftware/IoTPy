from stream import ExternalStream
import random

def process_target_leaf(num_messages, dict_queues, stream_name,
                            random_start, random_end):
    """
    Send num_messages random integers in the range
    [random_start: random_end] on the external stream with
    name stream_name and queue dict_queues['q_root'].

    """
    # stream_to_root is an external stream from a leaf process
    # to the root process
    stream_to_root = ExternalStream(
        name=stream_name, queue=dict_queues['q_root'])

    for i in range(num_messages):
        stream_item = random.randrange(random_start, random_end)
        print (stream_name, stream_item)
        stream_to_root.append(stream_item)
