import os
import json
import shutil
from tinydb import TinyDB, Query

from multiprocessing import Lock

filename = os.path.join(os.path.expanduser("~"), ".iotpy", "templates.json")

if not os.path.isfile(filename):
    dir = os.path.dirname(filename)
    if not os.path.isdir(dir):
        os.makedirs(os.path.dirname(filename))
    source = os.path.join(os.path.dirname(__file__), "..", "templates.json")
    shutil.copy(source, filename)

db = TinyDB(filename)
Template = Query()


mutex = Lock()


def find(name):
    """ Finds a template in the db

    Parameters
    ----------
    name : str
        Name of the template

    Returns
    -------
    list
        List of templates

    """
    with mutex:
        return db.search(Template.name == name)


def get_template(name):
    """ Finds and returns a template in the db

    Parameters
    ----------
    name : str
        Name of the template

    Returns
    -------
    dict or None
        If template is found, dict is returned. Otherwise None is returned.

    """
    template_data = find(name)
    if len(template_data) > 0:
        template_arguments = template_data[0]
        args_dict = json.loads(template_arguments["template"])
        return args_dict
    else:
        return None


def save_template(template):
    """ Saves template in the db.

    This function takes as input a dict specifying a template and saves it in
    the db. If the template already exists, it is updated.

    Parameters
    ----------
    template : dict
        Dict specifying template

    """
    name = template["name"]
    results = find(name)

    # Insert new template
    if len(results) == 0:
        db.insert({"name": name, "template": json.dumps(template)})

    # Update template
    else:
        db.update({"template": json.dumps(template)}, Template.name == name)


def is_stream(name):
    """ Returns whether a template has stream fields

    Parameters
    ----------
    name : str
        Name of the template

    Returns
    -------
    bool
        Returns true if the template has stream inputs/outputs, False
        otherwise. If template does not exist, False is returned.

    """
    args_dict = get_template(name)

    # If template does not exist, return False
    if args_dict is None:
        return False
    for field in args_dict["inputs"] + args_dict["outputs"]:
        if isinstance(field, list) and field[0] == "stream":
            return True
