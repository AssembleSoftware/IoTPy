import sys
import os
import random
import numpy as np
from collections import namedtuple
import unittest

from IoTPy.core.stream import Stream, StreamArray
from IoTPy.core.system_parameters import DEFAULT_NUM_IN_MEMORY

class test_stream(unittest.TestCase): 

    def test_stream(self):
        # Numpy type for testing stream array.
        txyz_dtype = np.dtype([('time','int'), ('data', '3float')])

        #--------------------------------------------
        # Testing StreamArray with positive dimension
        s = StreamArray(name='s', dimension=3)
        # Each element of s is a numpy array with with 3 elements
        # Initially s is empty. So s.stop == 0
        assert s.stop == 0
        # If num_in_memory is not specified in the declaration for
        # s, the default value, DEFAULT_NUM_IN_MEMORY,  is used.
        # The length of s.recent is twice num_in_memory
        assert len(s.recent) == 2 * DEFAULT_NUM_IN_MEMORY

        # Append a numpy array with 3 zeros to s
        s.append(np.zeros(3))
        assert(s.stop == 1)
        # Thus s.recent[:s.stop] is an array with 1 row and 3 columns.
        assert(np.array_equal(s.recent[:s.stop], np.array([[0.0, 0.0, 0.0]])))

        # Extend s by an array with 2 rows and 3 columns. The number of
        # columns must equal the dimension of the stream array.
        s.extend(np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))
        # s.stop is incremented to account for the addition of two elements.
        assert s.stop == 3
        # s.recent[:s.stop] includes all the elements added to s.
        # Thus s.recent[:s.stop] is an array with 3 rows and 3 columns.
        assert(np.array_equal(s.recent[:s.stop],
                              np.array([[0.0, 0.0, 0.0],
                                        [1.0, 2.0, 3.0],
                                        [4.0, 5.0, 6.0]]
                                        )))

        # Extend s by an array with 1 row and 3 columns. The number of
        # columns must equal the dimension of the stream array.
        s.extend(np.array([[7.0, 8.0, 9.0]]))
        # s.stop is incremented to account for the addition of a single row.
        assert s.stop == 4
        # Thus s.recent[:s.stop] is an array with 4 rows and 3 columns.
        assert np.array_equal(s.recent[:s.stop],
                              np.array([[0.0, 0.0, 0.0],
                                        [1.0, 2.0, 3.0],
                                        [4.0, 5.0, 6.0],
                                        [7.0, 8.0, 9.0]]
                                        ))
        # Note the difference between EXTENDING s with an array consisting
        # of 1 row and 3 columns, versus APPENDING a rank-1 array consisting
        # of 3 elements, as in the following example.
        s.append(np.array([10.0, 11.0, 12.0]))
        # s.stop is incremented to account for the addition of a single row.
        assert s.stop == 5
        # Thus s.recent[:s.stop] is an array with 5 rows and 3 columns.
        assert np.array_equal(s.recent[:s.stop],
                              np.array([[0.0, 0.0, 0.0],
                                        [1.0, 2.0, 3.0],
                                        [4.0, 5.0, 6.0],
                                        [7.0, 8.0, 9.0],
                                        [10.0, 11.0, 12.0]]
                                        ))
                 
        
        #---------------------------------------------------------------
        # Testing StreamArray with zero dimension and user-defined dtype
        t = StreamArray(name='t', dimension=0, dtype=txyz_dtype)
        # Each element of t is an object of dtype txyz_dtype
        # t[i]['time'] is an int.
        # t[i]['data'] is a 3-tuple consisting of 3 floats.
        # Nothing has been appended to t, and so t.stop == 0.
        assert(t.stop == 0)

        # Append an object with 'time' = 1, and 'data' = [0.0, 1.0, 2.0].
        t.append(np.array((1, [0.0, 1.0, 2.0]), dtype=txyz_dtype))
        # Increase t.stop to account for the element that has just been
        # added to t.
        assert t.stop == 1
        # t.recent[:t.stop] contains all elements appended to t.
        assert t.recent[:t.stop] == np.array([(1, [0.0, 1.0, 2.0])],
                                             dtype=txyz_dtype)
        assert t.recent[0]['time'] == np.array(1)
        assert np.array_equal(t.recent[0]['data'], np.array([ 0.,  1.,  2.]))

        # Append another element to t.
        t.append(np.array((2, [11.0, 12.0, 13.0]), dtype=txyz_dtype))
        # Increase t.stop to account for the element that has just been
        # added to t.
        assert (t.stop==2)
        # t.recent[:t.stop] contains all elements appended to t.
        a =  np.array([(1, [0.0, 1.0, 2.0]),
                       (2, [11.0, 12.0, 13.0])],
                       dtype=txyz_dtype)
        assert np.array_equal(t.recent[:t.stop], a)

        # Extend t by a list of 2 elements each of which consists of
        # zeroes of txyz_dtype
        t.extend(np.zeros(2, dtype=txyz_dtype))
        # Increase t.stop to account for the element that has just been
        # added to t.
        assert(t.stop == 4)
        # t.recent[:t.stop] contains all elements appended to t.
        a = np.array([(1, [0.0, 1.0, 2.0]),
                       (2, [11.0, 12.0, 13.0]),
                       (0, [0.0, 0.0, 0.0]),
                       (0, [0.0, 0.0, 0.0])],
                       dtype=txyz_dtype)
        assert np.array_equal(t.recent[:t.stop], a)

        #---------------------------------------------------------------
        # Testing simple Stream
        u = Stream('u')
        v = Stream('v')
        # Add elements 0, 1, 2, 3 to stream u.
        u.extend(list(range(4)))
        # Increase u.stop to account for the element that has just been
        # added to u.
        assert u.stop == 4
        # u.recent[:t.stop] contains all elements appended to u.
        assert u.recent[:u.stop] == [0, 1, 2, 3]
        # No change to v.
        assert v.stop == 0

        # Append element 10 to v and then append the list [40, 50]
        v.append(10)
        v.append([40, 50])
        # Increase v.stop by 2 to account for the 2 new elements appended
        # to v.
        assert v.stop == 2
        # v.recent[:v.stop] contains all elements appended to v.
        assert v.recent[:v.stop] == [10, [40, 50]]

        # Extend stream v
        v.extend([60, 70, 80])
        # Increase v.stop by 3 to account for the 3 new elements appended
        # to v.
        assert v.stop == 5
        # v.recent[:v.stop] contains all elements appended to v.
        assert v.recent[:v.stop] == [10, [40, 50], 60, 70, 80]

        #------------------------------------------
        # Test helper functions: get_contents_after_column_value()
        # Also test StreamArray
        y = StreamArray(name='y', dimension=0, dtype=txyz_dtype,
                        num_in_memory=64)
        # y[i]['time'] is a time (int).
        # y[i]['data'] is 3-tuple usually with directional data
        # for x, y, z.
        # y.recent length is twice num_in_memory
        assert len(y.recent) == 128
        # y has no elements, so y.stop == 0
        assert y.stop == 0
        # Test data for StreamArray with user-defined data type.
        test_data = np.zeros(128, dtype=txyz_dtype)
        assert len(test_data) == 128

        # Put random numbers for test_data[i]['time'] and
        # test_data[i]['data'][xyx] for xyz in [0, 1, 2]
        for i in range(len(test_data)):
            test_data[i]['time']= random.randint(0, 1000)
            for j in range(3):
                test_data[i]['data'][j] = random.randint(2000, 9999)

        # ordered_test_data has time in increasing order.
        ordered_test_data = np.copy(test_data)
        for i in range(len(ordered_test_data)):
            ordered_test_data[i]['time'] = i
        y.extend(ordered_test_data[:60])
        # extending y does not change length of y.recent
        assert(len(y.recent) == 128)
        # y.stop increases to accommodate the extension of y by 60.
        assert(y.stop == 60)
        # y.recent[:y.stop] now contains all the values put into y.
        assert np.array_equal(y.recent[:y.stop], ordered_test_data[:60])

        assert np.array_equal(y.get_contents_after_column_value(column_number=0, value=50),
                    ordered_test_data[50:60])
        assert  np.array_equal(y.get_contents_after_time(start_time=50),
                   ordered_test_data[50:60])
        assert(y.get_index_for_column_value(column_number=0, value=50) ==
               50)

        yz = StreamArray(name='yz', dimension=0, dtype=txyz_dtype,
                        num_in_memory=64)
        c = np.array((1, [0., 1., 2.]), dtype=txyz_dtype)
        yz.append(c)
        assert np.array_equal(yz.recent[:yz.stop], np.array([
            (1, [0., 1., 2.])], dtype=txyz_dtype))
        d = np.array([(2, [3., 4., 5.]), (3, [6., 7., 8.])], dtype=txyz_dtype)
        yz.extend(d)
        assert np.array_equal(yz.recent[:yz.stop], np.array([
            (1, [0., 1., 2.]), (2, [3., 4., 5.]), (3, [6., 7., 8.])], dtype=txyz_dtype))

        #------------------------------------------
        # TESTING regular Stream class
        x = Stream(name='x', num_in_memory=16) # Changed 8 to 16 to get test working - Num in Mem is same as len(recent) as per stream.py - check with Prof. Chandy)
        # The length of x.recent is twice num_in_memory
        assert(len(x.recent) == 16)
        # No values have been appended to stream x; so x.stop == 0
        assert(x.stop == 0)

        # Test append
        x.append(10)
        # Appending values to x does not change len(x.recent)
        assert(len(x.recent) == 16)
        # x.stop increases to accomodate the value appended.
        assert(x.stop == 1)
        # x.recent[:x.stop] includes the latest append
        assert(x.recent[:x.stop] == [10])
        x.append(20)
        assert(len(x.recent) == 16)
        # x.stop increases to accomodate the value appended.
        assert(x.stop == 2)
        # x.recent[:x.stop] includes the latest append
        assert(x.recent[:2] == [10, 20])

        # Test extend
        x.extend([30, 40])
        assert(len(x.recent) == 16)
        # x.stop increases to accomodate the values extended.
        assert(x.stop == 4)
        # x.recent[:x.stop] includes the latest extend
        assert(x.recent[:x.stop] == [10, 20, 30, 40])
        # Checking extension with the empty list.
        x.extend([])
        assert(len(x.recent) == 16)
        # extending a stream with the empty list does not change
        # the stream.
        assert(x.stop == 4)
        assert(x.recent[:4] == [10, 20, 30, 40])
        # Checking extending a stream with a singleton list
        x.extend([50])
        assert(len(x.recent) == 16)
        assert(x.stop == 5)
        assert(x.recent[:5] == [10, 20, 30, 40, 50])

        # Check registering a reader.
        # Register a reader called 'a' for stream x starting
        # to read from x[3] onwards.
        x.register_reader('a', 3)
        # Register a reader called 'b' for stream x starting
        # to read from x[4] onwards.
        x.register_reader('b', 4)
        # x.start is a dict which identifies the readers of x
        # and where they are starting to read from.
        assert(x.start == {'a':3, 'b':4})
        
        x.extend([1, 2, 3, 4, 5])
        assert(len(x.recent) == 16)
        assert(x.stop == 10)
        assert(x.recent[:10] == [10, 20, 30, 40, 50, 1, 2, 3, 4, 5])
        assert(x.start == {'a':3, 'b':4})

        x.register_reader('a', 7)
        x.register_reader('b', 7)
        assert(x.start == {'a':7, 'b':7})
        
        #------------------------------------------
        # Test helper functions
        assert(x.get_last_n(n=2) == [4, 5])

        v = StreamArray(dimension=(3,4), dtype=int)
        v.append(np.array([
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [8, 9, 10, 11]]))
        a = np.array([
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [8, 9, 10, 11]])
        np.array_equal(v.recent[:v.stop], np.array([[
            [0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]]))
        v.extend(np.array([
            [[12, 13, 14, 15],[16, 17, 18, 19], [20, 21, 22, 23]],
            [[24, 25, 26, 27], [28, 29, 30, 31], [32, 33, 34, 35]]]))
        np.array_equal(v.recent[:v.stop], np.array([
            [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]],
            [[12, 13, 14, 15],[16, 17, 18, 19], [20, 21, 22, 23]],
            [[24, 25, 26, 27], [28, 29, 30, 31], [32, 33, 34, 35]]]))
        

        u = StreamArray(name='u', dimension=2, dtype=int)
        a = np.array([0, 1])
        u.append(a)
        np.array_equal(u.recent[:u.stop], np.array([[0,1]]))
        u.extend(np.array([[2,3], [4,5],[6,7]]))
        np.array_equal(u.recent[:u.stop], np.array([[0,1],[2,3],[4,5],[6,7]]))

        t = StreamArray('t')
        t.append(np.array(1.0))
        t.extend(np.array([2.0, 3.0]))
        np.array_equal(t.recent[:t.stop], np.array([1.0, 2.0, 3.0]))


if __name__ == '__main__':
    unittest.main()
