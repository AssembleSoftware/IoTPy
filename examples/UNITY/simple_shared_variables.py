"""
These examples illustrate algorithms implemented by nondeterministic
atomic actions. These examples are from the book, "Parallel Program
Design: A Foundation" by Chandy & Misra. The most efficient way to
solve most problems is to carry out a deterministic sequence of
actions; these examples of nondeterministic solutions can have poor
performance. They are presented here merely as examples of
nondeterminism and to show how IoTPy can implement algorithms written
in UNITY (see the book).

These examples illustrate how agents manipulate shared variables.
These examples show how SIGNAL streams can be used with shared
variables. Usually, a value is appended to a signal stream when a
shared variable changes value. Agents listen for signals (i.e.,
read signal streams) to detrermine when shared variables of interest
change value. Usually the message in the signal is arbitrary, and
often we use True or 1 as the only message.

The first example is to sort a list in increasing order by flipping
any adjacent pair of elements that are out of order. This example has
one agent for each adjacent pair indexed (i, i+1) of the list, and
this agent is responsible for ensuring that this pair is in increasing
order.

The second example is to find the matrix of shortest-path lengths in a
graph given the edge-weight matrix of the graph. This example has an
agent for every triple (i,j,k) where i,j,k are indices into the
matrix. The agent associated with the triple (i,j,k) is responsible
for ensuring that the triangle inequality holds for this triple, i.e.
d[i,k] <= d[i,j] + d[j,k].

The third example shows how a shared variable, stop, can be used by
one agent to stop the execution of another. This example illustrates
the nondeterministic aspect of these programs.

The examples use arrays of singal streams. The first example, has a
signal stream, changed[i], for each element lst[i] of the list. A
value is appended to changed[i] when lst[i] is changed. The second
example has a signal stream, changed[i,k], for the i,k-th entry into
the matrix, for all i,k. A value is appended to changed[i,k] when
D[i,k] changes. The third example uses a single shared variable, stop,
rather than a signal stream. This is because stop is changed only
once, from False to True. So, stop acts like a signal stream with a
single value.

"""
import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))

from stream import Stream, _no_value
from recent_values import recent_values
from op import signal_element, map_element
from merge import weave_f, merge_asynch, blend
from sink import sink
from split import split_signal
from run import run

def sort(lst):
    def flip(i):
        if lst[i-1] > lst[i]:
            lst[i-1], lst[i] = lst[i], lst[i-1]
            return 1
        else:
            return _no_value
    S = [Stream() for i in range(len(lst)+1)]
    for i in range(1, len(lst)):
        signal_element(func=flip, in_stream=weave_f([S[i-1],S[i+1]]), out_stream=S[i], i=i)
    for stream in S: stream.append(1)
    run()
        

    
## def sort(lst):

    ## # EXAMPLE 2: MATRIX OF LENGTHS OF SHORTEST PATHS
    ## D = [[0, 20, 40, 60], [20, 0, 10, 1], [40, 10, 0, 100],
    ##      [60, 1, 100, 0]]
    ## shortest_path(D)
    ## assert D == [[0, 20, 30, 21], [20, 0, 10, 1],
    ##              [30, 10, 0, 11], [21, 1, 11, 0]]

##     """
##     Parameters
##     ----------
##     lst: list

##     """
##     #----------------------------------------------------------------
##     # STEP 1. DEFINE FUNCTION TO BE ENCAPSULATED
    
##     def flip(I):
##         """
##         Flips elements of list, lst, if they are out of order.
        
##         Parameters
##         ----------
##         I : array of length 1 consisting of index of an element of the
##             list. The index is put into an array because Python passes
##             parameters that are integer by value and arrays by
##             reference. This is merely a trick to pass a parameter by
##             reference.
        
##         """
##         # Extract index from the array.
##         i = I[0]
##         # Flip elements if out of order and return any value (1 in
##         # this case) to indicate a change to lst.
##         # Return no value if the elements are in order.
##         if lst[i] > lst[i+1]:
##             lst[i], lst[i+1] = lst[i+1], lst[i]
##             # Since both lst[i] and lst[i+1] changed value, append
##             # a 1 for both output streams to signal that the values
##             # changed. 
##             return [1,1]
##         else:
##             # Since neither lst[i] nor lst[i+1] changed value, do not
##             # append any values to either output stream.
##             return [_no_value, _no_value]

##     #----------------------------------------------------------------
##     # STEP 2. CREATE STREAMS
##     indices = range(len(lst))
##     changed = [ Stream('changed_' + str(i)) for i in indices]

##     # Create an agent for each of the elements 0, 1, ..., len(lst)-1,
##     # The agent executes its action when it reads a new value on either
##     # stream changed[i] or changed[i+1].
##     # This agent sends a signal (the value 1 in our example)
##     # on stream, changed[i], when, and only when, the agent changes
##     # lst[i]. Likewise, the agent sends a signal on changed[i+1] only
##     # when lst[i+1] changes.

##     #----------------------------------------------------------------
##     # STEP 3. CREATE AGENTS
##     # Note: weave_f is used split_signal below. weave_f returns a
##     # stream consisting of the elements of its input streams in the
##     # order in which they arrive. In this example, in_stream is a
##     # stream of elements from changed[i] and changed[i+1].
##     for i in range(len(lst) - 1):
##         split_signal(
##             func=flip,
##             in_stream=weave_f([changed[i], changed[i+1]]),
##             out_streams=[changed[i], changed[i+1]], name=i, I=[i])

