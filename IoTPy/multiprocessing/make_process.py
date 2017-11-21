"""This module makes a mulitprocessing.Process by encapsulating
an agent.  A process has one input queue of type multiprocessing.Queue.
The process receives messages on its input queue. Each message that it
receives is a tuple (stream name, message content). The process
appends the message content to the stream with the specified
name. This stream must be an input stream of the agent.

The process sends messages that arrive on output streams of
the agent to input queues of other processes. Each output stream
is associated with a list of input queues of other processes.
A message on the output stream is copied to each of the queues
associated with that stream. This message is a tuple:
(stream name, message content).

A stream is closed by appending the _close object to the
stream. A process terminates execution when all its input streams
are closed.

Notes
-----
The module consists of three functions:
(1) make_input_manager, which makes an agent that we call
'input manager'
(2) make_output_manager, which makes an agent that we call
'output manager'
(3) make_process, which sets up the data structures for
input and output managers and creates the agent which creates
a network of agents that processes input streams and produces
output streams.

The input manager agent gets messages on the process's input
queue and puts them on input streams of func. The output manager
agent gets messages on output streams of func and places copies
of the messages on the input queues of other processes.

"""

from Stream import Stream, _close, _no_value
from Operators import stream_agent, stream_agent
from multiprocessing import Process, Queue
from RemoteQueue import RemoteQueue
import socket
import thread
import json
import time
from server import create_server_thread
import logging
import pika
import sys

logging.basicConfig(filename="make_process_log.log", filemode='w', level=logging.INFO)

class make_process(object):
    """
    Makes a process by encapsulating an agent which connects
    to other agents through a message queuing (APMQ) connection.

    Parameters
    ----------
    connection: RabbitMQ connection
        All messages are sent through this broker.
    agent: Agent
        The agent that is encapsulated to make this agent.

    Attributes
    ----------
    in_streams: list of Stream
        The agent's input streams.
    out_streams: list of Stream
        The agent's output streams.
    name_to_input_stream: dict
        key: name of an input stream
        value: the input stream

    """
    def __init__(self, agent, exchange_name='stream_exchange',
                 host='localhost', port=None,
                 virtual_host=None, credentials=None,
                 args=[], kwargs={}):
        self.agent = agent
        self.exchange_name = exchange_name
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.credentials = credentials
        self.name_to_input_stream = \
          dict([(stream.name, stream) for stream in agent])

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=self.host))

        # Attributes for the input channel
        self.input_channel = self.connection.channel()
        self.input_channel.exchange_declare(exchange=exchange_name, type='direct')
        self.result = self.input_channel.queue_declare(exclusive=True)
        self.queue_name = self.result.method.queue
        for in_stream in agent.in_streams:
            self.input_channel.queue_bind(
                exchange=exchange_name, queue=self.queue_name, routing_key=in_stream.name)
        self.input_manager = threading.Thread(target=self.channel.start_consuming())

        # Attributes for the output channel
        self.output_channel = self.connection.channel()
        self.output_channel.exchange_declare(exchange=exchange_name, type='direct')
        

    def callback(self, ch, method, properties, body):
        in_stream_name = method.routing_key
        in_stream = self.name_to_input_stream[in_stream_name]
        message = json.loads(body)
        in_stream.append(message)

        

    def make_output_manager(self):
        pass
    def start_process(self):
        pass
    

def make_input_manager(input_queue, input_stream_names,
                       map_name_to_input_stream, finished_execution):
    """ Makes an object that waits continuously for a
    message arriving on input_queue and then sends the message
    to the stream with the name specified on the message.

    Parameters
    ----------
    input_queue: queue
                 Either Multiprocessing.Queue or
                        StreamPy.RemoteQueue
    input_stream_names: list of str
                  The list of names of the input streams.

    map_name_to_input_stream : dict
                key : str
                      Name of an input stream.
                value : Stream
                      The stream with that name.

    Attributes
    ----------
    finished_execution : bool
                True if at least one input stream is open
                False if all input streams are closed.

    Returns
    -------
    None

    Notes
    -----
    This agent waits for a message arriving on input_queue.
    Every incoming message is a tuple: (stream_name, message_content)
    The message_content is appended to the stream with the specified
    name. If message_content is _close then the stream is closed
    by the Stream class; the program then sets finished_execution to
    True if all input streams are closed.
    If a message arrives for a closed stream then a warning message
    is attached to the log.
    The input manager continues execution until all its input streams
    are closed, and then stops.

    """

    # Initially, by default, all streams are open
    finished_execution = False
    # If the process has no input queue, i.e., if
    # the process is a source, then the process
    # has nothing to do. In this case, set
    # finished_execution to True.
    if not input_queue:
        finished_execution = True

    while not finished_execution:
        try:
            message = input_queue.get()
            message = json.loads(message)
            logging.info('make_input_manager, message = ' + str(message))
        except Exception, err:
            logging.error(err)
            return
        # This message_content is to be appended to the
        # stream with name stream_name.
        #print 'received message: ', message
        stream_name, message_content = message
        # Get the input_stream to which the message must
        # be appended.
        input_stream = map_name_to_input_stream[stream_name]

        # Message arrived for a closed stream. Error!
        if input_stream.closed:
            logging.warning('inserting values into a closed stream!')
            return

        # Append message_content to input_stream. Note message_content
        # may be '_close'; in this case convert the message content to
        # the object _close. This is because the string '_close' was
        # used as a proxy for the object _close because strings can be
        # serialized.
        if message_content == '_close':
            message_content = _close
        input_stream.append(message_content)

        # Terminate execution of the input manager when all its
        # input streams get closed.
        if message_content == _close:
            input_stream.close()
            finished_execution = \
              all([stream.closed for stream in
                   map_name_to_input_stream.values()])


