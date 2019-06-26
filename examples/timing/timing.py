import sys
"""
This module consists of functions that use ntp to produce streams of
timestamps or time offsets from local clocks.

The key point of this module is that you develop these applications in
the following steps:
(1) Write terminating functions that call ntp and that return a time
offset from the local computer clock. 
(2) Wrap these functions using the source_func_to_stream wrapper to get an
source agent that generates a stream of offsets or corrected times.
(3) Make processes using these sources by using the wrapper
                    single_process_single_source
which makes a process consisting of:
(a) the single source agent executing in its own thread and
(b) a computational network of agents executing in its own thread. In
our tests, this computational network has a sink agent that prints a
stream. 

This module has four parts:
(1) Classes for computing parameters such as the estimated time offset
or the estimated mean and standard deviation for a Wiener process
model of the offset. Helper functions such as print_stream.
(2) Agents that generate streams of offsets or absolute times. These
agents are created in two steps:
  (a) Create terminating functions that call one or more ntp services
  and obtain time offsets between the time read by the local system
  clock and the ntp services. The different functions use multiple ntp
  services in different ways, e.g., use the max or the median value.
  (b) Wrap these terminating functions using the source_func_to_stream
  wrapper to create agents that execute in their own threads.
(3) Make processes using the wrapper single_process_single_source;
test the processes.
(4) Tests of the processes.

"""
import os
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# stream is in core
from stream import Stream
# print_stream is in helper_functions
from print_stream import print_stream
# op, sink and source are in agent_types
from op import map_element, map_window
from sink import sink_element
from source import source_func_to_stream
# multicore is in multiprocessing
from multicore import run_single_process_single_source

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


#------------------------------------------------------------------
#------------------------------------------------------------------
#   PART 1: CLASSES DEALING WITH TIME, AND HELPER FUNCTIONS
#------------------------------------------------------------------
#------------------------------------------------------------------

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
    
class TimeCorrector(object):
    """
    Provides a more accurate time than the local system clock by using
    ntp services.

    Attributes
    ----------
    lock: Lock
       Lock that is acquired to access offset
    offset: float
       offset of the ntp time from the local clock.

    Methods
    -------
    set_offset() stores the most recent offset.
    get_time() gets the corrected time. 

    Note
    ----
    Uses a lock because a thread could be getting the
    time while another thread is setting offset.

    """
    def __init__(self):
        self.lock_offset = Lock()
        self.offset = 0.0
    def set_offset(self, offset):
        with self.lock_offset:
            self.offset = offset
    def get_time(self):
        with self.lock_offset:
            if self.offset:
                return time.time() + self.offset

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

    Returns
    -------
       time
          The correct time using the Wiener process model

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
    print 'Wiener Process average rate, mu is ', mu
    print 'Wiener Process standard deviation rate, sigma is ', sigma
    return wiener_process_time.get_corrected_time()


#------------------------------------------------------------------
#------------------------------------------------------------------
#   PART 2: AGENTS THAT GENERATE STREAMS OF CLOCK OFFSETS AND TIMES
#------------------------------------------------------------------
#------------------------------------------------------------------

