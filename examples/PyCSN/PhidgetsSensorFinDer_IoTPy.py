"""
This is an example for applying IoTPy to PyCSN still in development
"""

import sys
import os
import time

sys.path.append(os.path.abspath("../../IoTPy/concurrency"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))

# multicore is in multiprocessing
from multicore import multicore, copy_data_to_source
# stream is in core
from stream import Stream, StreamArray
# op, merge, source, sink are in agent_types
from op import map_element, map_window, filter_element
from merge import zip_stream, merge_window
from split import unzip
from sink import stream_to_file
from helper_control import _no_value

# constants related to reading data from file
PICKER_INTERVAL = 0.02

# 3 directions for sensors
N_DIR = 3

# our special order CSN Phidgets are scaled to +/- 2g instead of +/- 6g
PHIDGETS_ACCELERATION_TO_G = 1.0/3.0
PHIDGETS_DECIMATION = 1
PICKER_THRESHOLD = 0.0025

# we request samples at 250 per second
PHIDGETS_NOMINAL_DATA_INTERVAL_MS = 4

# constants for picker
MINIMUM_REPICK_INTERVAL_SECONDS = 1.0
delta = PHIDGETS_NOMINAL_DATA_INTERVAL_MS * PHIDGETS_DECIMATION * 0.001
LTA = 10.0
LTA_COUNT = int(LTA / delta)
LTA_COUNT = int(LTA_COUNT / 100)
print('LTA_COUNT: ', LTA_COUNT)


# Read from input and output sensor readings
def f(in_streams, out_streams):
    # in_stream[0] ~ in_stream[2] - re-ordered sensor data, in_stream[3] - time stamp,
    n_acc = len(in_streams) - 1

    # assume 3 in_streams of raw data - reordered
    scaled_acc = [Stream('scaled_acc_' + str(i)) for i in range(n_acc)]
    inverted_acc = Stream('inverted_acc')
    averaged_acc = [Stream('averaged_acc_' + str(i)) for i in range(n_acc)]
    # time stamp that corresponds to the averaged acc
    acc_timestamp = Stream('acc_timestamp')
    # acc merged with timestamp data
    acc_merged = Stream('acc_merged')
    # acc data picked according to timestamp
    acc_picked = Stream('acc_picked')

    def scale_g(v):
        return PHIDGETS_ACCELERATION_TO_G * v

    for i in range(n_acc):
        map_element(
            func=scale_g,
            in_stream=in_streams[i],
            out_stream=scaled_acc[i]
        )

    # need a mechanism to check missing samples
    # if self.last_phidgets_timestamp:
    #     sample_increment = int(
    #         round((phidgets_timestamp - self.last_phidgets_timestamp) / PHIDGETS_NOMINAL_DATA_INTERVAL))
    #     if sample_increment > 4 * self.decimation:
    #         logging.warn('Missing >3 samples: last sample %s current sample %s missing samples %s', \
    #                      self.last_phidgets_timestamp, phidgets_timestamp, sample_increment)
    #     elif sample_increment == 0:
    #         logging.warn('Excess samples: last sample %s current sample %s equiv samples %s', \
    #                      self.last_phidgets_timestamp, phidgets_timestamp, sample_increment)

    def invert_channel(v):
        return -1 * v

    # invert channel 1 (E-W) - this results in +1g being reported when the sensor is resting on its E side
    map_element(
        func=invert_channel,
        in_stream=scaled_acc[1],
        out_stream=inverted_acc
    )

    def average_samples(window):
        return sum(window) / float(len(window))

    for i in range(n_acc):
        if i == 1:
            map_window(
                func=average_samples,
                in_stream=inverted_acc,
                out_stream=averaged_acc[i],
                window_size=PHIDGETS_DECIMATION,
                step_size=PHIDGETS_DECIMATION
            )
        else:
            map_window(
                func=average_samples,
                in_stream=scaled_acc[i],
                out_stream=averaged_acc[i],
                window_size=PHIDGETS_DECIMATION,
                step_size=PHIDGETS_DECIMATION
            )

    def get_timestamp(window):
        return window[-1]

    map_window(
        func=get_timestamp,
        in_stream=in_streams[3],
        out_stream=acc_timestamp,
        window_size=PHIDGETS_DECIMATION,
        step_size=PHIDGETS_DECIMATION
    )

    # zip
    zip_stream(
        in_streams=averaged_acc + [acc_timestamp],
        out_stream=acc_merged
    )

    # filter for timestamp delta below PICKER_INTERVAL
    def timestamp_picker(v, state):
        if v[3] - state > PICKER_INTERVAL: # spit output - False
            return False, v[3]
        else:
            return True, state

    filter_element(
        func=timestamp_picker,
        in_stream=acc_merged,
        out_stream=acc_picked,
        state=0
    )

    unzip(
        in_stream=acc_picked,
        out_streams=out_streams
    )

    # write to datastore - maybe use another process?
    # if self.datastore_file:
    #     if self.first_sample_timestamp_in_file == None:
    #         self.first_sample_timestamp_in_file = sample_timestamp
    #     try:
    #         self.datastore_file.write("%20.5f" % sample_timestamp + ' ' +
    #                                   ' '.join("%10.7f" % x for x in accelerations) + '\n')
    #         self.writing_errors = 0
    #     except Exception, e:
    #         self.writing_errors += 1
    #         if self.writing_errors <= 10:
    #             logging.error('Error %s writing sample to file %s with timestamp %s', e, self.datastore_filename,
    #                           sample_timestamp)

    # create datastore

    # if sample_timestamp - self.first_sample_timestamp_in_file >= self.file_store_interval:
    #     logging.info('File %s store interval elapsed with %s samples, rate %s samples/second', self.datastore_filename,
    #                  len(self.data_buffer), float(len(self.data_buffer)) / self.file_store_interval)
    #     # we will change to a new file in the datastore
    #     if self.datastore_file:
    #         self.datastore_file.close()
    #     # logging.info('File closed')
    #     self.last_datastore_filename = self.datastore_filename
    #     self.data_buffer = []
    #     self.time_start = None


