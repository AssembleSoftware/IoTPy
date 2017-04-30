
def source(queue, dict_parts):
    """ Listens on queue and adds values to streams

    Parameters
    ----------
    queue : multiprocessing.Queue
       Queue to listen to
    dict_parts : dict
        Dict containing values for fields

    """
    while True:
        value = queue.get()
        print "Received"
        print value

        # No index
        if len(value) == 2:
            stream_name, stream_value = value
            dict_parts[stream_name].value.append(stream_value)
        else:
            stream_name, stream_index, stream_value = value

            dict_parts[stream_name][stream_index].value.append(stream_value)
