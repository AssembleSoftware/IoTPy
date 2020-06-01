"""
These examples illustrate algorithms implemented by nondeterministic
atomic actions. The examples are from the book, "Parallel Program
Design: A Foundation" by Chandy & Misra.  

The efficient way to solve most problems is to execute a deterministic
sequence of actions. The examples are presented merely to show how
IoTPy can implement nondeterministic algorithms written in the UNITY
framework (see the book).

In any point in a computation, at most one agent in a process can
execute an action. Execution proceeds as follows. One agent in a
process is selected nondeterministically and fairly to execute an
action. If the selected agent has not read all the items in its input
streams then the agent executes an action, i.e., it reads the values
currently in its input streams and as a consequence it may append new
values to its output streams. If the selected agent has read all the
items in its input stream then the action is a skip, i.e. nothing is
changed.

Fair selection is the same as in UNITY: every agent will be selected
for execution eventually. For each agent x, at each point in the
computation there will be a later point at which agent x will execute
an action.

If an agent has read all the values in its input streams then the
action of the agent at that point is a skip. If a program consists of
a single process and all agents of the process execute only skips then
the program has reached a fixed point: no values in the program change
from that point onwards. The system detects a fixed point and
execution of the process terminates.

If a program has multiple processes then a separate termination
detection algorithm has to be executed to determine if the program has
reached a fixed point.

An agent in one process communicates with an agent in a different
process through message passing. Agents in different processes do not
share memory.

Agents in different processes can execute actions concurrently;
however, for the purposes of reasoning about the program we can assume
that at each point in the computation only one agent in one process
executes an action.

The following examples illustrate how agents in a single process
operate on shared variables.  These examples show how SIGNAL agents
use shared variables. A signal agent takes an action when there are
new values on its input streams. The agent doesn't inspect the values;
it takes an action regardless of the values and the number of new
values. Its input streams are merely signalling mechanisms to take
action.

Usually, an agent appends a value to a signaling stream to indicate
that the agent has changed a shared variable; an agent that has this
stream as an input stream can then take an action that reads the new
value of the shared variable. Since the value on the signaling stream
is arbitrary, and value can be used; we use the object _changed to
indicate that the state has changed. You can use any value including 1
and TRUE. Likewise, to indicate that a variable has not changed, the
stream signaling changes should have no new value, or equivalently has
_no_value. For convenience, you can also use _unchanged which has the
same effect as _no_value.

The first example is to sort a list in increasing order by flipping
any adjacent pair of elements that are out of order. This example has
one agent for each adjacent pair indexed (i, i+1) of the list, and
this agent is responsible for ensuring that this pair is in increasing
order. In this example, each action is represented by a single agent.

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
import unittest
from IoTPy.core.stream import Stream
from IoTPy.core.helper_control import _no_value, _unchanged, _changed
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.agent_types.op import signal_element, map_element
from IoTPy.agent_types.merge import weave_f
from IoTPy.agent_types.sink import sink
from IoTPy.agent_types.split import split_signal

def sort(lst):
    """
    Parameters
    ----------
    lst: list

    """
    #----------------------------------------------------------------
    # STEP 1. DEFINE FUNCTION TO BE ENCAPSULATED
    
    def flip(index):
        """
        Flips elements of list, lst, if they are out of order.
        
        Parameters
        ----------
        index: index into the array
        
        """
        # Flip elements if out of order and return _changed
        # to indicate a change to to the corresponding index.
        # Return _unchanged if the elements are unchanged.
        if lst[index] > lst[index+1]:
            lst[index], lst[index+1] = lst[index+1], lst[index]
            # Since both lst[index] and lst[index+1] changed value, return
            # _changed for both outputs corresponding to index
            # and index + 1
            return [_changed,_changed]
        else:
            # Since neither lst[index] nor lst[index+1] changed value,
            # return _unchanged for both outputs
            return [_unchanged, _unchanged]

    #----------------------------------------------------------------
    # STEP 2. CREATE STREAMS
    # Create one stream for each index into the array.
    # The stream changed[i] gets a new value when the i-th element
    # of the array is changed.
    indices = range(len(lst))
    changed = [ Stream('changed_' + str(i)) for i in indices]

    #----------------------------------------------------------------
    # STEP 3. CREATE AGENTS
    # Create an agent for each of the elements 0, 1, ..., len(lst)-1,
    # The agent executes its action when it reads a new value on either
    # stream changed[i] or changed[i+1].
    # This agent sends _changed on stream, changed[i], when the agent
    # changes lst[i].
    # Likewise, the agent sends _changed on stream changed[i+1] only
    # when it changes lst[i+1].
    
    # Note: weave_f is used in split_signal below. weave_f returns a
    # stream consisting of the elements of its input streams in the
    # order in which they arrive. In this example, in_stream is a
    # stream of elements from changed[i] and changed[i+1].
    for i in range(len(lst) - 1):
        split_signal(
            func=flip,
            in_stream=weave_f([changed[i], changed[i+1]]),
            out_streams=[changed[i], changed[i+1]],
            name=i, index=i)

    #----------------------------------------------------------------
    #STEP 4. START COMPUTATION
    # Get the scheduler and execute a step.
    scheduler = Stream.scheduler
    # Start the computation by putting any value (1 in this case) in
    # each changed stream.
    for i in indices:
        changed[i].append(1)
    # Start the scheduler.
    scheduler.step()

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
            # Since D[i][k] changed value return _changed
            return(_changed)
        else:
            # Since D[i][k] was changed by this action return _unchanged
            return (_unchanged)

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
                               in_stream=weave_f([changed[i][j], changed[i][k]]),
                               out_stream=changed[i][k],
                               name='triple_'+ str(i)+"_"+str(j)+"_"+str(k),
                               triple=[i, j, k])

    #----------------------------------------------------------------
    #STEP 4. START COMPUTATION
    # Get the scheduler and execute a step.
    scheduler = Stream.scheduler
    # Start the computation by putting a value on changed[i,j].
    for i in indices:
        for j in indices:
            changed[i][j].append(1)
    scheduler.step()
    
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

class test_shared_variables(unittest.TestCase):
    def test_shared_variables(self):
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
    unittest.main()
    
            
