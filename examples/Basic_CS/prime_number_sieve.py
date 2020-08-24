"""
This module has implementations of the prime-number sieve of
Erasthostenes. See:
https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes

EXAMPLE 1
The first example computes all primes up to N, for some positive
integer N. This example illustrates how one agent's action can
create other agents.

EXAMPLE 2
The second example computes all primes up to the N-th prime. This
example illustrates the interactions between two asynchronous
computations, one of which stops the other. The two agents are:
(1) An agent that generates primes until a shared variable, stop,
    becomes True, and
(2) an agent that detects that N primes have been generated, and
    then changes the value of the shared variable, stop, to True.

"""
import sys
import os
import math

sys.path.append("../")
from IoTPy.core.stream import Stream, _no_value
from IoTPy.agent_types.op import map_element
from IoTPy.agent_types.sink import sink_element
from IoTPy.agent_types.merge import merge_asynch
from IoTPy.helper_functions.recent_values import recent_values
    
def sieve(in_stream, prime_stream):
    """
    Function used by both examples of prime number sieve.

    Parameters
    ----------
    in_stream: input Stream of positive integers
    prime_stream: Stream of prime numbers
    
    Notes
    -----
    This agent assumes that the first element of in_stream is a prime
    number p. It appends that prime number to prime_stream and then
    creates another sieve agent and passes this new agent the stream
    of elements of in_stream that are not divisible by p.
    
    Operation:
    sieve creates a single sink agent. The sink agent has a single
    input stream, in_stream. The agent encapsulates stateful function
    f which has an initial state of 0. (Sinks have no output streams.)
    
    Let the first element of in_stream be p. We assume that p
    is a prime number. So, function f appends p to prime_stream. Many
    agents append prime numbers to prime_stream, but at most one agent
    does so at a time.

    When function f discovers an element of in_stream that is not a
    multiple of p, f creates a new sieve agent which takes a new
    stream out_stream as its input stream. out_stream consists of
    elements of in_stream that are not multiples of p.

    """
    #---------------------------------------------------------------
    # The function encapsulated by the agent
    #---------------------------------------------------------------
    def f(v, state, prime_stream, out_stream):
        """
        Parameters
        ----------
        v: an element of an input stream
        state: int
          Initially 0, to indicate that no elements of the input stream
          have been read. Then it becomes the first element of the input
          stream, and from then on state remains unchanged.
        prime_stream: Stream
          A stream of prime numbers. This function appends a prime number
          to this stream.
        out_stream: Stream
          Initially an empty stream. It consists of elements of the
          input stream that are not multiples of state (after state
          becomes the first element of the input stream).

        """
        if state == 0:
            # This is the first value read on the input stream.
            # Assumption: first value must be a prime number. So append it
            # to the stream of primes.
            prime_stream.append(v)
            # Make the new state the first value on the input stream. This
            # state remains unchanged from now onwards.
            state = v
            # Create an agent that sieves out_stream.
            sieve(out_stream, prime_stream)
        # Put elements of the input stream that are not multiples of state
        # on the output stream.
        if v % state != 0:
            out_stream.append(v)
        # A stateful function encapsulated by a sink agent must return the
        # next state. So, return state.
        return state
    #---------------------------------------------------------------
    # Create the agent
    #---------------------------------------------------------------
    # Create a sink agent that encapsulates a stateful function f with
    # an initial state of 0. Pass parameters prime_stream and
    # out_stream from the sink agent to its encapsulated function.
    sink_element(func=f, in_stream=in_stream, state=0,
         prime_stream=prime_stream, out_stream=Stream())

def primes_example_1(N):
    """
    This function returns a stream which consists of all primes up to
    N.

    Parameters
    ----------
    N : int
      Integer greater than 2.

    Returns
    -------
    prime_stream: Stream
      Sequence of primes less than or equal to N.

    """
    # 1. Define streams
    numbers = Stream('integers from 2')
    prime_stream = Stream('prime numbers')

    # 2. Define agents
    sieve(numbers, prime_stream)

    # 3. Put values into input stream.
    numbers.extend(list(range(2, N)))

    return prime_stream
    

    
