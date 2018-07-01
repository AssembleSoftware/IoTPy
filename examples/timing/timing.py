import sys
"""
This module consists of functions that use ntp and other sources of
timing signals to produce streams of either (1) timestamps or (2) time
offsets from  system clocks.

The key point of this module is that you create the streams you want
by first writing simple terminating functions that call ntp (or other
services) and which return an offset or other time. Then you encapsulate
these functions using source_to_stream or other procedures from the
IoTPy library to generate threads. Finally you start the threads to
generate streams of offsets or timing values, and join the threads
before terminating.

This module has four parts:
(0) Classes for storing parameters such as the estimated offset or the
estimated mu and sigma for a Wiener process.
(1) Terminating functions that call one or more ntp services and
obtain time offsets between the time read by the local system clock
and the ntp services. The different functions use multiple ntp
services in different ways, e.g., use the max or the median value.
(2) Encapsulations of these terminating functions to create functions that
return threads.
(3) Tests that start the threads. Execution of these threads causes a
sequence of timing offsets to populate timing streams.

Note: In some cases, the average or median of a window of offsets is
more robust than a single offset. Use functions from
IoTPy/examples/windows to compute statistics on the offset streams.

Note: This module also has an example of generating a stream of
timestamps obtained by getting system-clock offsets from an ntp
service and then adding the offset to the clock. In some cases, a
moving-window average of system-clock offsets is more robust than a
single offset; examples of moving-window averages are given elsewhere.

"""
import os
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))

# stream is in core
from stream import Stream
# recent_values is in helper_functions
from recent_values import recent_values
# op and source are in agent_types
from op import map_element, map_window
from source import source_function, source_to_stream

from threading import Lock
# math is used for calculating statistics such as median
import math
import time
# ntplib is used for ntp services
import ntplib
import logging
# If an ntp service is unavailable then this logged in the log file
# 'ntp_service_operation.txt'
logging.basicConfig(
    filename='ntp_service_operation.txt', level=logging.DEBUG)  
ntp_client = ntplib.NTPClient()


#-----------------------------------------------------
#   PART 0: CLASSES WITH PARAMETERS DEALING WITH TIME
#----------------------------------------------------

class TimeCorrector(object):
    """
    Stores the most recent offset which is used to compute the
    corrected time.

    """
    def __init__(self):
        self.lock_offset = Lock()
        self.offset = 0.0
    def set_offset(self, offset):
        with self.lock_offset:
            self.offset = offset
    def get_time(self):
        with self.lock_offset:
            return time.time() + self.offset

# This is the only instance of the class TimeCorrector
time_corrector = TimeCorrector()

class WienerProcessTime(object):
    """
    Models the situation in which the deviation of the system
    clock from the true time is a Wiener process.
    Stores the parameters mu and simga for a Wiener process.
    mu is used in correcting the local clock time.
    sigma is used in estimating when the accuracy of the corrected
    time exceeds a threshold.

    Attributes
    ----------
    lock: Lock
       Lock that is acquired to access other attributes
    mu: float
       mu is the drift rate for a Wiener process
    sigma: float
       sigma is the infinitesimal standard deviation of the Wiener
       process.
    local_anchor_time: time
       The corrected time is a function of the local_anchor_time
       and the current time.
       This time is the last time, measured on the local system clock,
       at which an ntp reading was taken.
    anchor_offset: ntp offset
       anchor_offset is the offset obtained from an ntp service when
       the local clock reads local_anchor_time.
    corrected_anchor_time: time
       The corrected time (i.e. ntp time) when the local clock reads
       local_anchor_time. 

    """
    def __init__(self):
        self.lock = Lock()
        self.mu = 0.0
        self.sigma = 0.0
        self.local_anchor_time = time.time()
        self.anchor_offset = 0.0
        self.corrected_anchor_time = \
          (self.local_anchor_time + self.anchor_offset) 
    def set_mu(self, mu):
        with self.lock:
            self.mu = mu
    def set_sigma(self, sigma):
        with self.lock:
            self.sigma = sigma
    def set_anchor_times(self, local_anchor_time, anchor_offset):
        with self.lock:
            self.local_anchor_time = local_anchor_time
            self.anchor_offset = anchor_offset
            self.corrected_anchor_time = \
              (self.local_anchor_time + self.anchor_offset)
    def get_corrected_time(self):
        """
        Get the corrected time based on the drift mu of the Wiener
        process. 

        """
        with self.lock:
            self.local_current_time = time.time()
            local_delta_from_anchor = \
              self.local_current_time - self.local_anchor_time
            corrected_delta_from_anchor = \
              (self.local_current_time - self.local_anchor_time)/self.mu
            corrected_current_time = \
              (self.corrected_anchor_time +
               corrected_delta_from_anchor)  
            return corrected_current_time