def make_output_manager(output_streams, output_conn_list):
    """ Creates an agent, called the output manager, that
    receives messages on streams and inserts these messages
    into queues. The output manager receives messages on all
    streams in the list output_streams and output_streams[j]
    is associated with the list of queues, output_queues_list[j].
    Note that output_queues_list[j] is a list of queues and not a
    singleton queue. A message that arrives on the stream
    output_streams[j] is copied to each of the queues in
    output_queues_list[j]. When a message is placed in a queue
    the message is a tuple (stream_name, message_content).
    Each queue is either Multiprocessing.Queue or
    StreamPy.RemoteQueue.

    Parameters
    ----------
    output_streams : list of Stream
                  list of output streams
    output_queues_list : list of list of Queue
                  list of list of output queues.
                  output_queues_list[j] is the list of queues to which
                  messages in output_streams[j] should be sent.
                  assert len(output_streams) == len(output_queues_list)

    Returns
    -------
    None

    """
    # The sequential program that implements state-transitions of the agent.
    def send_message_to_queue(msg_content_and_stream_index_tuple):
        """ The parameter msg_content_and_stream_index_tuple
        specifies the content of a message and an index, j, which
        specifies a stream, namely output_streams[j].
        Append the message content to the each of the queues
        in the list of queues, output_queues_list[j].
        The message placed on the queue is a tuple
            (output_stream_name, message_content).

        Parameter
        ---------
        msg_content_and_index_tuple: tuple
                   (message_content, stream_index)
                   message_content: value to be inserted into queues of
                                 processes that receive the specified stream.
                   stream_index: int
                                 The slot of the sending stream in the list
                                 output_stream_names_list.

        """
        message_content, stream_index = msg_content_and_stream_index_tuple
        # receiver_queue_list is the list of queues to
        # which this message is copied.
        receiver_conn_list = output_conn_list[stream_index]
        # output_streams[stream_index] is the output stream
        # on which this message arrived.
        # output_stream_name is the name of the stream on which
        # this message arrived.
        output_stream_name = output_streams[stream_index].name

        # The messages in the queue must be serializable. The
        # object _close is not serializable; so convert it into a
        # string '_close'. The receiving agent will convert this
        # string back into the object _close.
        if message_content is _close:
            message_content = '_close'
        # The message placed in each of the receiver queues is
        # a tuple (name of the stream, content of the message).
        message = json.dumps((output_stream_name, message_content))

        for receiver_conn in receiver_conn_list:
            host, port = receiver_conn
            try:
                logging.info('make_output_manager. send_message_to_queue')
                logging.info('put message' + str(message))
                logging.info("Connecting to {0}:{1}".format(host, port))
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.connect((host, port))
                s.send(message)
                s.close()

            except socket.error as error_msg:
                logging.error(error_msg)
                continue

        return _no_value

    # Create the agent
    stream_agent(
        # The agent listens to output streams of func
        inputs=output_streams,
        # The agent does not generate its own output streams.
        outputs=[Stream('empty_stream')],
        # The agent processes messages from all its input
        # streams as the messages arrive. The agent does not
        # synchronize messages across different input streams.
        # So, f_type is 'asynch_element' rather than 'element'.
        f_type='asynch_element',
        f=send_message_to_queue)


