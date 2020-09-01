"""
Implements the Misra_Gries Heavy Hitters algorithm in IoTPy.
See https://www.assemblesoftware.com/counting-items-in-streams.
authors: Atishay Jain, K. Mani Chandy
date: 26 July, 2019 

"""
import copy
import sys
sys.path.append("../")
from IoTPy.core.stream import Stream, _no_value, run
from IoTPy.agent_types.op import map_element
from IoTPy.helper_functions.print_stream import print_stream

#------------------------------------------------------------------
#THE MISRA GRIES ALGORITHM
#------------------------------------------------------------------
def misra_gries_process_element(v, state, M):

    """
    This function updates the state for a new element
    in the input stream using the Misra-Gries
    algorithm. It outputs the candidates for
    heavy hitters after M elements arrive on the input
    stream. See
    http://www.cs.utexas.edu/users/misra/Notes.dir/HeavyHitters.pdf.

    Parameters
    ----------
    v: object
        An element of the stream
    state: list of 3 elements
        state[0]: is keys
          where keys is list of k items which are
          candidates for heavy hitters or may be None.
        state[1]: is counts
          where counts is a list of k non-negative integers.
          counts[j] corresponds to keys[j], all j.
          counts[j] is the number of times that keys[j] has occurred.
        state[2]: int, nonnegative
          The number of new elements that have
          arrived on the input stream since the
          last output.

    Returns
    -------
       output, next state
       output is the next output element which is the
          current value of (keys, counts).
       next_state is the next state.

    """
    # A new element arrived on the input stream.
    # Obtain keys, counts, index from the state.
    keys, counts, index = state
    # Increment index because a new input element arrived.
    index += 1

    # UPDATE KEYS AND COUNTS
    # If the input element is in keys then increment
    # its count.
    if v in keys:
        pos = keys.index(v)
        counts[pos] += 1
    # If the input element is not in keys and None
    # is in keys, then insert the input element into
    # keys with a count of 1.
    elif None in keys:
        pos = keys.index(None)
        counts[pos] += 1
        keys[pos]  = v
    # If the input element and None are not in keys
    # then decrement counts, and set keys[i] to
    # None for any zero count.
    else:
        for i in range(len(keys)):
            counts[i] -= 1
            if counts[i] == 0:
                keys[i] = None
    # FINISHED UPDATING KEYS AND COUNTS.
    
    if index < M:
        # Not enough inputs for an output.
        # So, output _no_value.
        output = _no_value
    else:
        # Got M inputs; so output a value.
        # Reset index to 0 because we are outputting
        # an element.
        index = 0
    
    next_state = (keys, counts, index)
    return copy.copy(keys), next_state

#-----------------------------------------------------------------------
#            TESTS
#-----------------------------------------------------------------------

def test_Misra_Gries():
    x = Stream('input')
    y = Stream('output')
    k = 2 # number of heavy hitters
    # Creat the Misra Gries Agent
    map_element(func=misra_gries_process_element,
                in_stream=x, out_stream=y,
                state=([None]*k, [0]*k, 0),
                M=1) # M is the window size. Report output every M steps.
    print_stream(y, y.name)

    x.extend([3]*8 + [2]*6 + [3]*4 + [1]*12)
    run()

    x.extend([4]*15 + [3]*14)
    run()

    x.extend([0]*20)
    run()
     



#-----------------------------------------------------------------------
#            RUN TESTS
#-----------------------------------------------------------------------

if __name__ == '__main__':
    test_Misra_Gries()