# This is the only instance of the class WienerProcessTime in this
# file. 
wiener_process_time = WienerProcessTime()

def set_wiener_process_parameters_and_get_time(
        list_of_local_time_and_offset, wiener_process_time):
    """
    Parameters
    ----------
       list_of_local_time_and_offset: list of 2-tuples
          2-tuples are (local_time, offset)
          An ntp service is called when the local system clock reads
          local_time and the offset returned by the call is offset.
       wiener_process_time: WienerProcessTime
          An object that stores mu and sigma and parameters of the
          Wiener process.

    """
    R = range(len(list_of_local_time_and_offset))
    # local_t is the list of the local times
    local_t = [v[0] for v in list_of_local_time_and_offset]
    # offset is the corresponding list of offsets from ntp
    offset = [v[1] for v in list_of_local_time_and_offset]
    # corrected_t is the list of the true (ntp-based) time
    corrected_t = [local_t[i]+offset[i] for i in R]
    # start_t_local is the local time at the start of the list.
    start_t_local = local_t[0]
    # start_t_corrected is the corrected time when the local clock
    # reads local_t.
    start_t_corrected = corrected_t[0]
    # delta_t_local is a list of the difference of the local time in
    # the list from the local time at the start of the list
    delta_t_local = \
      [v - start_t_local for v in local_t]
    # delta_t_corrected is a list of the difference of the corrected
    # time in the list from the corrected time at the start of the
    # list.
    delta_t_corrected = \
      [v - start_t_corrected for v in corrected_t]
    # compute mu: the drift parameter in a Wiener process
    # This is a linear regression where the line starts at the origin
    # where the origin is (delta_t_local=0, delta_t_corrected=0).
    # mu, the slope of the line y = mx is:
    # sum of y[i]*x[i]/ sum of x[i]*x[i]
    numerator = 0.0
    denominator = 0.0
    for i in R:
        numerator += delta_t_local[i]*delta_t_corrected[i]
        denominator += delta_t_corrected[i]*delta_t_corrected[i]
    mu = numerator/float(denominator)
    # sigma is the standard deviation parameter of a Wiener process.
    # Compute sigma
    error = [delta_t_corrected[i] - mu * delta_t_local[i]
             for i in R]
    variance = 0.0
    for i in range(len(delta_t_corrected)-1):
        variance += ((error[i+1] - error[i])*(error[i+1] - error[i]) /
                     (delta_t_corrected[i+1] - delta_t_corrected[i]))
    sigma = math.sqrt(variance)
    # Update the wiener_process parameters
    wiener_process_time.set_mu(mu)
    wiener_process_time.set_sigma(sigma)
    wiener_process_time.set_anchor_times(
        local_anchor_time=local_t[-1],
        anchor_offset=offset[-1])
    print 'mu is ', mu
    print 'sigma is ', sigma
    return wiener_process_time.get_corrected_time()

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
            print 'drift is ', drift
            return drift
    # None of the npt servers in the list returned values.
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
    for ntp_server in list_of_ntp_servers:
        offset = clock_drift_from_ntp_server(ntp_server)
        if offset:
            return time.time(), offset
    # None of the ntp servers in the list returned values.
    return time.time(), 0.0


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
        midpoint = len(list_of_drifts)/2
        if len(list_of_drifts) == 0:
            return 0.0
        if len(list_of_drifts) == 1:
            return list_of_drifts[0]
        if len(list_of_drifts) % 2:
            # list_of_drifts has an odd number of elements
            # So, return the midpoint
            return list_of_drifts[midpoint]
        else:
            # list_of_drifts has an even number of elements
            # So, return the average of the middle two elements.
            return (list_of_drifts[midpoint-1] + list_of_drifts[midpoint])/2.0
            

