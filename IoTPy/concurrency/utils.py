"""
This module provides utility functions for other files in multiprocessing directory.
Written by Daniel Lee.
"""


def check_processes_connections_format(processes, connections):
    """
    This function checks the validity of the format of
    input processes and connections

    Parameters
    ----------
    processes: processes used for multicore applications
    connections: connections between processes of multicore applications

    Returns
    -------
    None
    """
    type_code_set = set(['b', 'B', 'u', 'h', 'H', 'i', 'I', 'l', 'L', 'q', 'Q', 'f', 'd', 'x'])

    # 1. check the format of processes
    for process_name in processes:
        process = processes[process_name]
        stream_name_set = set([]) # used to check stream name duplicates
        stream_name_type_list = process['inputs'] + process['outputs']
        if 'sources' in process.keys():
            # to check for duplicate stream name for source as well
            for stream in process['sources']: 
                stream_name_type_list.append((stream, process['sources'][stream]['type']))
        for stream_name_type in stream_name_type_list:
            # check stream_name_type format validity
            assert type(stream_name_type) == tuple, \
                "stream_name_type of process '{}' is not a tuple".format(process_name)
            # check stream name validity
            assert type(stream_name_type[0]) == str, \
                "stream '{}' of process '{}' has an invalid name".format(stream_name_type[0], process_name)
            # check stream type validity
            assert stream_name_type[1] in type_code_set, \
                "stream '{}' of process '{}' does not have a valid data type".format(stream_name_type[0], process_name)

            # assert that there is not duplicate stream name in process
            assert stream_name_type[0] not in stream_name_set, \
                "process '{}' contains duplicate stream name '{}'".format(process_name, stream_name_type[0])
            stream_name_set.add(stream_name_type[0])

        if 'sources' in process.keys():
            for source_name in process['sources']:
                source = process['sources'][source_name]
                # check that source has both 'type' and 'func'
                assert 'type' in source and 'func' in source, \
                "source '{}' of process '{}' does not contain 'type' or 'func'".format(
                    source_name, process_name)
                # check source type validity
                assert source['type'] in type_code_set, \
                "source '{}' of process  '{}' does not have a valid data type".format(
                    source_name, process_name)

        # need assertion for actuators

    # 2. check the format of connections
    for process_name in connections:
        for stream in connections[process_name]:
            for target_process_stream in connections[process_name][stream]:
                assert (type(target_process_stream) == tuple or
                        type(target_process_stream) == list), \
                    "connection for stream '{}' of process '{}' is '{}' which is not a tuple or list".format(stream, process_name, target_process_stream)
                assert len(target_process_stream) == 2, \
                    "connection for stream '{}' of process '{}' is ill-formatted".format(stream, process_name)
                assert type(target_process_stream[0]) == str and type(target_process_stream[1]) == str, \
                    "connection for stream '{}' of process '{}' does not have str elements".format(stream, process_name)


def check_connections_validity(processes, connections, external_sources={}):
    """
    This function checks whether the connections between processes
    are complete and valid

    Parameters
    ----------
    processes: processes used in multicore applications
    connections: connections between processes in multicore applications

    Returns
    -------
    None
    """
    # make new data structure for checking for convenience - assume format checking is complete
    process_stream_dict, process_stream_type_dict = {}, {}
    for process in processes:
        process_stream_dict[process] = {'in_stream': [], 'out_stream': [], 'source': []} # list of stream names
        process_stream_type_dict[process] = {} # dictionary to track data types of each stream
        for stream in processes[process]['inputs']:
            process_stream_dict[process]['in_stream'].append(stream[0])
            process_stream_type_dict[process][stream[0]] = stream[1]
        for stream in processes[process]['outputs']:
            process_stream_dict[process]['out_stream'].append(stream[0])
            process_stream_type_dict[process][stream[0]] = stream[1]
        if 'sources' in processes[process].keys():
            for source in processes[process]['sources']:
                process_stream_dict[process]['source'].append(source)
                process_stream_type_dict[process][source] = processes[process]['sources'][source]['type']

    # check if all streams in connections are defined in processes
    for process in connections:
        for stream in connections[process]:
            # assert that streams in connections are defined in corresponding processes
            if not stream in external_sources:
                assert stream in process_stream_dict[process]['out_stream'] or \
                       stream in process_stream_dict[process]['source'], \
                "stream '{}' from process '{}' is not defined in processes".format(stream, process)

            for target_process, target_stream in connections[process][stream]:
                # assert that the target process of a stream actually exists
                assert target_process in process_stream_dict, \
                    "process '{}' connected to '{}' does not exist".format(target_process, process)
                # assert that the input stream for the target process is actually an input stream of the process
                assert target_stream in process_stream_dict[target_process]['in_stream'], \
                    "process '{}' does not have in_stream '{}'".format(target_process, target_stream)

    # check if all streams in processes are connected in connections
    ## for process in processes:
    ##     assert process in connections, \
    ##         "process {} is not in connections".format(process)
        # check streams for sources
        for source_name in process_stream_dict[process]['source']:
            # source must be connected to at least one input stream of processes
            source_cnt = 0
            for process_name in connections:
                if source_name in connections[process_name]:
                    source_cnt += 1
            assert source_cnt > 0, \
                "source '{}' must be connected to at least one input stream of any process".format(source_name)

            # source must be connected to valid input streams of processes
            for process_name in connections:
                if source_name in connections[process_name]:
                    for target_process, target_stream in connections[process_name][source_name]:
                        assert target_process in process_stream_dict, \
                            "process '{}' connected to source '{}' does not exist".format(target_process, source_name)
                        assert target_stream in process_stream_dict[target_process]['in_stream'], \
                            "source '{}' is not connected to stream '{}'".format(source_name, target_stream)

        # check if output streams are stated in connections
        ## for out_stream_name in process_stream_dict[process]['out_stream']:
        ##     assert out_stream_name in connections[process], \
        ##         "out_stream '{}' of process '{}' is not stated in connections".format(out_stream_name, process)

        # check if input streams of processes are connected to output streams of other processes
        # assume that input stream must be connected to one output stream i.e. not multiple streams
        for in_stream_name in process_stream_dict[process]['in_stream']:
            in_stream_cnt = 0
            for process_name in connections:
                for stream_name in connections[process_name]:
                    for target_process, target_stream in connections[process_name][stream_name]:
                        if process == target_process and in_stream_name == target_stream:
                            in_stream_cnt += 1
            assert in_stream_cnt == 1, \
                "in_stream '{}' of process '{}' is connected to {} streams".format(in_stream_name, process,
                                                                                   in_stream_cnt)

    # check if the data types of connected streams match
    for process in connections:
        if process != 'external_sources':
            for stream in connections[process]:
                for target_process, target_stream in connections[process][stream]:
                    if stream in (process_stream_dict[process]['out_stream'] +
                                  process_stream_dict[process]['source']):
                        assert process_stream_type_dict[process][stream] \
                          == process_stream_type_dict[target_process][target_stream], \
                          "data types of stream '{}' of '{}' and '{}' of '{}' do not match".format(
                              stream, process, target_stream, target_process)