##     #----------------------------------------------------------------
##     #STEP 4. START COMPUTATION
##     # Get the scheduler and execute a step.
##     scheduler = Stream.scheduler
##     # Start the computation by putting any value (1 in this case) in
##     # each changed stream.
##     for i in indices:
##         changed[i].append(1)
##     # Start the scheduler.
##     scheduler.step()

def shortest_path(D):
    """
    Parameters
    ----------
    D: matrix where D[j,k] is the length of the edge from vertex j to
    vertex k.

    Returns
    -------
    D: matrix where D[j,k] is the length of the shortest path from
    vertex j to  vertex k.
    
    """
    #----------------------------------------------------------------
    # STEP 1. DEFINE FUNCTION TO BE ENCAPSULATED
    def triangle_inequality(triple):
        """
        Apply the triangle inequality. If this changes D then
        return any value (1 in our example). If D is unchanged
        then return no value.

        Parameters
        ----------
        triple: 3-element array or list

        """
        i, j, k = triple
        if D[i][j] + D[j][k] < D[i][k]:
            D[i][k] = D[i][j] + D[j][k]
            return 1
        else:
            return _no_value

    #----------------------------------------------------------------
    # STEP 2. CREATE STREAMS
    # Create an array, changed, of streams, where a value is appended
    # to changed[i][k] when D[i][k] is changed.
    indices = range(len(D))
    changed = [[ Stream('changed_'+ str(i)+"-" + str(j))
                 for i in indices] for j in indices]

    #----------------------------------------------------------------
    # STEP 3. CREATE AGENTS
    # Create an agent for each triple i,j,k. The agent executes its
    # action when it reads a new element of stream x. If it changes D
    # it then puts a new element on x.
    for i in indices:
        for j in indices:
            for k in indices:
                signal_element(func=triangle_inequality,
                               in_stream=weave_f([changed[i][j], changed[j][k]]),
                               out_stream=changed[i][k],
                               triple=[i, j, k])

    #----------------------------------------------------------------
    #STEP 4. START COMPUTATION
    # Start the computation by putting a value on changed[i,j].
    for i in indices:
        for j in indices:
            changed[i][j].append(1)
    run()
    
    return D


def stop_agent_when_enough_elements(N):
    """
    Shows how shared variables can be used to stop agents.
    One agent generates a sequence until stopped by another agent.

    Parameters
    ----------
    N: int (positive)

    """
    #----------------------------------------------------------------
    # STEP 1. DEFINE FUNCTIONS TO BE ENCAPSULATED
    def generate_numbers(v, state, stop):
        """
        This function generates the sequence 0, 1, 2, ... starting
        with the specified initial state. The function stops execution
        when stop becomes True.

        Parameters
        ----------
        v: The element in the sequence, 0,1,2,.. read from the input
           stream.
        state: The last element of the sequence
        stop: array of length 1. This is a shared variable of the agent.

        """
        if not stop[0]:
            return state, state+1
        else:
            return _no_value, state

    def call_halt(v, N, stop):
        if v > N:
            stop[0] = True

    #----------------------------------------------------------------
    # STEP 2. CREATE STREAMS AND SHARED VARIABLES
    # stop is a variable shared by both agents that are created
    # below. It is initially False and set to True and then remains
    # True. 
    stop = [False]
    numbers = Stream('numbers')

    #----------------------------------------------------------------
    # STEP 3. CREATE AGENTS
    # Create an agent that reads and writes the same stream: numbers.
    # The agent executes its action when a new value appears on
    # numbers. The action puts the next value on numbers if stop is
    # False. The action has no effect (it is a skip operation) if stop
    # is True.
    map_element(
        func=generate_numbers, in_stream=numbers,
        out_stream=numbers, state=1, stop=stop)
    # Create an agent that sets stop to True after it reads more than
    # N values.
    N = 3
    sink(func=call_halt, in_stream=numbers, N=N, stop=stop)

    #----------------------------------------------------------------
    #STEP 4. START COMPUTATION
    # Get the scheduler and execute a step.
    scheduler = Stream.scheduler
    # Start the computation by putting a value into the numbers stream.
    numbers.append(0)
    scheduler.step()
    # The stream numbers will be 0, 1, ... up to N-1 and possibly may
    # contain additional values. For example, if N = 3 then numbers
    # could be 0, 1, 2 or 0, 1, 2, 3, 4, 5.
    return numbers
    assert list(range(N)) == recent_values(numbers)[:N]

def test_shared_variables():
    # EXAMPLE 1: SORT
    lst = [10, 6, 8, 3, 20, 2, 23, 35]
    sort(lst)
    assert lst == [2, 3, 6, 8, 10, 20, 23, 35]

    # EXAMPLE 2: MATRIX OF LENGTHS OF SHORTEST PATHS
    D = [[0, 20, 40, 60], [20, 0, 10, 1], [40, 10, 0, 100],
         [60, 1, 100, 0]]
    shortest_path(D)
    assert D == [[0, 20, 30, 21], [20, 0, 10, 1],
                 [30, 10, 0, 11], [21, 1, 11, 0]]

    # EXAMPLE 3: STOP WHEN AGENT AFTER N ELEMENTS GENERATED.
    N = 3
    numbers = stop_agent_when_enough_elements(N)
    assert list(range(N)) == recent_values(numbers)[:N]

    print ('TEST OF SHARED VARIABLES IS SUCCESSFUL!')

if __name__ == '__main__':
    test_shared_variables()

    
            
