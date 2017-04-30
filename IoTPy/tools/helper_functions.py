import sys
import importlib


def get_function(func_name, module_name):
    """ Returns a function.

    This function takes as input a function name and a module name and returns
    the function.

    Parameters
    ----------
    func_name : str or function
        Name of the function. If func_name is a function, it is returned.
        Otherwise if func_name has module namespaces, it is returned from the
        modules directory. E.g. if func_name == module_1.func,
        func is defined in modules/module_1.py

    module_name : str
        Name of the module where the function is defined. Used if func_name
        does not have modules.

    Returns
    -------
    function
        Function with name func_name

    """

    # Func_name is a function
    if not isinstance(func_name, basestring):
        return func_name

    modules = func_name.split(".")

    # No modules, return function from module_name
    if len(modules) == 1:
        func = getattr(sys.modules[module_name], func_name)

    # Function in modules
    else:
        module_name = ".".join(modules[0:-1])
        func_name = modules[-1]
        module = importlib.import_module(
            "IoTPy.modules." + module_name)
        func = getattr(module, func_name)
    return func


def parse_fields(field, dict_parts):
    """
    Parses fields and returns the field if it is enclosed in \" or if it is a
    number, otherwise returns the value in dict_parts

    Parameters
    ----------
    field : str or float or list
        The field to parse
    dict_parts : dict
        Dictionary containing values for the part

    Returns
    _______
    field
        Parsed field
    """

    # If field is enclosed in \", return the field as a string
    if field[0] == "\"" and field[-1] == "\"":
        return field[1:-1]

    # If field is "None", return None
    if field == "None":
        return None

    # Return the value of the field
    try:
        return dict_parts[field]
    except BaseException:
        pass

    # Parse field as int or float
    try:
        return int(field)
    except BaseException:
        pass
    try:
        return float(field)
    except BaseException:
        return field


def extend(lst, index):
    """ Extends a list to index

    This function takes as parameters a list and an index, and extends the list
    to have length = index + 1.

    Parameters
    ----------
    lst : list
        The list to extend
    index : int
        The index to extend list to

    """
    lst.extend([None] * (index - len(lst) + 1))


def get_value(dict_parts):
    """ Returns values in dict

    This function returns values in Value objects in dict_parts.

    Parameters
    ----------
    dict_parts: dict
        Dict of Value objects

    Returns
    -------
    dict
        Dict of values

    """
    value = {}
    for key in dict_parts:
        value[key] = get_valueR(dict_parts[key])

    return value


def get_valueR(value):
    """ Recursively returns values in Value objects

    Parameters
    ----------
    value : list or Value
        If value is a list, this function recursively returns the values in the
        list. Otherwise if value is Value, returns the value.

    Returns
    -------
    list or Value or object

    """

    # Recursively get values
    if isinstance(value, list):
        return [get_valueR(val) for val in value]
    try:

        # Return value if not None
        if value.value is not None:
            return value.value
        else:
            return value
    except BaseException:
        return value
