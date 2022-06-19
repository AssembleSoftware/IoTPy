"""
Implements the Misra_Gries Heavy Hitters algorithm in IoTPy.
authors: Atishay Jain, K. Mani Chandy
date: 26 July, 2019 

"""
from stream import Stream, run
from example_operators import single_item

#------------------------------------------------------------------
#THE MISRA GRIES ALGORITHM
#------------------------------------------------------------------
def misra_gries_process_element(v, candidates, inputs, N):

    """
    The Misra-Gries algorithm identifies candidates for the N heavy
    hitters in a stream. A candidate for a heavy hitter in a stream
    of length L is an item that appears at least ceiling(N/L) times
    in the stream. The algorithm guarantees that all heavy hitters
    are identified as candidates; however, not all identified
    candidates are necessarily heavy hitters. To check whether
    a candidate is a heavy hitter we run through the stream again,
    counting the number of times the candidate appeared.

    This function updates the state for a new element in the input
    stream using the Misra-Gries algorithm.
    See
    http://www.cs.utexas.edu/users/misra/Notes.dir/HeavyHitters.pdf.

    Parameters
    ----------
    v: object
        An element of the input stream
    N: positive integer (constant)
    candidates: dict
        key: item of input stream
        value: int
             A lower bound on the number of times the key has
             appeared on the input stream.
    inputs: dict
        key: item
        value: number of times the item appears in the stream
        THIS IS USED ONLY FOR DEBUGGING AND EXPLANATION!
        REMOVE FOR USE IN AN APPLICATION.
    


    Returns
    -------
       Updates candidates and inputs

    """

    # If the input element is in candidates then increment
    # its count.
    if v in candidates:
        candidates[v] += 1
    # If the input element is not in candidates and there are
    # fewer than N candidates, insert the input element in
    # candidates.
    elif len(candidates) < N:
        candidates[v] = 1
    # If the input element is not in candidates and if the
    # number of candidates is N, then decrement counts for
    # all candidates.
    else:
        for key, value in candidates.items(): candidates[key] -= 1
    # Remove candidates whose count is reduced to 0.
    zero_count_candidates = [key for key in candidates.keys() if candidates[key] == 0]
    for candidate in zero_count_candidates:
        del candidates[candidate]

    # FOR DEBUGGING AND EXPLANATION ONLY: UPDATE INPUTS
    if v in inputs.keys(): inputs[v] += 1
    else: inputs[v] = 1

    # PRINTS FOR EXPLANATION.
    print('inputs')
    print(inputs)
    print('candidates')
    print(candidates)
    print()

#-----------------------------------------------------------------------
#            TESTS
#-----------------------------------------------------------------------

def test_Misra_Gries():
    # Declare streams.
    x = Stream('input')
    # Create the Agent
    single_item(in_stream=x,
        func=misra_gries_process_element, candidates={},
        inputs={}, N=2)

    # Put data into streams and run.
    x.extend([3])
    run()

    x.extend([2])
    run()

    x.extend([3])

    x.extend([2])
    run()

    x.extend([4])
    run()

    x.extend([4, 4, 4])
    run()
     



#-----------------------------------------------------------------------
#            RUN TESTS
#-----------------------------------------------------------------------

if __name__ == '__main__':
    test_Misra_Gries()








