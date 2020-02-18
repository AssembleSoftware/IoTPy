import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/concurrency"))
from source import source_func_to_stream
from multicore import run_single_process_single_source
from multicore import copy_data_to_source, source_finished
from sink import sink_element
from print_stream import print_stream

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

# This is the network of agents that operates on the data
# acquired from the source. This network consists of a single
# sink agent. Create the sink agent by using the encapsulator
# sink_element to encapsulate terminating function
# print_output.
def h(in_streams, out_streams):
    def print_output(v): print (v)
    sink_element(func=print_output, in_stream=in_streams[0])


def test_0():
    #------------------------------------------------
    # Test of ntp running in its own thread using
    # run_single_process_single_source() instead of
    # explicitly writing processes and connections.
    #------------------------------------------------
    ntp_obj = ntp_single_server("0.us.pool.ntp.org")
    def source_thread_target(source):
        num_steps=3
        for i in range(num_steps):
            v = ntp_obj.offset()
            copy_data_to_source([v], source)
            time.sleep(0.01)
        source_finished(source)
    def compute_func(in_streams, out_streams):
        print_stream(in_streams[0])
    run_single_process_single_source(source_thread_target, compute_func)


def test_1():
    servers = ntp_multiple_servers(list_of_ntp_servers)
    def source_thread_target(source):
        num_steps=3
        for i in range(num_steps):
            v = servers.first_offset()
            copy_data_to_source([v], source)
            time.sleep(0.01)
        source_finished(source)
    def compute_func(in_streams, out_streams):
        print_stream(in_streams[0])
    run_single_process_single_source(source_thread_target, compute_func)

def test_2():
    servers = ntp_multiple_servers(list_of_ntp_servers)
    def source_thread_target(source):
        num_steps=1
        for i in range(num_steps):
            v = servers.mean_offset()
            copy_data_to_source([v], source)
            time.sleep(0.01)
        source_finished(source)
    def compute_func(in_streams, out_streams):
        print_stream(in_streams[0])
    run_single_process_single_source(source_thread_target, compute_func)

if __name__ == '__main__':
    print ('starting test_0')
    test_0()
    print
    print ('starting test_1')
    test_1()
    print
    print ('starting test_2')
    test_2()
    print
