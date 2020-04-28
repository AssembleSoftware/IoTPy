"""
This module has examples of splitting a stream
into multiple streams.

"""
import sys
sys.path.append("../../IoTPy/helper_functions")
sys.path.append("../../IoTPy/core")
sys.path.append("../../IoTPy/agent_types")

# stream, helper_control are in IoTPy/IoTPy/core
from stream import Stream, run
from helper_control import _no_value, _multivalue
# recent_values is in IoTPy/IoTPy/helper_functions
from recent_values import recent_values
# split, basics are in IoTPy/IoTPy/agent_types
from split import split_element, split_window
from split import split_element_f, split_window_f
from basics import split_e, split_w, fsplit_2e, fsplit_2w

def examples():
    #----------------------------------------------
    # EXAMPLE: SIMPLE SPLIT
    # Split a stream into a list of streams. In this
    # example, a stream (s) is split into two streams:
    # u and v.
    # Decorate a conventional function to get a
    # stream function. This function returns a list
    # of two values corresponding to the two output
    # streams.
    @split_e
    def h(x):
        return [2*x, x+1000]

    # Create streams.
    s = Stream()
    u = Stream()
    v = Stream()

    # Create agents by calling the decorated function.
    h(s, [u,v])

    # Put data into input streams.
    DATA = list(range(5))
    s.extend(DATA)

    # Run the agents.
    run()

    # Check values of output streams.
    assert recent_values(u) == [2*x for x in DATA]
    assert recent_values(v) == [x+1000 for x in DATA]

    #----------------------------------------------
    # EXAMPLE: SPLIT WITH KEYWORD ARGUMENT
    # Split a stream into a list of streams. Use
    # a keyword argument in the splitting function.
    # Decorate a conventional function to get a
    # stream function. This function returns a list
    # of two values corresponding to the two output
    # streams. addend is a keyword argument in the
    # function that creates agents.
    @split_e
    def h(x, addend):
        return [x+addend, x+1000+addend]

    # Create streams.
    s = Stream()
    u = Stream()
    v = Stream()
    # Call decorated function.
    ADDEND=10
    h(s, [u,v], addend=ADDEND)
    # Put data into input streams.
    s.extend(DATA)
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == [x+ADDEND for x in DATA]
    assert recent_values(v) == [x+1000+ADDEND for x in DATA]

    #----------------------------------------------
    # EXAMPLE: SPLIT WITH KEYWORD ARGUMENT AND STATE
    # Split a stream into a list of streams, with
    # a keyword argument and state.
    # Decorate a conventional function to get a
    # stream function. addend and multiplicand are
    # keyword arguments used in the call to create
    # agents. The function h returns 2 values:
    # (1) a list of two numbers corresponding to the
    #     two output streams and
    # (2) the next state.
    @split_e
    def h(v, state, addend, multiplicand):
        next_state = state + 2
        return ([v+addend+state, v*multiplicand+state],
                next_state)

    # Create streams.
    s = Stream()
    u = Stream()
    v = Stream()

    # Call decorated function to create agents. The initial state
    # is 0. Include keyword arguments in the call.
    ADDEND = 10
    MULTIPLICAND = 2
    h(s, [u,v], state=0, addend=ADDEND, multiplicand=MULTIPLICAND)

    # Put data into input streams.
    s.extend(DATA)
    
    # Run the agent.
    run()

    # Check values of output streams.
    assert recent_values(u) == [10, 13, 16, 19, 22]
    assert recent_values(v) == [0, 4, 8, 12, 16]

    #----------------------------------------------
    # EXAMPLE: SPLIT WITH STATE AND NO KEYWORD ARGUMENTS
    # Split a stream into a list of streams, with
    # a state.
    # Decorate a conventional function to get a
    # stream function. This function returns two values
    # a list and the next state, where the list has two
    # values with one value for each output streams.
    @split_e
    def h(v, state):
        next_state = state + 1
        return [v+state, v+1000+state], next_state

    # Create streams.
    s = Stream()
    u = Stream()
    v = Stream()

    # Call decorated function to create agents.
    h(in_stream=s, out_streams=[u,v], state=0)
    # Put data into input streams.
    s.extend(DATA)

    # Run the decorated function.
    run()

    # Check values of output streams.
    assert recent_values(u) == [0, 2, 4, 6, 8]
    assert recent_values(v) == [1000, 1002, 1004, 1006, 1008]

    #----------------------------------------------
    # EXAMPLE: SPLIT USING FUNCTIONAL FORM FOR
    # SPLITTING A STREAM INTO 2 STREAMS.
    # Split a stream into exactly two streams.
    # This is in functional form, i.e. it creates
    # and returns two streams.
    # Decorate a conventional function to get a
    # stream function.
    @fsplit_2e
    def h(v):
        return [v, v+1000]

    # Create streams.
    s = Stream()

    # Call decorated function to create agents
    # Note that h creates streams u, v. It creates
    # 2 streams because the decorator is fsplit_2e 
    u, v = h(s)
    # Put data into input streams.
    s.extend(DATA)
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == DATA
    assert recent_values(v) == [1000+x for x in DATA]

    #----------------------------------------------
    # EXAMPLE: SPLIT USING FUNCTIONAL FORM FOR
    # SPLITTING A STREAM INTO 2 STREAMS.
    # Split a stream into exactly two streams, with a
    # keyword argument. This is in functional 
    # form, i.e. it creates and returns two streams.
    # Decorate a conventional function to get a
    # stream function.
    @fsplit_2e
    def h(v, addend):
        return [v+addend, v+1000+addend]

    # Create streams.
    s = Stream()

    # Call decorated function to create agents. Note
    # functional form.
    u, v = h(s, addend=10)

    # Put data into input streams.
    s.extend(DATA)

    # Run the agents.
    run()

    # Check values of output streams.
    assert recent_values(u) == [10, 11, 12, 13, 14]
    assert recent_values(v) == [1010, 1011, 1012, 1013, 1014]

    #----------------------------------------------
    # EXAMPLE: FUNCTIONAL FORM
    # Split a stream into exactly two streams, with a
    # state and keyword argument. This is in functional 
    # form, i.e. it creates and returns two streams.
    # Decorate a conventional function to get a
    # stream function.
    @fsplit_2e
    def h(v, state, addend):
        next_state = state + 1
        return ([v+addend+state, v+1000+addend+state],
                next_state)
    # Create streams.
    s = Stream()
    # Call decorated function.
    u, v = h(s, state=0, addend=10)
    # Put data into input streams.
    s.extend(list(range(5)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == [10, 12, 14, 16, 18]
    assert recent_values(v) == [1010, 1012, 1014, 1016, 1018]

    #----------------------------------------------
    # Split a stream into exactly two streams, with a
    # state. This is in functional form,
    # i.e. it creates and returns two streams.
    # Decorate a conventional function to get a
    # stream function.
    @fsplit_2e
    def hk(v, state):
        next_state = state + 1
        return [v+state, v+1000+state], next_state
    # Create streams.
    s = Stream()
    # Call decorated function.
    u, v = h(s, state=0, addend=10)
    u, v = hk(s, state=0)
    # Put data into input streams.
    s.extend(list(range(5)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == [0, 2, 4, 6, 8]
    assert recent_values(v) == [1000, 1002, 1004, 1006, 1008]

    #----------------------------------------------
    # Split a stream into a list of streams.
    # Window operation
    # Decorate a conventional function to get a
    # stream function.
    @split_w
    def h(window):
        return [sum(window), max(window)]
    # Create streams.
    s = Stream()
    u = Stream()
    v = Stream()
    # Call decorated function.
    h(s, [u,v], window_size=3, step_size=2)
    # Put data into input streams.
    s.extend(list(range(12)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == [3, 9, 15, 21, 27]
    assert recent_values(v) == [2, 4, 6, 8, 10]

    #----------------------------------------------
    # Split a stream into a list of streams with
    # keyword argument. Window operation
    # Decorate a conventional function to get a
    # stream function.
    @split_w
    def h(window, addend):
        return [sum(window)+addend, max(window)+addend]

    # Create streams.
    s = Stream()
    u = Stream()
    v = Stream()

    # Call decorated function to create agents.
    h(s, [u,v], window_size=3, step_size=2, addend=1000)

    # Put data into input streams.
    s.extend(list(range(12)))

    # Run the agents.
    run()

    # Check values of output streams.
    assert recent_values(u) == [1003, 1009, 1015, 1021, 1027]
    assert recent_values(v) == [1002, 1004, 1006, 1008, 1010]

    #----------------------------------------------
    # Split a stream into a list of streams with state and
    # keyword argument. Window operation
    # Decorate a conventional function to get a
    # stream function.
    @split_w
    def h(window, state, addend):
        next_state = state + 1
        return ([sum(window)+addend+state,
                max(window)+addend+state], next_state)
    # Create streams.
    s = Stream()
    u = Stream()
    v = Stream()
    # Call decorated function.
    h(s, [u,v], window_size=3, step_size=2, state=0, addend=1000)
    # Put data into input streams.
    s.extend(list(range(12)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == [1003, 1010, 1017, 1024, 1031]
    assert recent_values(v) == [1002, 1005, 1008, 1011, 1014]

    #----------------------------------------------
    #       SPLITTING WITH WINDOWS
    #----------------------------------------------
    # EXAMPLE
    # Split a stream into a list of streams with state.
    # Window operation
    # Decorate a conventional function to get a
    # stream function. The first argument of the function
    # is a list, i.e., the window. The function returns
    # two values: a list and the next state where the list
    # has one item for eah output stream.
    @split_w
    def h(window, state):
        next_state = state + 1
        return [sum(window)+state, max(window)+state], next_state

    # Create streams.
    s = Stream()
    u = Stream()
    v = Stream()

    # Call decorated function to create agents.
    h(s, [u,v], window_size=3, step_size=2, state=0)

    # Put data into input streams.
    s.extend(list(range(12)))

    # Run the agents.
    run()

    # Check values of output streams.
    assert recent_values(u) == [3, 10, 17, 24, 31]
    assert recent_values(v) == [2, 5, 8, 11, 14]

    #----------------------------------------------
    # Split a stream into exactly TWO streams.
    # WINDOW operation
    # Decorate a conventional function to get a
    # stream function. This is in functional form,
    # i.e. it creates and returns a list of streams.
    @fsplit_2w
    def h(window):
        return sum(window), max(window)
    # Create streams.
    s = Stream()
    # Call decorated function. This function
    # creates and returns two streams.
    u, v = h(s, window_size=3, step_size=2)
    # Put data into input streams.
    s.extend(list(range(12)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == [3, 9, 15, 21, 27]
    assert recent_values(v) == [2, 4, 6, 8, 10]

    #----------------------------------------------
    # Split a stream into exactly two streams with 
    # keyword argument. Window operation
    # Decorate a conventional function to get a
    # stream function. This is in functional form,
    # i.e. it creates and returns two streams.
    @fsplit_2w
    def h(window, addend):
        return sum(window)+addend, max(window)+addend*2
    # Create streams.
    s = Stream()
    # Call decorated function. This function
    # creates and returns two streams.
    u, v = h(s, window_size=3, step_size=2, addend=1000)
    # Put data into input streams.
    s.extend(list(range(12)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == [1003, 1009, 1015, 1021, 1027]
    assert recent_values(v) == [2002, 2004, 2006, 2008, 2010]


    #----------------------------------------------
    # Split a stream into exactly two streams with 
    # state and keyword argument. Window operation
    # Decorate a conventional function to get a
    # stream function. This is in functional form,
    # i.e. it creates and returns two streams.
    @fsplit_2w
    def h(window, state, addend):
        next_state = state + 1
        return ([sum(window)+addend+state,
                max(window)+addend*2-state], next_state)
    # Create streams.
    s = Stream()
    # Call decorated function. This function
    # creates and returns two streams.
    u, v = h(s, window_size=3, step_size=2,
             state=0, addend=1000)
    # Put data into input streams.
    s.extend(list(range(12)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == [1003, 1010, 1017, 1024, 1031]
    assert recent_values(v) == [2002, 2003, 2004, 2005, 2006]

    #----------------------------------------------
    # Split a stream into exactly two streams with 
    # state. Window operation
    # Decorate a conventional function to get a
    # stream function. This is in functional form,
    # i.e. it creates and returns two streams.
    @fsplit_2w
    def h(window, state):
        next_state = state + 1
        return [sum(window)+state, max(window)-state], next_state
    # Create streams.
    s = Stream()
    # Call decorated function. This function
    # creates and returns two streams.
    u, v = h(s, window_size=3, step_size=2, state=0)
    # Put data into input streams.
    s.extend(list(range(12)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(u) == [3, 10, 17, 24, 31]
    assert recent_values(v) == [2, 3, 4, 5, 6]

if __name__ == '__main__':
    examples()

