import sys
sys.path.append("../")
from IoTPy.helper_functions.print_stream import print_stream
from IoTPy.concurrency.multicore import get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import extend_stream
from IoTPy.concurrency.MQTT_Subscriber import start_callback_thread


def mqtt_subscriber_test():
    """
    This function shows how to use MQTT to receive a
    stream that was sent using MQTT_Publisher.

    The mqtt_receive_agent prints its single input stream.
    The function start_callback_thread starts a thread
    which receives JSON input (see 'body in callback) from
    MQTT and puts the data into a stream called
    'mqtt_receive_stream'.

    Note that start_callback_thread is a function that
    starts a thread; it is not a thread or a thread target.

    For efficiency, the publisher publishes segments of a
    stream as opposed to sending each single element separately.

    """
    # Step 0: Define agent functions, source threads 
    # and actuator threads (if any).

    # Step 0.0: Define agent functions.
    # This is merely a dummy agent that does nothing other than print.
    def mqtt_receive_agent(in_streams, out_streams):
        print_stream(in_streams[0], 'mqtt_receive_stream')

    # Step 0.1: Define source thread targets (if any).
    # qtt_callback_thread imported from MQTT_Subscriber
    # This thread is started when processes are started.

    # Step 1: multicore_specification of streams and processes.
    # Specify Streams: list of pairs (stream_name, stream_type).
    # Specify Processes: name, agent function, 
    #       lists of inputs and outputs, additional arguments.
    # The mqtt_receive_stream data type is 'x' for arbitrary.
    # If the data type is int use 'i', and use 'f' for float.
    multicore_specification = [
        # Streams
        [('mqtt_receive_stream', 'x')],
        # Processes
        [{'name': 'mqtt_receive_process', 'agent': mqtt_receive_agent,
          'inputs':['mqtt_receive_stream'], 'sources': ['mqtt_receive_stream']}]]

    # Step 2: Create processes.
    processes, procs = get_processes_and_procs(multicore_specification)

    # We skip these steps because we will call start_callback_thread
    # to start a thread.
    # Step 3: Create threads (if any)
    # The function start_callback_thread will start the callback thread.
    # Step 4: Specify which process each thread runs in.
    # mqtt_callback_thread runs in this (the calling) process.

    # Step 5: Start, join and terminate processes.
    # Start the mqtt_callback loop thread. The parameters are:
    # (0) procs, (1) stream name, (2) the pub/sub topic,
    # (3) the host.
    start_callback_thread(
        procs, 'mqtt_receive_stream', 'topic', 'localhost')
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

if __name__ == '__main__':
    mqtt_subscriber_test()