# Picker
def g(in_streams, out_streams):
    """
    Parameters
    ----------
    in_streams: list of Streams
        single stream of (acc0, acc1, acc2, timestamp)
    out_streams

    Returns
    -------

    """

    # define Streams
    adjusted_acc = [Stream('adjusted_acc_{}'.format(i)) for i in range(len(in_streams) - 1)]
    adjusted_timestamp = Stream('adjusted_timestamp')
    merged_acc = Stream('acc_merged')
    filtered_acc = Stream('filtered_acc')
    quenched_acc = Stream('quenched_acc')

    # subtract long term average for all accelerations
    # def adjust_lta(window_arr):
    #     timestamp = list(map(lambda x: x[-1], window_arr))[-1]
    #     adjusted_window = [abs(window[-1] - sum(window)/len(window)) for window in zip(*map(lambda x: x[:-1], window_arr))]
    #     return adjusted_window + [timestamp]

    def adjust_lta(window):
        return abs(window[-1] - sum(window)/len(window))

    for i in range(len(in_streams) - 1):
        map_window(
            func=adjust_lta,
            in_stream=in_streams[i],
            out_stream=adjusted_acc[i],
            window_size=LTA_COUNT,
            step_size=1
        )

    def adjust_timestamp(window):
        return window[-1]

    map_window(
        func=adjust_timestamp,
        in_stream=in_streams[-1],
        out_stream=adjusted_timestamp,
        window_size=LTA_COUNT,
        step_size=1
    )

    # zip acc streams and timestamp stream
    zip_stream(
        in_streams=adjusted_acc + [adjusted_timestamp],
        out_stream=merged_acc
    )

    # filter out small magnitude i.e. under picker threshold
    def detect_anomaly(v):
        return any(map(lambda x: x > PICKER_THRESHOLD, v[:-1]))

    filter_element(
        func=detect_anomaly,
        in_stream=merged_acc,
        out_stream=filtered_acc
    )

    # check if minimum_repick interval has passed
    def check_repick_interval(v, state):
        timestamp = v[3]
        if timestamp - state < MINIMUM_REPICK_INTERVAL_SECONDS:
            return _no_value, state
        else:
            print(timestamp)
            state = timestamp
            return v, state

    map_element(
        func=check_repick_interval,
        in_stream=filtered_acc,
        out_stream=quenched_acc,
        state=0
    )

    # need to separate timestamp from stream
    stream_to_file(quenched_acc, './phidget_data.txt')


def read_timestamp_from_file(source):
    filename = 'timestamp.txt'
    with open(filename, 'r') as fpin:
        data = list(map(float, fpin))
        for i in range(len(data)):
            copy_data_to_source([data[i]], source)
            time.sleep(0.001)
    return


if __name__ == '__main__':
    # 'e' for east, 'n' for north, 'z' for vertical
    direction_list = ['n', 'e', 'z']
    direction_source_dict = {}

    # define function to read data from input file
    for direction in direction_list:
        def read_file_thread_target(source, file_suffix=direction):
            filename = 'acc_{}.txt'.format(file_suffix)
            with open(filename, 'r') as fpin:
                data = list(map(float, fpin))
                for i in range(len(data)):
                    copy_data_to_source([data[i]], source)
                    time.sleep(0.001)
            return
        direction_source_dict[direction] = read_file_thread_target

    processes = dict()
    processes['sensor_reading'] = {
        'in_stream_names_types': [('in_{}'.format(direction), 'f') for direction in direction_list],
        'out_stream_names_types': [('out_{}'.format(direction), 'f') for direction in direction_list],
        'compute_func': f,
        'sources':
            {
                'source_' + direction:
                    {
                        'type': 'f',
                        'func': direction_source_dict[direction]
                    }
                for direction in direction_list
            },
        'actuators': {}
    }
    processes['sensor_reading']['in_stream_names_types'].append(('in_timestamp', 'f'))
    processes['sensor_reading']['out_stream_names_types'].append(('out_timestamp', 'f'))
    processes['sensor_reading']['sources']['source_timestamp'] = {
        'type': 'f',
        'func': read_timestamp_from_file
    }

    # define the aggregation process
    processes['picker'] = \
        {
            'in_stream_names_types': [('in_{}'.format(direction), 'f') for direction in direction_list],
            'out_stream_names_types': [],
            'compute_func': g,
            'sources': {},
            'actuators': {}
        }
    processes['picker']['in_stream_names_types'].append(('in_timestamp', 'f'))

    # make connections between processes
    connections = dict()
    connections['sensor_reading'] = {}
    for direction in direction_list:
        connections['sensor_reading']['source_{}'.format(direction)] = [('sensor_reading', 'in_{}'.format(direction))]
        connections['sensor_reading']['out_{}'.format(direction)] = [('picker', 'in_{}'.format(direction))]
    connections['sensor_reading']['source_timestamp'] = [('sensor_reading', 'in_timestamp')]
    connections['sensor_reading']['out_timestamp'] = [('picker', 'in_timestamp')]

    connections['picker'] = {}

    print(processes)
    print(connections)

    multicore(processes, connections)

