import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
from source import source_func_to_stream
from multicore import single_process_single_source
from sink import sink_element

import time
import ntplib
import logging
# If an ntp service is unavailable then this logged in the log file
# 'ntp_service_operation.txt'
logging.basicConfig(
    filename='ntp_service_operation.txt', level=logging.DEBUG)  
ntp_client = ntplib.NTPClient()


def clock_drift_from_ntp_server(ntp_server):
    """
    Returns the system clock drift computed from the specified
    ntp_server 

    Parameters
    ----------
    ntp_server: str
        The name of an ntp server.

    Returns
    -------
    response.offset: float
       system clock drift

    filenames
    ---------
    'ntp_service_operation.txt': logging error file

    """
    try:
        # response.offset is the system clock offset from ntp time.
        response = ntp_client.request(ntp_server, version=3)
        return response.offset
    except:
        logging.warning('No response from NTP server: %s',ntp_server)
        return None


def clock_drift_from_first_ntp_server(list_of_ntp_servers):
    """
    Returns the system clock drift computed from the first functioning
    ntp_server in list_of_ntp_servers. 

    Parameters
    ----------
    list_of_ntp_servers: list
        List of names of ntp servers which are called in order.

    Returns
    -------
    response.offset: float
       system clock drift

    filenames
    ---------
    'ntp_service_operation.txt': logging error file

    """
    for ntp_server in list_of_ntp_servers:
        drift = clock_drift_from_ntp_server(ntp_server)
        if drift:
            return drift
    # None of the ntp servers in the list returned values.
    return 0.0

def time_and_offset(list_of_ntp_servers):
    """
    Returns the absolute time and offset from ntp computed from the
    first functioning ntp_server in list_of_ntp_servers. 

    Parameters
    ----------
    list_of_ntp_servers: list
        List of names of ntp servers which are called in order.

    Returns: 2-tuple consisting of absolute time, offset
    -------    
    time: float
       absolute time at which ntp server was called
    offset: float
       difference between ntp server time and local system clock
       time. 

    filenames
    ---------
    'ntp_service_operation.txt': logging error file

    """
    #print 'In time_and_offset(list_of_ntp_servers)'
    for ntp_server in list_of_ntp_servers:
        offset = clock_drift_from_ntp_server(ntp_server)
        if offset:
            #print 'offset is ', offset
            return time.time(), offset
    # None of the ntp servers in the list returned values.
    return time.time(), 0.0


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
def h(in_stream):
    def print_output(v): print v
    sink_element(func=print_output, in_stream=in_stream)


def test_0():
    def g(out_stream):
        return source_func_to_stream(
            func=clock_drift_from_ntp_server,
            out_stream=out_stream,
            time_interval=0.1, num_steps=3,
            ntp_server=ntp_server
            )
    single_process_single_source(source_func=g, compute_func=h)

def test_1():
    def g(out_stream):
        return source_func_to_stream(
            func=clock_drift_from_first_ntp_server,
            out_stream=out_stream,
            time_interval=0.1, num_steps=3,
            list_of_ntp_servers=list_of_ntp_servers
            )
    single_process_single_source(source_func=g, compute_func=h)


def test_2():
    def g(out_stream):
        return source_func_to_stream(
            func=time_and_offset,
            out_stream=out_stream,
            time_interval=0.1, num_steps=3,
            list_of_ntp_servers=list_of_ntp_servers
            )
    single_process_single_source(source_func=g, compute_func=h)

if __name__ == '__main__':
    print 'starting test_0'
    test_0()
    print
    print 'starting test_1'
    test_1()
    print
    print 'starting test_2'
    test_2()
    print
