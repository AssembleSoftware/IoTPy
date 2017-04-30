

def assemble(params):
    """ Runs a function

    Parameters
    ----------
    params : dict
        Dict of values

    """

    func = params["function"]
    parameters = params["parameters"]
    params["out"].value = func(*parameters)