def ntp_time_estimate(offset):
    """
    Parameters
    ----------
       offset: float
          offset between system clock and ntp clock.
          This value should be obtained by calling an ntp service.
    Returns
    -------
       float
          The number of seconds since the epoch

    """
    return time.time() + offset


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

def thread_offset_from_single_ntp_server(ntp_server, out_stream):
    return source_to_stream(
        func=clock_drift_from_ntp_server,
        out_stream=out_stream,
        time_interval=0.1, num_steps=8,
        window_size=1, name='ntp_agent_single',
        #declare kwargs: ntp_server 
        ntp_server=ntp_server
        )

def thread_offset_from_first_ntp_server(
        list_of_ntp_servers, out_stream): 
    return source_to_stream(
        func=clock_drift_from_first_ntp_server,
        out_stream=out_stream,
        time_interval=0.1, num_steps=8,
        name='ntp_agent_first_ntp_server', window_size=1,
        list_of_ntp_servers=list_of_ntp_servers
        )

def thread_offset_from_average_of_ntp_servers(
        list_of_ntp_servers, out_stream):
    return source_to_stream(
        func=clock_drift_from_average_of_ntp_servers,
        out_stream=out_stream,
        time_interval=0.1, num_steps=8,
        name='ntp_agent_average_of_ntp_servers', window_size=1,
        list_of_ntp_servers=list_of_ntp_servers
        )

def thread_offset_from_median_of_ntp_servers(
        list_of_ntp_servers, out_stream):
    return source_to_stream(
        func=clock_drift_from_median_of_ntp_servers,
        out_stream=out_stream,
        time_interval=0.1, num_steps=8,
        name='ntp_agent_median', window_size=1,
        list_of_ntp_servers=list_of_ntp_servers
        )

def thread_time_and_offset(
        list_of_ntp_servers, out_stream):
    return source_to_stream(
        func=time_and_offset,
        out_stream=out_stream,
        time_interval=0.1, num_steps=8,
        name='time_and_offset_agent', window_size=1,
        list_of_ntp_servers=list_of_ntp_servers
        )

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#                        PART 3: TESTS
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

#          TESTING FUNCTIONS ENCAPSULATED IN THREADS

# N is the number of times that groups of NTP services are called.
N = 8
def test_clock_drift_from_ntp_server():
    """
    Tests clock drift by printing N drifts

    """
    ntp_server = '0.us.pool.ntp.org'
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

def test_time_and_offset():
    list_of_ntp_servers =  [
        "0.us.pool.ntp.org",
        "1.us.pool.ntp.org",
        "2.us.pool.ntp.org",
        "3.us.pool.ntp.org"
        ]
    N = 8
    for _ in range(N):
        absolute_time, offset = time_and_offset(
            list_of_ntp_servers) 
        print 'absolute time is ', absolute_time, 'offset is ', offset
        time.sleep(0.1)
    


