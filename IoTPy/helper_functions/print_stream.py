from ..agent_types.sink import sink_element
# sink is in ../agent_types

def print_stream(in_stream, name=None):
    """
    Creates a sink agent that prints values in in_stream.

    Parameters
    ----------
    in_stream: Stream
       input stream of the sink agent.

    """
    def print_output(v, index):
        if name == None:
            print ('[' + str(index) + '] = ' + str(v))
        else: print (name + '[' + str(index) + '] = ' + str(v))
        return index+1
    sink_element(func=print_output, in_stream=in_stream, state=0)
