class _close(object):
    """
    _close is the message sent on a stream to indicate that the
    process in which the stream runs should terminate.

    """
    def __init__(self):
        pass

class _no_value(object):
    """
    _no_value is the message sent on a stream to indicate that no
    value is sent on the stream at that point. _no_value is used
    instead of None because you may want an agent to send a message
    with value None and for the agent receiving that message to
    take some specific action.

    """
    def __init__(self):
        pass
