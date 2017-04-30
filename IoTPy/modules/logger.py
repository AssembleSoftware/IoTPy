import logging


def log(x, filename):
    print x
    logging.basicConfig(filename=filename, level=logging.DEBUG)
    logging.info(str(x))
