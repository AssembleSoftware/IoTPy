

def assemble(params):
    """ Gets the attribute of a value

    Parameters
    ----------
    params : dict
        Dict of values.

    """
    value = params["in"]
    attribute = params["attribute"]
    params["out"].value = getattr(value, attribute)