def make_process(
        input_stream_names, output_stream_names, func,
        input_queue, output_conn_list, host, port):
    """ Makes a process that gets messages on its single
    input queue, processes the messages and puts messages
    on its output queues. An output queue of this process
    is an input queue of another process.

    Parameters
    ----------
    input_stream_names : list of str
             List of names of input streams
    output_stream_names : list of str
             List of names of output streams
    func : function
           The parameters of func are
                input_streams, output_streams where
            input_streams is a list of streams whose names
            are in input_stream_names and where
            output_streams is a list of streams whose names
            are in output_stream_names. func gets messages
            on its input streams and puts messages on its
            output streams.
    input_queue: multiprocessing.Queue
            Each process has a single input queue along
            which it receives messages.
    output_queues_list : list of list of multiprocessing.Queue
            output_queues_list[j] is the list of queues to
            which messages that appear on the stream with name
            output_stream_names[j] should be sent.

    Returns
    -------
          None
    Attributes
    ----------
    input_streams : list of Stream
           input_stream[j] is the Stream with name
           input_stream_name[j].
    output_streams : list of Stream
           output_stream[j] is the Stream with name
           output_stream_name[j].
    map_name_to_input_stream : dict
           key : str
                 name of an input stream
           value : Stream
                 The stream with the specified name.

    Notes
    -----
    make_process carries out the following steps:
    (1) Sets up data structures for the next two steps.
    (2) Calls func which creates the network of agents
    that process messages on its input streams and puts
    messages on its output streams.
    (3) Makes the output and input managers.


    """
    logging.info("Running process on {0}:{1}".format(host, port))
    finished_execution = False
    create_server_thread(host, port, input_queue, finished_execution)
    logging.info("Server created. Listening on {0}:{1}".format(host, port))
    # Create input_streams, output_streams and
    # map_name_to_input_stream
    input_streams = [Stream(name) for name in input_stream_names]
    output_streams = [Stream(name) for name in output_stream_names]
    map_name_to_input_stream = dict()
    for stream in input_streams:
        map_name_to_input_stream[stream.name] = stream
    # Call the function that creates a network of agents that
    # map input streams to output streams.
    func(input_streams, output_streams)

    make_output_manager(output_streams, output_conn_list)
    make_input_manager(input_queue, input_streams, map_name_to_input_stream, finished_execution)



def main():
    #########################################
    # 1. DEFINE ELEMENT FUNCTIONS
    # The signature for all these functions is
    # f(input_streams, output_streams) where
    # input_streams and output_streams are lists of
    # Stream.

    # Generate a stream with N random numbers and
    # then close the stream.
    N = 5
    from random import randint
    def random_ints(input_streams, output_streams):
        # Append random numbers to output_streams[0]
        # The numbers are in the interval (0, 99).
        for i in range(N):
            element_of_stream = randint(0,99)
            output_streams[0].append(element_of_stream)
            print 'In random_ints. element = ', element_of_stream
            #time.sleep(0.1)

        # Close this stream
        output_streams[0].append(_close)


    # The single output stream returns the function f
    # applied to elements of the single input stream.
    # When the input stream is closed, also close the
    # output stream.
    def f(v): return 2*v
    def apply_func_agent(input_streams, output_streams):
        input_stream = input_streams[0]
        output_stream = output_streams[0]

        def apply_func(v):
            # When the input stream is closed, return
            # _close to cause the output stream to close.
            if v == _close:
                return _close
            else:
                return f(v)

        return stream_agent(
            inputs=input_stream,
            outputs=output_stream,
            f_type='element',
            f=apply_func)

    # Print the values received on the input stream.
    def print_agent(input_streams, output_streams):
        input_stream = input_streams[0]

        def p(v):
            if v != _close:
                print 'print_agent', input_stream.name, v

        return stream_agent(
            inputs=input_stream,
            outputs=[],
            f_type='element',
            f=p)

    #########################################
    # 2. CREATE QUEUES

    #queue_0 = None
    conn_0 = ('localhost', 8891)
    queue_1 = Queue() # Input queue for process_1
    conn_1 = ('localhost', 8892)
    #queue_2 = Queue() # Input queue for process_2
    queue_2 = Queue()
    conn_2 = ('localhost', 8893)

    #########################################
    # 2. CREATE PROCESSES

    # This process is a source; it has no input queue
    # This process sends simple_stream to queue_1
    process_0 = Process(target=make_process,
                        args= (
                            [], # list of input stream names
                            ['random_ints_stream'], # list of output stream names
                            random_ints, # func
                            None, # the input queue
                            [[conn_1]], # list of list of output queues
                            conn_0[0],
                            conn_0[1]
                            ))

    # This process receives simple_stream from process_0.
    # It sends double_stream to process_2.
    # It receives messages on queue_1 and sends messages to queue_2.
    process_1 = Process(target=make_process,
                        args= (
                            ['random_ints_stream'], # list of input stream names
                            ['func_stream'], # list of output stream names
                            apply_func_agent, # func
                            queue_1, # the input queue
                            [[conn_2]], #list of list of output queues
                            conn_1[0],
                            conn_1[1]
                            ))

    # This process is a sink; it has no output queue.
    # This process receives double_stream from process_1.
    # It prints the messages it receives.
    # This process prints [0, 2, ... , 8]
    process_2 = Process(target=make_process,
                        args= (
                            ['func_stream'], # list of input stream names
                            [], # list of output stream names
                            print_agent, # func
                            queue_2, # the input queue
                            [], # list of list of output queues
                            conn_2[0],
                            conn_2[1]
                            ))

    #########################################
    # 3. START PROCESSES
    process_2.start()
    #time.sleep(0.1)
    process_1.start()
    #time.sleep(0.1)
    process_0.start()

    #########################################
    # 4. JOIN PROCESSES
    #time.sleep(0.1)
    process_2.join()
    #time.sleep(0.1)
    process_1.join()
    #time.sleep(0.1)
    process_0.join()



if __name__ == '__main__':
    main()
