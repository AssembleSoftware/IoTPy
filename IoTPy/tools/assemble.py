from .db import get_template
from .value import Value
import pika

from . import component


def assemble(name, template_name, module_name, multiprocessing=False,
             distributed=False, host="localhost",
             user="guest", password="guest", **kwargs):
    """
    Assembles a part.

    Parameters
    ----------
    name : str
        Name of the part
    template_name : str
        Name of the template
    module_name : str
        Name of the module calling assemble
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
    kwargs : keyword arguments
        Keyword arguments. All inputs and outputs (non-optional) must be
        keywords

    Returns
    -------
    Component
        The component for the template

    """

    # Get the template from the db
    args_dict = get_template(template_name)

    # Template not found
    if args_dict is None:
        raise Exception("Template {0} not found".format(template_name))

    # Wrap parameters in Value
    for param in ["inputs", "outputs"]:
        for param_name in args_dict[param]:

            # Param name = type, name
            if isinstance(param_name, list):
                param_name = param_name[1]

            if param_name in args_dict["optional"] and param_name not in kwargs:
                continue

            if isinstance(kwargs[param_name], list):
                kwargs[param_name] = [Value(x) for x in kwargs[param_name]]
            else:
                kwargs[param_name] = Value(kwargs[param_name])

    # Create exchange for template if using distributed
    if distributed:
        connection = pika.BlockingConnection(pika.URLParameters(
            "amqp://{0}:{1}@{2}/%2f".format(user, password, host)))
        channel = connection.channel()

        channel.exchange_declare(exchange=name, type='direct')

    return component.Component(name, template_name, module_name, kwargs,
                     multiprocessing, distributed, host, user, password)
