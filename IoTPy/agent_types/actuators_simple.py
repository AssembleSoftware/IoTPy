def print_from_queue(q):
    """
    prints values read from queue q to
    standard out.

    """
    while True:
        v = q.get()
        if v is None:
            # exit loop
            return
        else:
            print (str(v))

class queue_to_file(object):
    """
    self.actuate(a) puts values from a queue q
    into the file called self.filename

    """
    def __init__(self, filename, timeout=0):
        self.filename = filename
        self.timeout = timeout

    def actuate(self, q):
        with open(self.filename, 'w') as the_file:
            while True:
                try:
                    v = q.get(timeout=self.timeout)
                except:
                    # No more input for this actuator
                    return
                if v is None:
                    # exit loop
                    return
                else:
                    the_file.write(str(v) + '\n')

    
