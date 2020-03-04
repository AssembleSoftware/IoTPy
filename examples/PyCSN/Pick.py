"""
A version of the Phidget picker
"""

import sys
import os

sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

from stream import Stream
from merge import zip_streams
from run import run
from print_stream import print_stream
from recent_values import recent_values
from op import map_window, filter_element, map_element
from split import split_element
from basics import f_mul

def send_event(stream, orientation):
    #Replace by Julian's send_event().
    print_stream(stream, name=stream.name + '_' + orientation)

def pick_orientation(scaled, timestamps, orientation):
    """
    Sends picks on a single orientation, either 'n', 'e', or 'z'.

    """
    DECIMATION = 2
    LTA_count = 2
    PICK_THRESHOLD = 0.5

    # ---------------------------------------------------------------
    # CREATE AGENTS AND STREAMS
    # ---------------------------------------------------------------
    
    # 1. DECIMATE SCALED DATA.
    # Window of size DECIMATION is decimated to its average.
    # Input = scaled
    # Output = decimated.
    decimated = Stream('decimated')
    map_window(lambda v: sum(v)/float(len(v)), scaled, decimated,
               window_size=DECIMATION, step_size=DECIMATION)

    
    # 2. DECIMATE TIMESTAMPS.
    # Window of size DECIMATION is decimated to its last value.
    # Input = timestamps
    # Output = decimated_timestamps.
    decimated_timestamps = Stream('decimated_timestamps')
    map_window(lambda window: window[-1],
               timestamps, decimated_timestamps,
               window_size=DECIMATION, step_size=DECIMATION)

    # 3. DEMEAN (subtract mean from) DECIMATED STREAM.
    # Subtract mean of window from the window's last value.
    # Move sliding window forward by 1 step.
    # Input = decimated
    # Output = demeaned
    demeaned = Stream('demeaned', initial_value = [0.0]*(LTA_count-1))
    map_window(lambda window: window[-1] - sum(window) / float(len(window)),
               decimated, demeaned,
               window_size=LTA_count, step_size=1)

    # 4. MERGE TIMESTAMPS WITH DEMEANED ACCELERATIONS.
    # Merges decimated_timestamps and demeaned to get timestamped_data.
    # Inputs = decimated_timestamps, demeaned
    # Outputs = timestamped_data
    timestamped_data = Stream('timestamped_data')
    zip_streams(in_streams=[decimated_timestamps, demeaned], out_stream=timestamped_data)

    # 5. DETECT PICKS.
    # Output a pick if the value part of the time_value (t_v) exceeds threshold.
    # Input = timestamped_data
    # Output = picks
    picks = Stream('picks')
    filter_element(lambda t_v: abs(t_v[1]) > PICK_THRESHOLD, timestamped_data, picks)

    # 6. QUENCH PICKS.
    # An element is a (timestamp, value).
    # Start a new quench when timestamp > QUENCH_PERIOD + last_quench.
    # Update the last quench when a new quench is initiated.
    # Initially the last_quench (i.e. state) is 0.
    # Input = picks
    # Output = quenched_picks
    quenched_picks = Stream('quenched_picks')
    # f is the filtering function
    def f(timestamped_value, last_quench, QUENCH_PERIOD):
        timestamp, value = timestamped_value
        new_quench = timestamp > QUENCH_PERIOD + last_quench
        last_quench = timestamp if new_quench else last_quench
        # return filter condition (new_quench) and next state (last_quench)
        return new_quench, last_quench
    filter_element(f, picks, quenched_picks, state = 0, QUENCH_PERIOD=2)

    # 7. SEND QUENCHED PICKS.
    send_event(quenched_picks, orientation)
    # ---------------------------------------------------------------

    
def picker(nezt):
    SCALE = 1.0/3.0
    # nezt is a stream of 'data_entry' in the original code.
    # Declare acceleration streams in n, e, z orientations and timestamp stream.
    n, e, z, t = (Stream('raw_north'), Stream('raw_east'), Stream('raw_vertical'),
                  Stream('timestamps'))

    # split the nezt stream into its components
    split_element(lambda nezt: [nezt[0], nezt[1], nezt[2], nezt[3]],
          in_stream=nezt, out_streams=[n, e, z, t])

    # Determine picks for each orientation after scaling. Note negative scale for East.
    # Parameters of pick_orientation are:
    # (0) stream of accelerations in a single orientation, scaled by multiplying by SCALE.
    # (1) timestamps
    # (2) The orientation 'n', 'e', or 'z'
    pick_orientation(f_mul(n, SCALE), t, 'n')
    pick_orientation(f_mul(e, -SCALE), t, 'e')
    pick_orientation(f_mul(z, SCALE), t, 'z')

    
