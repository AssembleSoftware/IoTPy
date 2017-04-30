from .helper_functions import extend, get_function, get_value, parse_fields
from .db import get_template, is_stream
from .parameter import get_external, get_internal, Parameter

from IoTPy.code.stream import Stream

from .value import Value
from . import multicore
from . import distributed

import threading
from multiprocessing import Process, Queue
import importlib
import pika
import jsonpickle


class Component:
    """Class for a template

    This class creates a template and assembles its subparts.

    Parameters
    ----------
    name : str
        Name of the part
    template_name : str
        Name of the template
    module_name : str
        Name of the module calling assemble
    dict_parts : dict
        Keyword arguments. All inputs and outputs (non-optional) must be
        keywords
    multiprocessing : bool, optional
        Describes whether to run the template using multiprocessing (the
        default is False).
    distributed : bool, optional
        Describes whether to run the template using distributed computing (the
        default is False).
    host : str, optional
        Name of the server for rabbitmq if using distributed (the default is
        localhost).
    user : str, optional
        Name of the user for rabbitmq (the default is guest)
    password : str, optional
        User password for rabbitmq (the default is guest)

    Attributes
    ----------
    name : str
        The name of the part
    template_name : str
        The name of the template

    """
    def __init__(self, name, template_name, module_name, dict_parts,
                 multiprocessing=False, distributed=False, host="localhost",
                 user="guest", password="guest"):
        self.name = name
        self.template_name = template_name
        self._module_name = module_name
        self._multiprocessing = multiprocessing
        self._distributed = distributed
        self._host = host
        self._user = user
        self._password = password
        self._components = []

        self._run(dict_parts)

    def _run(self, dict_parts):

        # Get the template from the db
        args_dict = get_template(self.template_name)
        assembly = args_dict['assembly']

        inputs = []

        # Check for missing fields and handle field types
        for field in args_dict["inputs"] + args_dict["outputs"]:
            field_name = field

            # field = type, field
            if isinstance(field, list):
                field_name = field[1]

            if field in args_dict["inputs"]:
                inputs.append(field_name)

            # Field (non-optional) is missing
            if field_name not in dict_parts and field_name not in args_dict["optional"]:
                raise Exception(
                    "{0} in {1} not specified".format(
                        field_name, "fields"))

            # Optional field is missing
            elif field_name not in dict_parts:
                dict_parts[field_name] = None
                continue

            # Handle field types
            if isinstance(field, list):
                field_type, field_name = field

                # Parse functions
                if field_type == "function":
                    # Get function name
                    function_name = dict_parts[field_name].value
                    dict_parts[field_name].value = get_function(
                        function_name, self._module_name)

                # Create streams
                if field_type == "stream":
                    try:
                        # List of streams
                        for x in dict_parts[field_name]:
                            if x.value is None:
                                x.value = Stream()
                    # One stream
                    except BaseException:
                        if dict_parts[field_name].value is None:
                            dict_parts[field_name].value = Stream()

        # Assembly
        if assembly == "assemble":
            subparts_dict = {}

            components = args_dict['components']

            # Multiprocessing queues
            queues = {}
            queues[self.name] = Queue()

            for part_name, template_name in components:
                subparts_dict[part_name] = {}
                if self._multiprocessing:
                    queues[part_name] = Queue()

            # Externals
            externals = args_dict['externals']
            for external in externals:
                assembled_name = external[0]
                param = external[1:]
                p = get_external(param)
                component = p.name
                param = p.param
                index = p.index

                if param not in subparts_dict[component] and index is not None:
                    # Create list
                    subparts_dict[component][param] = [None] * (index + 1)

                # Index is greater than length of list
                elif index is not None and index >= len(subparts_dict[component][param]):
                    # Extend list
                    extend(subparts_dict[component][param], index)

                # Parse the field and set param or param[index] to the field
                value = parse_fields(assembled_name, dict_parts)
                if not isinstance(value, Value):
                    value = Value(value)
                if index is not None:
                    subparts_dict[component][param][index] = value
                else:
                    subparts_dict[component][param] = value

                # Add to list of destinations
                if self._multiprocessing or self._distributed:
                    if assembled_name in inputs:
                        value.dest.append(Parameter(component, param, index))

                    # Param is output
                    else:
                        value.dest.append(
                            Parameter(
                                self.name,
                                assembled_name,
                                None))

            # Internals
            internals = args_dict['internals']
            for internal in internals:
                source, des = get_internal(internal)
                if source.param not in subparts_dict[source.name]:
                    if source.index is not None:
                        # Create list
                        params = [None] * (source.index + 1)
                        params[source.index] = Value()
                        subparts_dict[source.name][source.param] = params
                    else:
                        subparts_dict[source.name][source.param] = Value()

                # Source param exists
                elif source.index is not None:
                    # Index is greater than length of list
                    if source.index >= len(
                            subparts_dict[source.name][source.param]):
                        # Extend list
                        extend(subparts_dict[source.name]
                               [source.param], source.index)

                    # Source value doesn't exist
                    if subparts_dict[source.name][source.param][source.index] is None:
                        # Create new value
                        subparts_dict[source.name][source.param][source.index] = Value(
                        )

                if des.param not in subparts_dict[des.name] and des.index is not None:
                    # Create list
                    params = [None] * (des.index + 1)
                    subparts_dict[des][des.param] = params

                # Destination param exists
                elif des.index is not None:
                    # Index is greater than length of list
                    if des.index >= len(subparts_dict[des.name][des.param]):
                        # Extend list
                        extend(subparts_dict[des.name][des.param], des.index)

                # Set des param to source param
                if source.index is not None:
                    value = subparts_dict[source.name][source.param][source.index]
                else:
                    value = subparts_dict[source.name][source.param]

                if des.index is not None:
                    subparts_dict[des.name][des.param][des.index] = value
                else:
                    subparts_dict[des.name][des.param] = value

                if self._multiprocessing or self._distributed:
                    value.dest.append(des)

            # Assemble subparts

            for part_name, template_name in components:

                # Create process for subparts with streams
                if self._multiprocessing and is_stream(template_name):
                    p = Process(
                        target=multicore.run,
                        args=(
                            part_name,
                            template_name,
                            self._module_name,
                            subparts_dict[part_name],
                            queues))
                    p.daemon = True
                    p.start()

                # Send subpart
                elif self._distributed:
                    connection = pika.BlockingConnection(pika.URLParameters(
                        "amqp://{0}:{1}@{2}/%2f".format(
                            self._user, self._password, self._host)))
                    channel = connection.channel()

                    args = self.name, part_name, template_name, self._module_name, subparts_dict[
                        part_name]
                    body = jsonpickle.encode(args)
                    channel.basic_publish(
                        exchange='', routing_key='assemble', body=body)

                # Assemble subpart
                else:
                    subpart = Component(
                        part_name,
                        template_name,
                        self._module_name,
                        subparts_dict[part_name])
                    self._components.append(subpart)

            # Create sink and source for multiprocessing
            if self._multiprocessing:
                multicore.sink(queues, args_dict["inputs"], dict_parts)
                t = threading.Thread(target=multicore.source, args=(
                    queues[self.name], dict_parts))
                t.daemon = True
                t.start()

            # Create sink and source for distributed
            if self._distributed:
                distributed.sink(
                    self.name,
                    args_dict["inputs"],
                    dict_parts,
                    self._host,
                    self._user,
                    self._password)
                t = threading.Thread(
                    target=distributed.source,
                    args=(
                        self.name,
                        self.name,
                        dict_parts,
                        self._host,
                        self._user,
                        self._password))
                t.daemon = True
                t.start()

        # Encapsulation function
        else:
            # Load module for function
            module = importlib.import_module(
                "IoTPy.encapsulation_functions." +
                assembly + ".assemble")

            # Get values in dict
            dict_parts = get_value(dict_parts)

            # Get assembly
            f = getattr(module, "assemble")

            # Assemble part
            subpart = f(dict_parts)
