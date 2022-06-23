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
    Parameters
    ----------
    v: object
        An element of the input stream
    candidates: dict
        key: item of input stream
        value: int
             A lower bound on the number of times the key has
             appeared on the input stream.
        initially: empty
    inputs: dict
        key: item
        value: number of times the item appears in the stream
        initially: empty
        THIS IS USED ONLY FOR DEBUGGING AND EXPLANATION!
        REMOVE FOR USE IN AN APPLICATION.
    N: positive integer (constant)
       A heavy hitter appears more than L/N times in a stream
       of length L.
    

    Returns: None
    -------
       Updates candidates and inputs

    """

    # Step 1. If the input element, v, is already a candidate then
    # increment v' count.
    if v in candidates: candidates[v] += 1
    # Step 2. If v is not already a candidate, and there are fewer
    # than N-1 candidates, then add v as a candidate.
    elif len(candidates) < N-1: candidates[v] = 1
    # Step 3. If v is not already a candidate and there are already
    # N-1 candidates then decrement the count for all candidates
    else:
        for key, value in candidates.items():
            candidates[key] -= 1
    #Step 4. Remove candidates whose count is reduced to 0.
    zero_count_candidates = \
      [key for key in candidates.keys() if candidates[key] == 0]
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
    print('remove non heavy hitters from candidates')
    sum_values = sum([value for value in candidates.values()])
    smaller_candidate_set = \
      [key for key in candidates.keys()
           if candidates[key] >=sum_values/N]
    print(smaller_candidate_set)
    
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
        inputs={}, N=3)

    # Put data into streams and run.
    x.extend([3])
    run()

    x.extend([2])
    run()


    x.extend([1])
    run()

    x.extend([3, 3, 3])

    x.extend([2, 2])
    run()

    x.extend([4, 4, 4, 4, 4, 4,])
    run()
    
     



#-----------------------------------------------------------------------
#            RUN TESTS
#-----------------------------------------------------------------------

if __name__ == '__main__':
    test_Misra_Gries()








