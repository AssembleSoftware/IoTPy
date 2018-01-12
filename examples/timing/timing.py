import sys
"""
This module consists of functions that use ntp and other sources of
timing signals to produce streams of timestamps or time offsets from
system clocs.

The key point of this module is that you create the streams you want
by first writing simple terminating functions and then you encapsulate
these functions using source_function or other mechanisms from the
IoTPy library.

This module has three parts: (1) terminating (non-streaming)
terminating functions; (2) encapsulating these terminating functions
to create functions that generate threads; (3) tests that start the
threads which then populate the timing streams.

"""
import os
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))
from source import source_function
from stream import Stream
from recent_values import recent_values

import time
import ntplib
import logging
logging.basicConfig(
    filename='ntp_service_operation.txt', level=logging.DEBUG)  
ntp_client = ntplib.NTPClient()

#-----------------------------------------------------------------------------
#   PART 1: FUNCTIONS ENCAPSULATED IN STREAMS
#-----------------------------------------------------------------------------

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
        response = ntp_client.request(ntp_server, version=3)
        return response.offset
    except:
        logging.warning('No response from NTP server: %s',ntp_server)
        return None


def clock_drift_from_first_ntp_server(list_of_ntp_servers):
    """
    Returns the system clock drift computed from the first functioning
    ntp_server. 

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
        return clock_drift_from_ntp_server(ntp_server)

def clock_drift_from_average_of_ntp_servers(list_of_ntp_servers):
    """
    Returns the system clock drift computed from the average obtained
    from the list of ntp servers. 

    Parameters
    ----------
    list_of_ntp_servers: list
        List of names of ntp servers which are called in order.

    Returns
    -------
    system clock drift

    filenames
    ---------
    'ntp_service_operation.txt': logging error file

    """
    list_of_drifts_including_None = [
        clock_drift_from_ntp_server(ntp_server) for
        ntp_server in list_of_ntp_servers]
    list_of_drifts = [v for v in list_of_drifts_including_None
                      if v is not None]
    if list_of_drifts:
        return sum(list_of_drifts)/float(len(list_of_drifts))


def clock_drift_from_median_of_ntp_servers(list_of_ntp_servers):
    """
    Returns the system clock drift computed from the median obtained
    from the list of ntp servers. 

    Parameters
    ----------
    list_of_ntp_servers: list
        List of names of ntp servers which are called in order.

    Returns
    -------
    system clock drift

    filenames
    ---------
    'ntp_service_operation.txt': logging error file

    """
    list_of_drifts_including_None = [
        clock_drift_from_ntp_server(ntp_server) for
        ntp_server in list_of_ntp_servers]
    list_of_drifts = [v for v in list_of_drifts_including_None
                      if v is not None]
    if list_of_drifts:
        list_of_drifts = sorted(list_of_drifts)
        return list_of_drifts[len(list_of_drifts)/2]


#-----------------------------------------------------------------------------
#   PART 2: FUNCTIONS THAT RETURN SOURCE THREADS
#-----------------------------------------------------------------------------
# These functions encapsulate terminating Python functions to create
# threads and ready signaling objects. These functions call
# source_function from agent_types/source. Next we describe some of
# the parameters of source_function()

# The threads run for ever if num_steps is None. If num_steps is a
# positive number then the threads terminate after num_steps values
# are placed on the output stream.

# The stream name in source_function is important.
# This stream name is mapped to a stream inside the executing process.
# The mapping is specified in scheduler.name_to_stream when the
# processes are run.

def thread_offset_from_single_ntp_server(ntp_server):
    return source_function(
        func=clock_drift_from_ntp_server,
        stream_name='offset_stream_from_single_ntp_server',
        time_interval=0.1, num_steps=3,
        name='ntp_agent_single', window_size=1,
        ntp_server=ntp_server
        )


def thread_offset_from_first_ntp_server(list_of_ntp_servers):
    return source_function(
        func=clock_drift_from_first_ntp_server,
        stream_name='offset_stream_from_first_ntp_server',
        time_interval=0.1, num_steps=3,
        name='ntp_agent_first', window_size=1,
        list_of_ntp_servers=list_of_ntp_servers
        )


def thread_offset_from_average_of_ntp_servers(list_of_ntp_servers):
    return source_function(
        func=clock_drift_from_average_of_ntp_servers,
        stream_name='offset_stream_from_average_of_ntp_servers',
        time_interval=0.1, num_steps=3,
        name='ntp_agent_average', window_size=1,
        list_of_ntp_servers=list_of_ntp_servers
        )

def thread_offset_from_median_of_ntp_servers(list_of_ntp_servers):
    return source_function(
        func=clock_drift_from_median_of_ntp_servers,
        stream_name='offset_stream_from_median_of_ntp_servers',
        time_interval=0.1, num_steps=3,
        name='ntp_agent_median', window_size=1,
        list_of_ntp_servers=list_of_ntp_servers
        )

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#                        PART 3: TESTS
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

#          TESTING FUNCTIONS TO BE ENCAPSULATED BY AGENTS

def test_clock_drift_from_ntp_server():
    """
    Tests clock drift by printing N drifts

    """
    ntp_server = '0.us.pool.ntp.org'
    N = 2
    for _ in range(N):
        drift = clock_drift_from_ntp_server(ntp_server)
        print 'drift = ', drift
        time.sleep(0.1)

def test_clock_drift_from_first_ntp_server():
    
    """
    Tests clock drift by printing N drifts

    """
    list_of_ntp_servers =  [
        "0.us.pool.ntp.org",
        "1.us.pool.ntp.org",
        "2.us.pool.ntp.org",
        "3.us.pool.ntp.org"
        ]
    N = 2
    for _ in range(N):
        drift = clock_drift_from_first_ntp_server(list_of_ntp_servers)
        print 'drift = ', drift
        time.sleep(0.1)


def test_clock_drift_from_average_of_ntp_servers():
    
    """
    Tests clock drift by printing N drifts computed by taking
    the average from a list of ntp servers

    """
    list_of_ntp_servers =  [
        "0.us.pool.ntp.org",
        "1.us.pool.ntp.org",
        "2.us.pool.ntp.org",
        "3.us.pool.ntp.org"
        ]
    N = 2
    for _ in range(N):
        drift = clock_drift_from_average_of_ntp_servers(
            list_of_ntp_servers) 
        print 'drift = ', drift
        time.sleep(0.1)



def test_clock_drift_from_median_of_ntp_servers():
    
    """
    Tests clock drift by printing N drifts computed by taking
    the median from a list of ntp servers

    """
    list_of_ntp_servers =  [
        "0.us.pool.ntp.org",
        "1.us.pool.ntp.org",
        "2.us.pool.ntp.org",
        "3.us.pool.ntp.org"
        ]
    N = 2
    for _ in range(N):
        drift = clock_drift_from_median_of_ntp_servers(
            list_of_ntp_servers) 
        print 'drift = ', drift
        time.sleep(0.1)

        
#            TESTING AGENTS

def test_thread_clock_offset():

    # STEP 1: SPECIFY CONSTANT PARAMETERS AND SHARED DATA.
    ntp_server = '0.us.pool.ntp.org'
    list_of_ntp_servers =  [
        "0.us.pool.ntp.org",
        "1.us.pool.ntp.org",
        "2.us.pool.ntp.org",
        "3.us.pool.ntp.org"
        ]

    # STEP 2: DEFINE THE scheduler
    scheduler = Stream.scheduler

    # STEP 3: DECLARE STREAMS
    offset_stream_single_server = Stream()
    offset_stream_first_server = Stream()
    offset_stream_from_average_of_ntp_servers = Stream()
    offset_stream_from_median_of_ntp_servers = Stream()

    # STEP 4: SPECIFY MAPPING FROM NAMES (STRINGS) GIVEN
    # TO STREAMS IN source_function AND NAMES USED WITHIN
    # THE EXECUTING PROCESS. YOU CAN USE ANY NAME WITHIN
    # THE EXECUTING PROCESSES; THESE NAMES DON'T HAVE TO BE
    # THE SAME AS THE NAMES USED IN source_function.
    # FOR EXAMPLE: THE STREAM WITH NAME
    # 'offset_stream_from_single_ntp_server' in source_function
    # IS MAPPED TO THE STREAM offset_stream_single_server IN
    # THE EXECUTING PROCESS.
    scheduler.name_to_stream = {
        'offset_stream_from_single_ntp_server':
        offset_stream_single_server,
        'offset_stream_from_first_ntp_server':
        offset_stream_first_server,
        'offset_stream_from_average_of_ntp_servers':
        offset_stream_from_average_of_ntp_servers,
        'offset_stream_from_median_of_ntp_servers':
        offset_stream_from_median_of_ntp_servers
        }

    # STEP 5: GET A THREAD AND A READY SIGNALING OBJECT FOR
    # EACH source_function
    ntp_thread_single, ntp_thread_single_ready = \
      thread_offset_from_single_ntp_server(ntp_server)
    ntp_thread_first, ntp_thread_first_ready = \
      thread_offset_from_first_ntp_server(list_of_ntp_servers)
    ntp_thread_average, ntp_thread_average_ready = \
      thread_offset_from_average_of_ntp_servers(list_of_ntp_servers)
    ntp_thread_median, ntp_thread_median_ready = \
      thread_offset_from_median_of_ntp_servers(list_of_ntp_servers)

    # STEP 6: START EACH THREAD.
    ntp_thread_single.start()
    ntp_thread_first.start()
    ntp_thread_average.start()
    ntp_thread_median.start()

    # STEP 7: WAIT FOR EACH THREAD TO BE READY.
    # This step can be skipped if threads run for ever.
    # This step is helpful if threads run until they generate a fixed
    # number of values.
    ntp_thread_single_ready.wait()
    ntp_thread_first_ready.wait()
    ntp_thread_average_ready.wait()
    ntp_thread_median_ready.wait()

    # STEP 8:JOIN EACH THREAD.
    # This step should be skipped if threads run for ever.
    # This step is helpful if threads run until they generate a fixed
    # number of values.
    ntp_thread_single.join()
    ntp_thread_first.join()
    ntp_thread_average.join()
    ntp_thread_median.join()

    # STEP 9: START THE SCHEDULER.
    scheduler.start()

    # STEP 10: JOIN THE SCHEDULER THREAD
    # This step should be skipped if execution should never stop.
    scheduler.join()

    # STEP 11: FOR TESTING, PRINT VALUES IN STREAMS.
    print recent_values(offset_stream_single_server)
    print recent_values(offset_stream_first_server)
    print recent_values(offset_stream_from_average_of_ntp_servers)
    print recent_values(offset_stream_from_median_of_ntp_servers)

if __name__ == '__main__':
    print 'TESTING CLOCK DRIFT FROM SINGLE NTP SERVER'
    test_clock_drift_from_ntp_server()
    print
    print 'TESTING CLOCK DRIFT FROM FIRST NTP SERVER'
    test_clock_drift_from_first_ntp_server()
    print
    print 'TESTING CLOCK DRIFT FROM AVERAGE OF NTP SERVERS'
    test_clock_drift_from_average_of_ntp_servers()
    print
    print 'TESTING CLOCK DRIFT FROM MEDIAN OF NTP SERVERS'
    test_clock_drift_from_median_of_ntp_servers()
    print
    print 'TESTING NTP OFFSET STREAM'
    print 'Next output will be N values of the stream'
    print 'ntp timer from single server followed by'
    print 'ntp timer from first server'
    print
    print 'The scheduler waits for the input queue to become empty.'
    print 'Expect to see "input queue empty" a few times.'
    print
    test_thread_clock_offset()
    