#---------------------------------------------------------------------
#      TESTS
#---------------------------------------------------------------------
def test_pick_orientation_with_verbose_output():
    PHIDGETS_ACCELERATION_TO_G = 1.0/3.0
    DECIMATION = 2
    LTA_count = 2
    PICK_THRESHOLD = 0.5

    # ---------------------------------------------------------------
    # Input streams
    # raw is the stream of raw acceleration data along one axis.
    # timestamps is the stream of timestamps
    scaled = Stream('scaled')
    timestamps = Stream('timestamps')

    # Decimate acceleration.
    # Window of size DECIMATION is decimated to its average.
    # Input = scaled
    # Output = decimated.
    decimated = Stream('decimated')
    map_window(lambda v: sum(v)/float(len(v)), scaled, decimated,
               window_size=DECIMATION, step_size=DECIMATION)

    # Decimate timestamps.
    # Window of size DECIMATION is decimated to its last value.
    # Input = timestamps
    # Output = decimated_timestamps.
    decimated_timestamps = Stream('decimated_timestamps')
    map_window(lambda window: window[-1],
               timestamps, decimated_timestamps,
               window_size=DECIMATION, step_size=DECIMATION)

    # Demean (subtract mean) from decimated stream.
    # Subtract mean of window from the window's last value.
    # Move sliding window forward by 1 step.
    # Input = decimated
    # Output = demeaned
    demeaned = Stream('demeaned', initial_value = [0.0]*(LTA_count-1))
    map_window(lambda window: window[-1] - sum(window) / float(len(window)),
               decimated, demeaned,
               window_size=LTA_count, step_size=1)

    # Add timestamps to demeaned accelerations.
    # Merges decimated_timestamps and demeaned to get timestamped_data.
    # Inputs = decimated_timestamps, demeaned
    # Outputs = timestamped_data
    timestamped_data = Stream('timestamped_data')
    zip_streams(in_streams=[decimated_timestamps, demeaned], out_stream=timestamped_data)

    # Detect picks.
    # Output a pick if the value part of the time_value (t_v) exceeds threshold.
    # Input = timestamped_data
    # Output = picks
    picks = Stream('picks')
    filter_element(lambda t_v: abs(t_v[1]) > PICK_THRESHOLD, timestamped_data, picks)

    # Quench picks.
    # An element is a (timestamp, value).
    # Start a new quench when timestamp > QUENCH_PERIOD + last_quench.
    # Update the last quench when a new quench is initiated.
    # Initially the last_quench (i.e. state) is 0.
    # Input = picks
    # Output = quenched_picks
    quenched_picks = Stream('quenched_picks')
    # f is the filtering function
    def f(timestamped_value, last_quench, QUENCH_PERIOD):
        timestamp, value = timestamped_value
        new_quench = timestamp > QUENCH_PERIOD + last_quench
        last_quench = timestamp if new_quench else last_quench
        # return filter condition (new_quench) and next state (last_quench)
        return new_quench, last_quench
    filter_element(f, picks, quenched_picks, state = 0, QUENCH_PERIOD=2)

    # Send quenched picks.
    send_event(quenched_picks, orientation='n')
    # ---------------------------------------------------------------

    # ---------------------------------------------------------------
    # Drive test
    print_stream(timestamps, 'timestamps')
    print_stream(scaled, 'scaled')
    print_stream(decimated, 'decimated')
    print_stream(decimated_timestamps, 'decimated_timestamps')
    print_stream(demeaned, 'demeaned')
    print_stream(timestamped_data, 'timestamped_data')
    print_stream(picks, 'picks')
    scaled.extend([1.0, 1.0, 2.0, 4.0, 4.0,
                          20.0, 8.0, 8.0, 4.0, 6.0])
    timestamps.extend(list(range(12)))
    run()

def test_pick_orientation():
    PHIDGETS_ACCELERATION_TO_G = 1.0/3.0
    DECIMATION = 2
    LTA_count = 2
    PICK_THRESHOLD = 0.5

    # ---------------------------------------------------------------
    # Input streams
    # raw is the stream of raw acceleration data along one axis.
    # timestamps is the stream of timestamps
    scaled = Stream('scaled')
    timestamps = Stream('timestamps')

    pick_orientation(scaled, timestamps, orientation='n')

    scaled.extend([1.0, 1.0, 2.0, 4.0, 4.0,
                          20.0, 8.0, 8.0, 4.0, 6.0])
    timestamps.extend(list(range(12)))
    run()

def test_picker():
    nezt = Stream('nezt')
    picker(nezt)
    nezt.extend([
        (3.0, 3.0, 3.0, 1.0),
        (3.0, 3.0, 3.0, 2.0),
        (6.0, 12.0, 6.0, 3.0),
        (12.0, 24.0, 12.0, 4.0),
        (12.0, 24.0, 12.0, 5.0),
        (60.0, 120.0, 60.0, 6.0),
        (24.0, 48.0, 24.0, 7.0),
        (24.0, 48.0, 24.0, 8.0),
        (12.0, 24.0, 12.0, 9.0),
        (18.0, 36.0, 18.0, 10.0)])
    run()


def test():
    print('')
    print ('starting test_pick_orientation_with_verbose_output')
    test_pick_orientation_with_verbose_output()
    print('')
    print ('starting test pick orientation')
    print('')
    test_pick_orientation()
    print('')
    print ('starting test picker')
    print('')
    test_picker()
    

if __name__ == '__main__':
    test()
    
