import os
import ConfigParser
import shutil

filename = os.path.join(os.path.expanduser("~"), "streampy", "config.ini")
if not os.path.isfile(filename):
    dir = os.path.dirname(filename)
    if not os.path.isdir():
        os.makedirs(os.path.dirname(filename))
    source = os.path.join(os.path.dirname(__file__), "config.ini")
    shutil.copy(source, filename)

Config = ConfigParser.ConfigParser()
Config.read(filename)


def get(key, value):
    """ This function returns the value for a key from config

    Parameters
    ----------
    key : str
        The key to find
    value : str
        The value to find

    Returns
    -------
    str

    """

    return Config.get(key, value)