#-----------------------------------------------------------------------------
#            TESTING AGENTS
#-----------------------------------------------------------------------------
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
    # Stream of offsets between local time and single NTP server.
    offset_stream_single_server = Stream()
    # Stream of offsets between local time and first NTP server in a
    # list of NTP servers.
    offset_stream_first_server = Stream()
    # Stream of offsets between local time and the average of a list
    # of NTP servers. NTP servers that are not responding are
    # ignored. 
    offset_stream_from_average_of_ntp_servers = Stream()
    # Stream of offsets between local time and the median of a list
    # of NTP servers. NTP servers that are not responding are
    # ignored. 
    offset_stream_from_median_of_ntp_servers = Stream()
    # Stream of tuples (absolute local time, offset)
    time_and_offset_stream = Stream('Time and offset')

    ## # STEP 4: DECLARE MAP FROM STREAM NAMES TO STREAMS
    ## # Specify mapping from names (strings) given
    ## # to streams in source_function and names used within
    ## # the executing process. You can use any name within
    ## # the executing processes; these names don't have to be
    ## # the same as the names used in source_function.
    ## # For example: the stream with name
    ## # 'offset_stream_from_single_ntp_server' in
    ## # def thread_offset_from_single_ntp_server() source_function
    ## # is mapped to the stream offset_stream_single_server in
    ## # the executing process, and
    ## # the stream with name
    ## # 'offset_stream_from_first_ntp_server' in
    ## # def thread_offset_from_first_ntp_server() source_function
    ## # is mapped to the stream offset_stream_first_server in
    ## # the executing process. 
    ## scheduler.name_to_stream = {
    ##     'offset_stream_from_single_ntp_server':
    ##     offset_stream_single_server,
    ##     'offset_stream_from_first_ntp_server':
    ##     offset_stream_first_server,
    ##     'offset_stream_from_average_of_ntp_servers':
    ##     offset_stream_from_average_of_ntp_servers,
    ##     'offset_stream_from_median_of_ntp_servers':
    ##     offset_stream_from_median_of_ntp_servers,
    ##     'time_and_offset_stream':
    ##     time_and_offset_stream
    ##     }

    # STEP 5: GET A THREAD AND A READY SIGNALING OBJECT FOR
    # EACH source_function.
    # The ready signal indicates that the thread is ready to run.
    #
    # ntp_thread_single is the name of the thread, and
    # ntp_thread_single_ready is the ready signal object.
    ntp_thread_single, ntp_thread_single_ready = \
      thread_offset_from_single_ntp_server(
          ntp_server, out_stream=offset_stream_single_server)
    ntp_thread_first, ntp_thread_first_ready = \
      thread_offset_from_first_ntp_server(
          list_of_ntp_servers, out_stream=offset_stream_first_server)
    ntp_thread_average, ntp_thread_average_ready = \
      thread_offset_from_average_of_ntp_servers(
          list_of_ntp_servers,
          out_stream=offset_stream_from_average_of_ntp_servers)
    ntp_thread_median, ntp_thread_median_ready = \
      thread_offset_from_median_of_ntp_servers(
          list_of_ntp_servers,
          out_stream=offset_stream_from_median_of_ntp_servers)
    time_and_offset_thread, thread_time_and_offset_ready = \
      thread_time_and_offset(
          list_of_ntp_servers,
          out_stream=time_and_offset_stream)

    # STEP 6: START EACH THREAD.
    ntp_thread_single.start()
    ntp_thread_first.start()
    ntp_thread_average.start()
    ntp_thread_median.start()
    time_and_offset_thread.start()

    # STEP 7: WAIT FOR EACH THREAD TO BE READY.
    # This step can be skipped if threads run for ever.
    # This step is helpful if threads run until they generate a fixed
    # number of values.
    ntp_thread_single_ready.wait()
    ntp_thread_first_ready.wait()
    ntp_thread_average_ready.wait()
    ntp_thread_median_ready.wait()
    thread_time_and_offset_ready.wait()

    # STEP 8: BUILD A NETWORK OF AGENTS THAT OPERATE ON SOURCE STREAMS
    # This example creates a stream of timestamps. This agent reads
    # time offsets from the stream offset_stream_first_server and it
    # outputs a stream, time_stream, of absolute times. Thus the
    # output stream is an absolute timestamp for each offset in the
    # input stream.
    time_stream = Stream('Time Stream')
    map_element(func=ntp_time_estimate,
                in_stream=offset_stream_first_server,
                out_stream=time_stream)

    # ----------------------------------------------------------------
    # This example creates an average of the offset over a sliding
    # window. The average offset is more stable than a single
    # offset value.
    #
    # average_offset_stream is a sliding window of the average of the
    # offsets for each input in the window.
    average_offset_stream = Stream('Average Offset Stream')
    def average_of_list(a_list):
        return sum(a_list)/float(len(a_list))
    map_window(func=average_of_list,
               in_stream=offset_stream_first_server,
               out_stream=average_offset_stream,
               window_size=3, step_size=1)
    # ----------------------------------------------------------------
    #
    # test class TimeCorrector
    # time_corrector is an instance of TimeCorrector.
    def test_time_object(offset, time_corrector):
        time_corrector.set_offset(offset)
        return time_corrector.get_time()
    corrected_time_stream = Stream('Corrected time stream')
    map_element(func= test_time_object,
                in_stream=average_offset_stream,
                out_stream=corrected_time_stream,
                time_corrector=time_corrector)
    # ----------------------------------------------------------------
    #
    # test class WienerProcessTime
    corrected_wiener_times = Stream('Corrected Wiener Times')
    map_window(
        func=set_wiener_process_parameters_and_get_time,
        in_stream=time_and_offset_stream,
        out_stream=corrected_wiener_times,
        window_size=3, step_size=2,
        wiener_process_time = wiener_process_time
        )

    # STEP 9:JOIN EACH THREAD.
    scheduler.start()
    # This step should be skipped if threads run for ever.
    # This step is helpful if threads run until they generate a fixed
    # number of values.
    ntp_thread_single.join()
    ntp_thread_first.join()
    ntp_thread_average.join()
    ntp_thread_median.join()
    time_and_offset_thread.join()

    # STEP 10: START THE SCHEDULER.
    #scheduler.start()

    # STEP 11: JOIN THE SCHEDULER THREAD
    # This step should be skipped if execution should never stop.
    scheduler.join()

    # STEP 12: FOR TESTING, PRINT VALUES IN STREAMS.
    print 'offset: NTP- local clock. Single NTP server.'
    print recent_values(offset_stream_single_server)
    print
    print 'offset from first NTP server to respond.'
    print recent_values(offset_stream_first_server)
    print
    print 'offset from the average of a list of NTP servers.'
    print recent_values(offset_stream_from_average_of_ntp_servers)
    print
    print 'offset from the median of a list of NTP servers.'
    print recent_values(offset_stream_from_median_of_ntp_servers)
    print
    print 'stream of absolute times.'
    print recent_values(time_stream)
    print
    print 'average of offset over sliding window'
    print recent_values(average_offset_stream)
    print
    print 'corrected time using offset from sliding window'
    print recent_values(corrected_time_stream)
    print
    print 'corrected Wiener times'
    print recent_values(corrected_wiener_times)
    print 'Test is successful'

if __name__ == '__main__':
    ## print 'TESTING CLOCK DRIFT FROM SINGLE NTP SERVER'
    ## test_clock_drift_from_ntp_server()
    ## print
    ## print 'TESTING CLOCK DRIFT FROM FIRST NTP SERVER'
    ## test_clock_drift_from_first_ntp_server()
    ## print
    ## print 'TESTING CLOCK DRIFT FROM AVERAGE OF NTP SERVERS'
    ## test_clock_drift_from_average_of_ntp_servers()
    ## print
    ## print 'TESTING CLOCK DRIFT FROM MEDIAN OF NTP SERVERS'
    ## test_clock_drift_from_median_of_ntp_servers()
    ## print
    ## print 'TESTING NTP OFFSET STREAM'
    ## test_time_and_offset()
    print
    print 'The scheduler waits for the input queue to become empty.'
    print 'This may take some time.'
    print 'Expect to see "input queue empty" a few times.'
    print
    test_thread_clock_offset()
    