def primes_example_2(N):
    """
    Agent used in example 2 in which prime_stream is the sequence of
    primes up to the N-th prime

    Parameters
    ----------
    N: int
       positive integer

    Returns: first_N, prime_stream
    -------
       first_N: list
         The first N primes
       prime_stream: Stream
         Stream of prime numbers. May have more than N primes
      
    
    Notes
    -----
    sieve creates a single sink agent. The sink agent has a single
    input stream, in_stream. The agent encapsulates stateful function
    f which has an initial state of 0. (Sinks have no output streams.)
    
    Let the first element of in_stream be p. This agent assumes that p
    is a prime number. So, the agent appends p to prime_stream. Many
    agents append prime numbers to prime_stream, but at most one agent
    can do so at a time.

    When the agent discovers an element of in_stream that is not a
    multiple of p, the agent creates a new sieve agent which takes a
    new stream out_stream as its input stream. out_stream consists of
    elements of in_stream that are not multiples of p.

    """

    def execute_until_stop_message(v, state, function):
        function_state, finished_execution = state
        if finished_execution:
            return (_no_value, True)
        index, input_value = v
        if index == 1:
            # This value is from stop_stream
            # Make finished_execution become True because a message
            # was received on stop_stream.
            finished_execution = True
            # From now onwards, no messages are appended to the output
            # stream, and finished_execution remains True forever.
            return (_no_value, (function_state, True))
        # index is 0. So, this value is from state_stream.
        output_value, next_function_state = function(
            input_value, function_state)
        # next_state = (next_function_state, finished_execution)
        return output_value, (next_function_state, finished_execution)


    def generate_numbers_until_stop_message(index_and_value, state):
        # state is initially False and switches to True if a message
        # is received in stop_stream. If state becomes True then it
        # remains True thereafter. After state becomes True no values
        # are appended to the output stream.
        # The elements of the input stream are tuples: index and
        # value.
        # index is 0 for state_stream and 1 for stop_stream.
        index, value = index_and_value
        if index == 1:
            # This value is from stop_stream
            # Make state True because a message was received on
            # stop_stream. 
            # From now onwards, no messages are appended to the output
            # stream, and state remains True.
            return (_no_value, True)
        # index is 0. So, this value is from state_stream.
        if state:
            # Do not append values to the output stream, and state
            # remains True
            return (_no_value, state)
        else:
            # Append the next value to the output stream, and state
            # remains False.
            return (value+1, state)

    def detect_finished_then_send_stop(v, state, N):
        length, stop = state
        # If stop is True then computation must stop
        length += 1
        if length >= N and not stop:
            stop = True
            return (True, (length, stop))
        else:
            return (_no_value, (length, stop))
    
    def first_N_elements(in_stream, N, first_N):
        def first_N_elements_of_stream(v, state, N, first_N):
            if state < N:
                first_N.append(v)
                state += 1
            return state
        sink_element(func=first_N_elements_of_stream, in_stream=in_stream,
             state=0, N=N, first_N=first_N)

    #-----------------------------------------------------------------
    # Define streams
    #-----------------------------------------------------------------
    state_stream = Stream(name='numbers 2, 3, 4, ...')
    stop_stream = Stream(name='stop!')
    prime_stream = Stream(name='prime numbers')
    first_N = []

    #-----------------------------------------------------------------
    # Define agents
    #-----------------------------------------------------------------
    # Create agent that generates 2, 3, 4... until it receives a
    # message on stop_stream

    ## merge_asynch(func=generate_numbers_until_stop_message,
    ##              in_streams=[state_stream, stop_stream],
    ##              out_stream=state_stream, state=False)
    def g(v, state):
        return v+1, state
          
    merge_asynch(func=execute_until_stop_message,
                 in_streams=[state_stream, stop_stream],
                 out_stream=state_stream, state=(None, False),
                 function=g)
    # Create an agent that sieves state_stream to create prime_stream
    # which is a sequence of primes. 
    # We do this by creating a sink agent that encapsulates a stateful
    # function f with an initial state of 0. Pass parameters
    # prime_stream and out_stream from the sink agent to its
    # encapsulated function f.
    sieve(in_stream=state_stream, prime_stream=prime_stream)

    # Create an agent that sends a message on stop_stream when the
    # length of prime_stream exceeds N.
    map_element(func=detect_finished_then_send_stop,
                in_stream=prime_stream, out_stream=stop_stream,
                state=(0, False), N=N)

    first_N_elements(in_stream=prime_stream, N=N, first_N=first_N)

    state_stream.append(2)

    return first_N, prime_stream



def test():
    scheduler = Stream.scheduler

    #---------------------------------------------------------------
    # EXAMPLE 1
    # Makes prime_stream the sequence of primes up to a positive
    # integer N
    #---------------------------------------------------------------
    prime_stream_1 = primes_example_1(30)

    # 4. Step the scheduler
    scheduler.step()

    # 5. Look at the output streams.
    print (recent_values(prime_stream_1))

    first_N, prime_stream_2 = primes_example_2(15)

    # 4. Step the scheduler
    scheduler.step()

    # 5. Look at the output streams.
    print (first_N)
    print (recent_values(prime_stream_2))

if __name__ == '__main__':
    test()
    
    
    
    
