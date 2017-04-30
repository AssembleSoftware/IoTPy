import IoTPy.tools.assemble


def addToQueue(value, queue, part_name, name, index=None):
    """ Adds a value to a queue

    Parameters
    ----------
    value : object
        Value to send
    queue : multiprocessing.Queue
        Queue to add value
    part_name : str
        Name of the part to send to
    name : str
        Name of the parameter
    index : int, optional
        Index of the parameter (the default is None)

    """
    if index is None:
        print "Adding {0} to queue for {1} for {2}".format(
            value, part_name, name)
        queue.put([name, value])
    else:
        print "Adding {0} to queue for {1} for {2},{3}".format(
            value, part_name, name, index)
        queue.put([name, index, value])


def sink(queues, fields, dict_parts):
    """ Create sinks for each stream in fields

    Parameters
    ----------
    queues : dict
        Dict of queues for each part
    fields : list
        List of field names
    dict_parts : dict
        Dict containing values for fields

    """
    for field in fields:

        # Typed field
        if isinstance(field, list):
            field_type, field_name = field
            if field_type == "stream":

                # List of streams
                if isinstance(dict_parts[field_name], list):
                    for stream in dict_parts[field_name]:
                        # Iterate over stream destinations
                        for des in stream.dest:
                            queue = queues[des.name]
                            parameters = [queue] + des.to_list()
                            args = {
                                "in": stream.value,
                                "function": addToQueue,
                                "parameters": parameters}

                            IoTPy.tools.assemble.assemble(
                                "sink", "sink", __name__, **args)
                else:
                    # Iterate over stream destinations
                    for des in dict_parts[field_name].dest:
                        queue = queues[des.name]
                        parameters = [queue] + des.to_list()
                        args = {
                            "in": dict_parts[field_name].value,
                            "function": addToQueue,
                            "parameters": parameters}

                        IoTPy.tools.assemble.assemble(
                            "sink", "sink", __name__, **args)