#------------------------------------------------------------
# CLOCK OFFSETS FROM A SPECIFIED NTP SERVER
#------------------------------------------------------------
def clock_offset_from_ntp_server(ntp_server):
    """
    Returns the system clock offset computed from the specified
    ntp_server 

    Parameters
    ----------
    ntp_server: str
        The name of an ntp server.

    Returns
    -------
    response.offset: float
       system clock offset

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

def offsets_from_ntp_server(
        out_stream, ntp_server, time_interval, num_steps):
    """
    Returns a source agent that produces a stream of time offsets from
    the local clock.

    Parameters
    ----------
    out_stream: Stream
       The output stream containing the source data.
    ntp_server: ntp server
       The ntp server that is called to get the offsets.
    time_interval: int or float
       time in seconds between successive calls to the ntp service.
    num_steps: int (optional)
       The number of steps after which the stream stops. Set this to a
        positive integer during debugging. If it is unspecified, or is
        0, then the stream never stops.
    
    """
    return source_func_to_stream(
        func=clock_offset_from_ntp_server,
        out_stream=out_stream,
        time_interval=time_interval,
        num_steps=num_steps,
        ntp_server=ntp_server)


#--------------------------------------------------------------
# CLOCK OFFSETS FROM THE FIRST FUNCTIONING NTP SERVER IN A LIST
#--------------------------------------------------------------
def clock_offset_from_first_ntp_server(list_of_ntp_servers):
    """
    Returns the system clock offset computed from the first functioning
    ntp_server in list_of_ntp_servers. 

    Parameters
    ----------
    list_of_ntp_servers: list
        List of names of ntp servers which are called in order until
        the first functioning ntp server is obtained.

    Returns
    -------
    response.offset: float
       system clock offset

    filenames
    ---------
    'ntp_service_operation.txt': logging error file

    """
    for ntp_server in list_of_ntp_servers:
        offset = clock_offset_from_ntp_server(ntp_server)
        if offset:
            return offset
    # None of the npt servers in the list returned values.
    return 0.0

def offsets_from_first_ntp_server(
        out_stream, list_of_ntp_servers, time_interval, num_steps):
    """
    Returns a source agent that produces a stream of time offsets from
    the first functioning ntp server in a list of ntp servers.

    Parameters
    ----------
    out_stream: Stream
       The output stream containing the source data.
    list_of_ntp_servers: list
       A list of ntp servers. The first functioning ntp server in the
       list is called to get the time offset from the local clock. 
    time_interval: int or float
       time in seconds between successive calls to the ntp services.
    num_steps: int (optional)
       The number of steps after which the stream stops. Set this to a
        positive integer during debugging. If it is unspecified, or is
        0, then the stream never stops.

    """
    return source_func_to_stream(
        func=clock_offset_from_first_ntp_server,
        out_stream=out_stream,
        time_interval=time_interval, num_steps=num_steps,
        list_of_ntp_servers=list_of_ntp_servers
        )


#-----------------------------------------------------------------
# TIME AND OFFSETS FROM THE FIRST FUNCTIONING NTP SERVER IN A LIST
#-----------------------------------------------------------------

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
        offset = clock_offset_from_ntp_server(ntp_server)
        if offset:
            return time.time(), offset
    # None of the ntp servers in the list returned values.
    return time.time(), 0.0


def times_and_offsets_from_first_ntp_server(
        out_stream, list_of_ntp_servers, time_interval, num_steps):
    """
    Returns a source agent that produces a stream of 2-tuples,
    (absolute time, time offset) from the first functioning ntp server
    in the specified list of ntp servers. 

    Parameters
    ----------
    out_stream: Stream
       The output stream containing the source data.
    list_of_ntp_servers: list
       A list of ntp servers. The first functioning ntp server in the
       list is called to get the time offset from the local clock. 
    time_interval: int or float
       time in seconds between successive calls to the ntp services.
    num_steps: int (optional)
       The number of steps after which the stream stops. Set this to a
        positive integer during debugging. If it is unspecified, or is
        0, then the stream never stops.

    """
    return source_func_to_stream(
        func=time_and_offset,
        out_stream=out_stream,
        time_interval=time_interval, num_steps=num_steps,
        list_of_ntp_servers=list_of_ntp_servers
        )


#-----------------------------------------------------------------
# OFFSETS FROM AVERAGE OF NTP SERVERS
#-----------------------------------------------------------------

def clock_offset_from_average_of_ntp_servers(list_of_ntp_servers):
    """
    Returns the system clock offset computed from the average obtained
    from the list of ntp servers. 

    Parameters
    ----------
    list_of_ntp_servers: list
        List of names of ntp servers which are called in order.

    Returns
    -------
    system clock offset

    filenames
    ---------
    'ntp_service_operation.txt': logging error file

    """
    list_of_offsets_including_None = [
        clock_offset_from_ntp_server(ntp_server) for
        ntp_server in list_of_ntp_servers]
    list_of_offsets = [v for v in list_of_offsets_including_None
                      if v is not None]
    if list_of_offsets:
        return sum(list_of_offsets)/float(len(list_of_offsets))


def offsets_from_average_of_ntp_servers(
        out_stream, list_of_ntp_servers, time_interval, num_steps):
    """
    Returns a source agent that produces a stream of time offsets
    which is the average of the offsets returned by each ntp server in
    the specified list. 

    Parameters
    ----------
    out_stream: Stream
       The output stream containing the averages of the offsets from
        the ntp servers.
    list_of_ntp_servers: list
       A list of ntp servers. All the functioning ntp servers in the
       list are called to get the time offset from the local clock,
        and the average of their values is placed on the stream.
    time_interval: int or float
       time in seconds between successive calls to the ntp services.
    num_steps: int (optional)
       The number of steps after which the stream stops. Set this to a
        positive integer during debugging. If it is unspecified, or is
        0, then the stream never stops.

    """
    return source_func_to_stream(
        func=clock_offset_from_average_of_ntp_servers,
        out_stream=out_stream,
        time_interval=time_interval, num_steps=num_steps,
        list_of_ntp_servers=list_of_ntp_servers
        )


#-----------------------------------------------------------------
# OFFSETS FROM MEDIAN OF NTP SERVERS
#-----------------------------------------------------------------

def clock_offset_from_median_of_ntp_servers(list_of_ntp_servers):
    """
    Returns the system clock offset computed from the median obtained
    from the list of ntp servers. 

    Parameters
    ----------
    list_of_ntp_servers: list
        List of names of ntp servers which are called in order.

    Returns
    -------
    system clock offset

    filenames
    ---------
    'ntp_service_operation.txt': logging error file

    """
    list_of_offsets_including_None = [
        clock_offset_from_ntp_server(ntp_server) for
        ntp_server in list_of_ntp_servers]
    list_of_offsets = [v for v in list_of_offsets_including_None
                      if v is not None]
    if list_of_offsets:
        list_of_offsets = sorted(list_of_offsets)
        midpoint = len(list_of_offsets)/2
        if len(list_of_offsets) == 0:
            return 0.0
        if len(list_of_offsets) == 1:
            return list_of_offsets[0]
        if len(list_of_offsets) % 2:
            # list_of_offsets has an odd number of elements
            # So, return the midpoint
            return list_of_offsets[midpoint]
        else:
            # list_of_offsets has an even number of elements
            # So, return the average of the middle two elements.
            return (list_of_offsets[midpoint-1] + list_of_offsets[midpoint])/2.0
            
def offsets_from_median_of_ntp_servers(
        out_stream, list_of_ntp_servers, time_interval, num_steps):
    """
    Returns a source agent that produces a stream of time offsets
    which is the median of the offsets returned by each ntp server in
    the specified list. 

    Parameters
    ----------
    out_stream: Stream
       The output stream containing the median of the offsets from
        the ntp servers.
    list_of_ntp_servers: list
       A list of ntp servers. All the functioning ntp servers in the
       list are called to get the time offset from the local clock,
        and the average of their values is placed on the stream.
    time_interval: int or float
       time in seconds between successive calls to the ntp services.
    num_steps: int (optional)
       The number of steps after which the stream stops. Set this to a
        positive integer during debugging. If it is unspecified, or is
        0, then the stream never stops.

    """
    return source_func_to_stream(
        func=clock_offset_from_median_of_ntp_servers,
        out_stream=out_stream,
        time_interval=time_interval, num_steps=num_steps,
        list_of_ntp_servers=list_of_ntp_servers
        )

#------------------------------------------------------------------
#------------------------------------------------------------------
#     PART 3:   PROCESSES
#------------------------------------------------------------------
#------------------------------------------------------------------

# Please use your own list of ntp servers. These servers are included
# here merely for illustration.
list_of_ntp_servers =  [
    "0.us.pool.ntp.org",
    "1.us.pool.ntp.org",
    "2.us.pool.ntp.org",
    "3.us.pool.ntp.org"
    ]
ntp_server = '0.us.pool.ntp.org'
time_interval=0.1
num_steps=10

# The three steps for creating the process are:
#     (1) Define the source: source()
#     (2) Define the computational network: compute()
#     (3) Call single_process_single_source()
#
# In many of the examples, the computational network consists of a
# single sink, print_stream(), which prints a stream. 

#------------------------------------------------------------
# PROCESS CLOCK OFFSET FROM THE SPECIFIED NTP SERVER
#------------------------------------------------------------
def process_offsets_from_ntp_server(
        ntp_server, time_interval, num_steps):

    def source(out_stream):
        return offsets_from_ntp_server(
            out_stream, ntp_server, time_interval, num_steps)

    # Wrapper that creates a network of two agents: source and
    # print_stream. 
    single_process_single_source(
        source_func=source, compute_func=print_stream)

#------------------------------------------------------------
# PROCESS CLOCK OFFSET FROM THE FIRST FUNCTIONING NTP SERVER
#------------------------------------------------------------
def process_offsets_from_first_ntp_server(
        list_of_ntp_servers, time_interval, num_steps):

    def source(out_stream):
        return offsets_from_first_ntp_server(
            out_stream, list_of_ntp_servers, time_interval, num_steps)

    # Wrapper that creates a network of two agents: source and
    # print_stream. 
    single_process_single_source(
        source_func=source, compute_func=print_stream)

#------------------------------------------------------------
# PROCESS TIME AND OFFSET FROM FIRST FUNCTIONING NTP SERVER
#------------------------------------------------------------
def process_time_and_offset(
        list_of_ntp_servers, time_interval, num_steps):

    def source(out_stream):
        return times_and_offsets_from_first_ntp_server(
            out_stream, list_of_ntp_servers, time_interval, num_steps)

    # Wrapper that creates a network of two agents: source and
    # print_stream. 
    single_process_single_source(
        source_func=source, compute_func=print_stream)

#------------------------------------------------------------
# PROCESS OFFSET FROM AVERAGE OF NTP SERVERS
#------------------------------------------------------------
def process_offsets_from_average_of_ntp_servers(
        list_of_ntp_servers, time_interval, num_steps):

    def source(out_stream):
        return offsets_from_average_of_ntp_servers(
            out_stream, list_of_ntp_servers, time_interval, num_steps)

    # Wrapper that creates a network of two agents: source and
    # print_stream. 
    single_process_single_source(
        source_func=source, compute_func=print_stream)

#------------------------------------------------------------
# PROCESS OFFSETS FROM MEDIAN OF NTP SERVERS
#------------------------------------------------------------
def process_offsets_from_median_of_ntp_servers(
        list_of_ntp_servers, time_interval, num_steps):

    def source(out_stream):
        return offsets_from_median_of_ntp_servers(
            out_stream, list_of_ntp_servers, time_interval, num_steps)

    # Wrapper that creates a network of two agents: source and
    # print_stream. 
    single_process_single_source(
        source_func=source, compute_func=print_stream)

#------------------------------------------------------------
# PROCESS OFFSETS FROM NTP SERVER, AVERAGED OVER WINDOW
#------------------------------------------------------------
window_size = 3
step_size = 1
def process_offsets_average_over_window(
        ntp_server, time_interval, num_steps, window_size, step_size):
    def average_of_list(a_list):
        if a_list:
            # Remove None elements from the list
            a_list = [i for i in a_list if i is not None]
            return sum(a_list)/float(len(a_list))
        else:
            return 0.0

    def source(out_stream):
        return offsets_from_ntp_server(
            out_stream, ntp_server, time_interval, num_steps)

    def compute(in_stream):
        offset_average_stream = Stream('Offsets averaged over window')
        map_window(
            func=average_of_list, in_stream=in_stream,
            out_stream=offset_average_stream, 
            window_size=window_size, step_size=step_size)
        print_stream(offset_average_stream)

    # Wrapper that creates a network of two agents: source and
    # compute. 
    single_process_single_source(
        source_func=source, compute_func=compute)


#------------------------------------------------------------
# PROCESS CORRECTED TIMES
#------------------------------------------------------------
def process_corrected_times(ntp_server, time_interval, num_steps):
    time_corrector = TimeCorrector()

    def f(offset):
        time_corrector.set_offset(offset)
        return time_corrector.get_time()

    def source(out_stream):
        return offsets_from_ntp_server(
            out_stream, ntp_server, time_interval, num_steps)

    def compute(in_stream):
        corrected_times = Stream('Corrected times')
        map_element(func=f, in_stream=in_stream, out_stream=corrected_times)
        print_stream(in_stream=corrected_times)

    # Wrapper that creates a network of two agents: source and
    # compute. 
    single_process_single_source(
        source_func=source, compute_func=compute)

    ## # ----------------------------------------------------------------
    ## #
    ## # test class WienerProcessTime
    ## corrected_wiener_times = Stream('Corrected Wiener Times')
    ## map_window(
    ##     func=set_wiener_process_parameters_and_get_time,
    ##     in_stream=time_and_offset_stream,
    ##     out_stream=corrected_wiener_times,
    ##     window_size=3, step_size=2,
    ##     wiener_process_time = wiener_process_time
    ##     )


#------------------------------------------------------------------
#------------------------------------------------------------------
#     PART 4:   TESTS
#------------------------------------------------------------------
#------------------------------------------------------------------

if __name__ == '__main__':
    # Please use your own list of ntp servers. These servers are included
    # here merely for illustration.
    list_of_ntp_servers =  [
        "0.us.pool.ntp.org",
        "1.us.pool.ntp.org",
        "2.us.pool.ntp.org",
        "3.us.pool.ntp.org"]
    ntp_server = '0.us.pool.ntp.org'
    # Set the test parameters
    time_interval=0.1
    num_steps=3
    window_size=2
    step_size=1
    print 'The scheduler waits for the input queue to become empty.'
    print 'This may take some time.'
    print 'Expect to see "input queue empty" a few times.'
    print
    print '-----------------------------------------------------'
    print
    print 'RUNNING TESTS'
    print
    print 'PROCESS OFFSETS FROM SINGLE NTP SERVER'
    process_offsets_from_ntp_server(
        ntp_server, time_interval, num_steps)
    ## print '-----------------------------------------------------'
    ## print
    ## print 'PROCESS OFFSETS FROM FIRST NTP SERVER'
    ## process_offsets_from_first_ntp_server(
    ##     list_of_ntp_servers, time_interval, num_steps)
    ## print '-----------------------------------------------------'
    ## print
    ## print 'PROCESS TIME AND OFFSET OFFSET STREAM'
    ## print 'OUTPUT IS (time, offset)'
    ## process_time_and_offset(
    ##     list_of_ntp_servers, time_interval, num_steps)
    ## print '-----------------------------------------------------' 
    ## print
    ## print 'PROCESS OFFSETS FROM AVERAGE OF NTP SERVERS'
    ## process_offsets_from_average_of_ntp_servers(
    ##     list_of_ntp_servers, time_interval, num_steps)
    ## print '-----------------------------------------------------'
    ## print
    ## print 'PROCESS OFFSETS FROM MEDIAN OF NTP SERVERS'
    ## process_offsets_from_median_of_ntp_servers(
    ##     list_of_ntp_servers, time_interval, num_steps)
    ## print '-----------------------------------------------------'
    ## ## print
    ## print 'PROCESS OFFSETS AVERAGE OVER WINDOW'
    ## process_offsets_average_over_window(
    ##     ntp_server, time_interval, num_steps, window_size, step_size)
    ## print '-----------------------------------------------------'
    ## print
    ## print "PROCESS CORRECTED TIMES"
    ## process_corrected_times(ntp_server, time_interval, num_steps)
