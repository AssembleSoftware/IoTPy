"""
This module defines a class, VM, for making a virtual machine which:
(0) Communicates with other (possibly remote) VMs by publishing and
    subscribing streams using APMQ. This APMQ implementation uses
    RabbitMQ/pika.
(1) Has a MulticoreApp (a child class) which consists of multiple
    processes and threads for data sources and actuators. See
    multicore.py for the MulticoreApp class. 

          Threads for data sources and actuators
           within a single process within a VM
Each process may have its own data sources and actuators. Each source
and each actuator runs in its own thread. Each process has a single
agent (see compute_func) that consumes data from sources and generates
data for actuators.

          Communicating between processes in the same VM
A process communicates with another process in the same VM using the
shared memory space. Connections between processes are made by
specifying connections between output streams of processes in the VM
to input streams of processes in the same VM.
"""

## import sys
## import os
#sys.path.append(os.path.abspath("../multiprocessing"))
## sys.path.append(os.path.abspath("../core"))
## sys.path.append(os.path.abspath("../agent_types"))
## sys.path.append(os.path.abspath("../helper_functions"))
## sys.path.append(os.path.abspath("../../examples/timing"))
from multicore import Multiprocess
import time

class VM(Multiprocess):
    """
    Class for creating and executing a virtual machine that
    communicates with other virtual machines using message passing.
    Messages are communicated using the AMQP protocol implemented by
    RabbitMQ.

    A VM contains a Multiprocess which connects processes within the
    VM by using the shared memory space of the VM.

    Parameters
    ----------
    processes: list
       list of DistributedProcess.
    connections: list
       list of 4-tuples connecting streams in the same Multiprocess
       object where each tuple is:
       (0) sending DistributedProcess,
       (1) name of out_stream of the sending DistributedProcess
       (2) receiving DistributedProcess
       (3) name of in_stream of the receiving DistributedProcess
       The sending and receiving DistributedProcess must be in the same
       Multiprocess object
    publishers: list
       list of 3-tuples where each tuple is:
       (0) sending DistributedProcess,
       (1) name of out_stream of the sending DistributedProcess
       (2) the publication bound to this out_stream.
    subscribers: list
       list of 3 tuples where each tuple is:
       (0) receiving DistributedProcess
       (1) name of in_stream of the receiving DistributedProcess
       (2) name of subscription bound to this in_stream.
    name: str, optional
       The name of the VM. The default is
       'unnamed_VM'.
    """
    def __init__(self, processes, connections=[],
                 publishers=[], subscribers=[], 
                 name='unnamed_VM'):
        self.processes = processes
        self.connections = connections
        self.publishers = publishers
        self.subscribers = subscribers
        super(VM, self).__init__(
            processes, connections, name)
        self.setup_publications()
        self.setup_subscriptions()

    def setup_publications(self):
        """
        Attach output streams of processes to their publications.

        """
        for publisher in self.publishers:
            sending_process, out_stream_name, publication = publisher
            sending_process.attach_out_stream_name_to_publication(
                out_stream_name, publication)
        return

    def setup_subscriptions(self):
        """
        Attach input streams of processes to their subscriptions. 
        """
        for subscriber in self.subscribers:
            receiving_process, in_stream_name, subscription = \
              subscriber
            receiving_process.attach_in_stream_name_to_subscription(
                in_stream_name, subscription)
        return

    def start(self):
        for process in self.processes:
            process.start()

    def join(self):
        for process in self.processes:
            process.join()
    
    def run(self):
        self.start()
        time.sleep(2)
        self.join()
