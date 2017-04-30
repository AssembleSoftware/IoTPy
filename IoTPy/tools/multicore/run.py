import IoTPy.tools.component
from IoTPy.tools.db import get_template
from .sink import sink
from .source import source


def run(name, template_name, module_name, dict_parts, queues):
    """ Assembles a template and starts  sink and source

    Parameters
    ----------
    name : str
        Name of the part
    template_name : str
        Name of the template
    module_name : str
        Name of the module
    dict_parts : dict
        Dict containing values for fields
    queues : dict
        Dict of queues for each part

    """
    args_dict = get_template(template_name)
    IoTPy.tools.component.Component(
        name, template_name, module_name, dict_parts)
    print "Sink for {0}".format(name)
    sink(queues, args_dict["outputs"], dict_parts)

    queue = queues[name]
    source(queue, dict_parts)
