import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, run
from IoTPy.agent_types.sink import sink_element
from IoTPy.helper_functions.print_stream import print_stream

from IoTPy.concurrency.multicore import get_processes, get_processes_and_procs
from IoTPy.concurrency.multicore import terminate_stream
from IoTPy.concurrency.multicore import get_proc_that_inputs_source
from IoTPy.concurrency.multicore import extend_stream

import threading
import time
import ntplib
import statistics
import logging
# If an ntp service is unavailable then this logged in the log file
# 'ntp_service_operation.txt'
logging.basicConfig(
    filename='ntp_service_operation.txt', level=logging.DEBUG)  


#------------------------------------------------
# An ntp manager class
#------------------------------------------------
class ntp_single_server(object):
    def __init__(self, ntp_server):
        # ntp_server is a string such as "0.us.pool.ntp.org"
        self.ntp_server = ntp_server
        self.ntp_client = ntplib.NTPClient()
    def offset(self):
        try:
            response = self.ntp_client.request(self.ntp_server, version=3)
            return response.offset
        except:
            print ('no response from ntp client')
            return 0.0

class ntp_multiple_servers(object):
    def __init__(self, ntp_servers):
        self.ntp_servers = ntp_servers
        self.servers = []
        for ntp_server in ntp_servers:
            self.servers.append(ntp_single_server(ntp_server))
    def first_offset(self):
        for server in self.servers:
            offset = server.offset()
            if offset:
                return offset
        # None of the servers returned an offset. So return 0
        return 0.0
    def time_and_first_offset(self):
        for server in self.servers:
            offset = server.offset()
            if offset:
                return (time.time(), offset)
        # None of the servers returned an offset. So return 0
        return (time.time(), 0.0)
    def offsets(self):
        offsets = []
        for server in self.servers:
            offset = server.offset()
            if offset:
                offsets.append(offset)
        return offsets
    def mean_offset(self):
        offsets = self.offsets()
        return statistics.mean(offsets) if offsets else 0.0
    def median_offset(self):
        return statistics.median(offset) if self.offsets else 0.0
    def mode_offset(self):
        return statistics.mode(offset) if self.offsets else 0.0

#----------------------------------------------------------
#          TESTS
#----------------------------------------------------------

ntp_server = "0.us.pool.ntp.org"

list_of_ntp_servers =  [
    "0.us.pool.ntp.org",
    "1.us.pool.ntp.org",
    "2.us.pool.ntp.org",
    "3.us.pool.ntp.org"
    ]


def test_0():
    # Implement single process with thread.
    # Step 0: Define agent functions, source threads 
    # and actuator threads (if any).

    # Step 0.0: Define agent functions.
    def printer_agent(in_streams, out_streams):
        print_stream(in_streams[0])

    # Step 0.1: Define source thread targets (if any).
    ntp_obj = ntp_single_server("0.us.pool.ntp.org")

    def source_thread_target(procs):
        num_steps=3
        for i in range(num_steps):
            v = ntp_obj.offset()
            extend_stream(procs, data=[v], 
                          stream_name='ntp')
            time.sleep(0.01)
        terminate_stream(procs, stream_name='ntp')

    # Step 1: multicore_specification of streams and processes.
    # Specify Streams: list of pairs (stream_name, stream_type).
    # Specify Processes: name, agent function, 
    #       lists of inputs and outputs, additional arguments.
    multicore_specification = [
        # Streams
        [('ntp', 'f')],
        # Processes
        [{'name': 'p0', 'agent': printer_agent, 'inputs': ['ntp'],
          'args' : [], 'sources': ['ntp']}]]

    # Step 2: Create processes.
    processes, procs = get_processes_and_procs(multicore_specification)

    # Step 3: Create threads (if any)
    thread_0 = threading.Thread(target=source_thread_target, args=(procs,))

    # Step 4: Specify which process each thread runs in.
    # thread_0 runs in the process called 'coordinator'
    procs['p0'].threads = [thread_0]

    # Step 5: Start, join and terminate processes.
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()


def test_1():
    # Step 0: Define agent functions, source threads 
    # and actuator threads (if any).

    # Step 0.0: Define agent functions.
    def printer_agent(in_streams, out_streams):
        print_stream(in_streams[0])

    # Step 0.1: Define source thread targets (if any).
    servers = ntp_multiple_servers(list_of_ntp_servers)
    def source_thread_target(procs):
        num_steps=3
        for i in range(num_steps):
            v = servers.first_offset()
            extend_stream(procs, data=[v], 
                          stream_name='ntp')
            time.sleep(0.01)
        terminate_stream(procs, stream_name='ntp')

    # Step 1: multicore_specification of streams and processes.
    # Specify Streams: list of pairs (stream_name, stream_type).
    # Specify Processes: name, agent function, 
    #       lists of inputs and outputs, additional arguments.
    multicore_specification = [
        # Streams
        [('ntp', 'f')],
        # Processes
        [{'name': 'p0', 'agent': printer_agent, 'inputs': ['ntp'], 'sources': ['ntp']}]]

    # Step 2: Create processes.
    processes, procs = get_processes_and_procs(multicore_specification)

    # Step 3: Create threads (if any)
    thread_0 = threading.Thread(target=source_thread_target, args=(procs,))

    # Step 4: Specify which process each thread runs in.
    # thread_0 runs in the process called 'coordinator'
    procs['p0'].threads = [thread_0]

    # Step 5: Start, join and terminate processes.
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

        
def test_2():
    # Step 0: Define agent functions, source threads 
    # and actuator threads (if any).

    # Step 0.0: Define agent functions.
    def printer_agent(in_streams, out_streams):
        print_stream(in_streams[0])

    # Step 0.1: Define source thread targets (if any).
    def source_thread_target(source):
        servers = ntp_multiple_servers(list_of_ntp_servers)
        num_steps=3
        for i in range(num_steps):
            v = servers.time_and_first_offset()
            extend_stream(procs, data=[v], 
                          stream_name='ntp')
            time.sleep(0.01)
        terminate_stream(procs, stream_name='ntp')

    # Step 1: multicore_specification of streams and processes.
    # Specify Streams: list of pairs (stream_name, stream_type).
    # Specify Processes: name, agent function, 
    #       lists of inputs and outputs, additional arguments.
    multicore_specification = [
        # Streams
        [('ntp', 'x')],
        # Processes
        [{'name': 'p0', 'agent': printer_agent, 'inputs': ['ntp'], 'sources': ['ntp']}]]

    # Step 2: Create processes.
    processes, procs = get_processes_and_procs(multicore_specification)

    # Step 3: Create threads (if any)
    thread_0 = threading.Thread(target=source_thread_target, args=(procs,))

    # Step 4: Specify which process each thread runs in.
    # thread_0 runs in the process called 'coordinator'
    procs['p0'].threads = [thread_0]

    # Step 5: Start, join and terminate processes.
    for process in processes: process.start()
    for process in processes: process.join()
    for process in processes: process.terminate()

if __name__ == '__main__':
    print ('starting test_0')
    test_0()
    print ('')
    print ('')
    print ('---------------------------')
    print ('')
    print ('')
    print ('starting test_1')
    test_1()
    print ('')
    print ('')
    print ('---------------------------')
    print ('')
    print ('')
    print ('starting test_2')
    test_2()
    print ('')
    print ('')
    print ('---------------------------')
    print ('')
    print ('')

