"""
This module has tests for the agent types iot and
iot_merge.

The iot agent has only two parameters: func and in_stream.
The iot_merge agent also has two parameters func and
in_streams where in_streams is a list of input streams.
Typically, func uses positional or keyword arguments
specified in *args or **kwargs, respectively.
These arguments may include streams and agents.

"""
import numpy as np
import unittest

# agent, stream, helper_control are in IoTPy/IoTPy/core
from IoTPy.core.agent import Agent, InList
from IoTPy.core.stream import Stream, StreamArray, run
# check_agent_parameter_types, recent_values
# are in IoTPy/IoTPy/helper_functions
from IoTPy.core.helper_control import _no_value, _multivalue
from IoTPy.agent_types.check_agent_parameter_types import *
from IoTPy.helper_functions.recent_values import recent_values
# iot is IoTPy/IoTPy/agent_types
from IoTPy.agent_types.iot import iot, iot_merge

#---------------------------------------------------------------------------
#     TESTS
#---------------------------------------------------------------------------
class iot_test(unittest.TestCase):
    
    def test_simple(self):
        """
        Create an agent with a single input stream, x, and a single
        output stream, y. The elements of y are twice the corresponding
        elements of x.

        """
        # Create the streams.
        x = Stream(name='x')
        y = Stream(name='y')

        def f(list_of_numbers, s):
            """
            Parameters
            ----------
            f: func
               the function that is wrapped by iot to create an
               agent.
            list_of_numbers: list
               the list obtained from the input
               stream of the agent and passed to f.
            s: stream
               the output stream of the agent.

            Returns
            -------
            An iot function returns the number of items that it has
            read in its single input stream.
            The function returns len(list_of_numbers) because the
            agent has finished processing the entire input.
            Note that this function uses a stream, s, whereas the other
            agents wrap functions that do not use streams.

            """
            output_list = [2*number for number in list_of_numbers]
            s.extend(output_list)
            return len(list_of_numbers)

        iot(f, x, y)

        # Extend stream x with an array
        x.extend(list(range(5)))
        run()

        assert (recent_values(y) == [0, 2, 4, 6, 8])
        
    def test_simple_array(self):
        """
        Same as test_simple except that StreamArray is used in place
        of Stream.
        
        Create an agent with a single input stream array, x, and a single
        output stream array, y. The elements of y are twice the corresponding
        elements of x.

        """
        # Create the streams arrays.
        x = StreamArray(name='x', dtype=int)
        y = StreamArray(name='y', dtype=int)

        def f(array_of_int, s):
            """
            Parameters
            ----------
            f: func
               the function that is wrapped by iot to create an
               agent.
            array_of_int: NumPy array of int
            s: StreamArray
               the output stream array of the agent.

            Returns
            -------
            The function returns len(array_of_int) because the
            agent has finished processing the entire array.

            """
            s.extend(array_of_int * 2)
            return len(array_of_int)

        # Create the agent by wrapping function f.
        iot(f, x, y)

        # Extend input stream x of the agent with an array
        x.extend(np.arange(5, dtype=int))
        run()
        assert np.array_equal(
            recent_values(y), np.array([0, 2, 4, 6, 8]))

    def test_iot(self):
        x = StreamArray(dtype=int)
        y = StreamArray(dtype=int)
        z = StreamArray(dtype=int)
        u = StreamArray(dtype=int)
        v = StreamArray(dtype=int)
        
        def f(A, y, z):
            """
            Function wrapped by an iot agent. The first parameter
            'A' is an array obtained from the input stream of the
            agent. The other parameters, y and z, are positional
            arguments (*args) of the function.

            The function returns a pointer into the input stream.
            In this example, each call to the function processes
            the entire input array 'A' and so the function returns
            len(A).

            """
            y.extend(2*A)
            z.extend(3*A)
            # Return a pointer into the input array.
            return len(A)

        def g(A, u, v):
            """
            Parameters are similar to f.

            """
            u.extend(A+A)
            v.extend(A**2)
            return len(A)

        # Create agents that wrap functions f and g.
        iot(f, x, y, z)
        iot(g, x, u, v)

        # Extend stream x with an array
        x.extend(np.arange(5, dtype=int))
        run()
        assert np.array_equal(recent_values(y), 2*np.arange(5, dtype=int))
        assert np.array_equal(recent_values(z), 3*np.arange(5, dtype=int))
        assert np.array_equal(recent_values(u), 2*np.arange(5, dtype=int))
        assert np.array_equal(recent_values(v), np.arange(5, dtype=int)**2)

        # Extend stream x with another array
        x.extend(np.arange(5, 10, dtype=int))
        run()
        assert np.array_equal(recent_values(y), 2*np.arange(10, dtype=int))
        assert np.array_equal(recent_values(z), 3*np.arange(10, dtype=int))
        assert np.array_equal(recent_values(u), 2*np.arange(10, dtype=int))
        assert np.array_equal(recent_values(v), np.arange(10, dtype=int)**2)

    def test_iot_merge(self):
        x = StreamArray(dtype=float)
        y = StreamArray(dtype=float)
        z = StreamArray(dimension=2, dtype=float)
        
        def f(A_list, z):
            """
            f is the function wrapped by an iot_merge agent.
            A_list is a list of arrays. A_list[j] is the input array obtained
            from the j-th input stream of the agent that wraps f.
            z is the positional argument of f. z is an output stream that is
            extended by f.

            The agent completes reading n_rows elements of each array in
            A_list where n_rows is the number of elements in the smallest
            array. So, the function returns n_rows.

            """
            n_rows = min([len(A) for A in A_list])
            n_cols = len(A_list)
            out = np.column_stack((A_list[0][:n_rows], A_list[1][:n_rows]))
            z.extend(out)
            return [n_rows for A in A_list]

        # Create the agent by wrapping function f.
        # A_list has two arrays from streams x and y.
        # z is a keyword argument for f.
        iot_merge(f, [x, y], z=z)
        # Extend stream x with [0, 1, 2, 3, 4]
        x.extend(np.arange(5, dtype=float))
        run()
        assert np.array_equal(recent_values(x), np.array(np.arange(5, dtype=float)))
        assert np.array_equal(recent_values(x), np.array([0., 1., 2., 3., 4.]))
        assert np.array_equal(recent_values(y), np.zeros(shape=(0,), dtype=float))
        assert np.array_equal(recent_values(z), np.zeros(shape=(0, 2), dtype=float))
        y.extend(np.arange(100, 107, dtype=float))
        run()
        assert np.array_equal(recent_values(x), np.array([0., 1., 2., 3., 4.]))
        assert np.array_equal(recent_values(y), np.array([100., 101., 102., 103., 104., 105., 106.]))
        assert np.array_equal(
            recent_values(z), np.array(
                [[  0., 100.], [  1., 101.], [  2., 102.], [  3., 103.], [  4., 104.]]))

    class sliding_window_test(object):
        """
        Example of using a class to create an agent which has parameters,
        such as window_size, and can also have state. This example illustrates
        how iot(func, in_stream) is used with additional parameters that are
        encapsulated in a class.

        """
        def __init__(self, func, in_stream, out_stream, window_size, step_size):
            # The function applied to each sliding window.
            self.func = func
            # This agent has a single input stream and a single output stream.
            self.in_stream = in_stream
            self.out_stream = out_stream
            # This agent operates on sliding windows of the input stream.
            self.window_size = window_size
            self.step_size = step_size
            # Create the agent by using iot to wrap function f (which is
            # specified below).
            iot(func=self.f, in_stream=self.in_stream)

        def f(self, A):
            if len(A) < self.window_size:
                return 0
            else:
                # num_steps is the number of windows in the input A.
                num_steps = int(1+(len(A) - self.window_size)//self.step_size)
                self.output = np.zeros(num_steps, dtype=int)
                # Iterate through the windows into A.
                for i in range(num_steps):
                    window = A[i*self.step_size : i*self.step_size+self.window_size]
                    self.output[i] = self.func(window)
                self.out_stream.extend(self.output)
                # Return a pointer into the input array A.
                return num_steps*self.step_size

    def test_iot_class(self):

        x = StreamArray(name='x', dtype=int)
        y = StreamArray(name='y', dtype=int)
        # Create an agent that wraps np.sum
        sw = self.sliding_window_test(
            func=np.sum, in_stream=x, out_stream=y, window_size=5, step_size=2)
        x.extend(np.arange(10, dtype=int))
        run()
        assert np.array_equal(recent_values(y), np.array([10, 20, 30]))
        x.extend(np.arange(10, 20, dtype=int))
        run()
        assert np.array_equal(recent_values(y),
                              np.array([10, 20., 30, 40, 50, 60, 70, 80]))

if __name__ == '__main__':
    unittest.main()    
    
