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
sys.path.append("../")
from IoTPy.core.stream import Stream, _no_value, run
from IoTPy.agent_types.op import signal_element, map_element
from IoTPy.agent_types.merge import weave_f, merge_asynch, blend
from IoTPy.agent_types.split import split_signal
from IoTPy.agent_types.sink import sink_element
from IoTPy.helper_functions.print_stream import print_stream
from IoTPy.helper_functions.recent_values import recent_values

def sort(lst):
    """
    Notes
    -----
    The program has len(lst)-1 agents indexed i = 1, 2, .. len(lst)-1.
    It has len(lst)+1 streams indexed j = 0, 1, ..., len(lst).
    The content of each stream is a sequence of 1s. Each 1 is a signal
    that an action needs to be executed. The action is on a shared
    data structure which, in this example, is list, called lst.

    agent i is responsible for ensuring lst[i-1] <= lst[i], and this
    agent may modify lst[i-1] and lst[i]. So agent i listens for a
    signal from agent i+1 because agent i+1 may modify lst[i]. Also,
    agent i listens for a signal from agent i-1 because agent i-1 may
    modify lst[i-1]. So, agent i listens to a weave of the signals
    generated by agents i-1 and i+1.

    """
    def flip(i):
        if lst[i-1] > lst[i]:
            lst[i-1], lst[i] = lst[i], lst[i-1]
            # Output a signal because lst has changed.
            return 1
        else:
            # Do not output a signal because lst remained unchanged.
            return _no_value
    # Create streams
    S = [Stream() for i in range(len(lst)+1)]
    # Create agents
    for i in range(1, len(lst)):
        signal_element(
            func=flip, in_stream=weave_f([S[i-1],S[i+1]]),
            out_stream=S[i], i=i)
    # Initiate the algorithm by putting a signal on each stream.
    for stream in S: stream.append(1)
    run()

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
            # Output a signal because D has changed.
            return 1
        else:
            # Do not output a signal because D remained unchanged.
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
    # Start the computation by putting a signal on stream changed[i,j].
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
    sink_element(func=call_halt, in_stream=numbers, N=N, stop=stop)

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
    ## lst = [10, 6, 8, 3, 20, 2, 23, 35]
    ## sort(lst)
    ## print ('lst is ', lst)
    ## assert lst == [2, 3, 6, 8, 10, 20, 23, 35]
    lst = [2, 3, 1, 0]
    sort(lst)
    print ('lst is ', lst)

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

    
            
