""" 
This module tests list_agent.py
"""

import numpy as np
import unittest
# agent, stream are in ../core
from IoTPy.core.agent import Agent
from IoTPy.core.stream import Stream, StreamArray, run
from IoTPy.core.stream import _no_value, _multivalue
# check_agent_parameter_types is in ../helper_functions
from IoTPy.agent_types.check_agent_parameter_types import *
# recent_values  are in ../helper_functions
from IoTPy.helper_functions.recent_values import recent_values
#from run import run
# sink, multi, op, split, merge are in ../agent_types
from IoTPy.agent_types.sink import sink_list, sink_list_f
from IoTPy.agent_types.multi import *
from IoTPy.agent_types.op import *
from IoTPy.agent_types.split import split_list, split_list_f
from IoTPy.agent_types.merge import merge_list, merge_list_f

#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#     LIST AGENT TESTS
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------

class test_list(unittest.TestCase):

    def test_list(self):
        scheduler = Stream.scheduler

        n = Stream('n')
        o = Stream('o')
        p = Stream('p')
        q = Stream('q')
        r = Stream('r')
        s = Stream('s')
        t = Stream('t')
        u = Stream('u')
        v = Stream('v')
        w = Stream('w')
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')


        #-------------------------------------------------------------------
        # Test simple map
        def simple(lst):
            return [2*v for v in lst]
        a = map_list(func=simple, in_stream=x, out_stream=y, name='a')
        yy = map_list_f(simple, x)
        #-------------------------------------------------------------------


        #-------------------------------------------------------------------
        # Test map with state
        # Function that operates on an element and state and returns an
        # element and state.
        def f(input_list, state):
            output_list = [[]]*len(input_list)
            for i in range(len(input_list)):
                output_list[i] = input_list[i]+state
                state += 2
            return output_list, state
            
        b = map_list(func=f, in_stream=x, out_stream=z, state=0, name='b')
        zz = map_list_f(f, x, 0)
        #-------------------------------------------------------------------


        #-------------------------------------------------------------------
        # Test map with call streams
        c = map_list(func=f, in_stream=x, out_stream=v, state=10,
                              call_streams=[w], name='c')
        #-------------------------------------------------------------------


        #-------------------------------------------------------------------
        # Test sink with state
        def sink_with_state(input_list, output_list):
            # sink has no output stream.
            # This function only returns the next state.
            return output_list.extend(input_list)

        out_list = []
        # In this simple example, out_list will be the same as the input
        # stream.
        sink_agent = sink_list(
            func=sink_with_state, in_stream=x,
            name='sink_agent', state=out_list)
        out_list_stream = []
        # Function version of the previous agent example
        sink_list_f(sink_with_state, x, out_list_stream)
        #-------------------------------------------------------------------

        #-------------------------------------------------------------------
        # Test merge
        # Function that operates on a list of lists
        def g(list_of_lists):
            return [sum(snapshot) for snapshot in zip(*list_of_lists)]
        d = merge_list(func=g, in_streams=[x,u], out_stream=s, name='d')
        ss = merge_list_f(g, [x,u])
        #-------------------------------------------------------------------


        #-------------------------------------------------------------------
        # Test split
        def h(input_list):
            return [[element+1 for element in input_list],
                    [element*2 for element in input_list]]
        e = split_list(func=h, in_stream=x, out_streams=[r, t], name='e')
        rr, tt = split_list_f(h, x, num_out_streams=2)
        #-------------------------------------------------------------------
        
        #-------------------------------------------------------------------
        # Test split with state
        def h_state(input_list, state):
            length = len(input_list)
            output_list_0 = [[]]*length
            output_list_1 = [[]]*length
            for i in range(length):
                output_list_0[i] = input_list[i]+state
                output_list_1[i] = input_list[i]*state
                state += 1
            return ([output_list_0, output_list_1], state)

        split_list(
            func=h_state, in_stream=x, out_streams=[p, q], state=0)
        pp, qq = split_list_f(h_state, x, num_out_streams=2, state=0)
        #-------------------------------------------------------------------


        #-------------------------------------------------------------------
        # Test many
        def f_many(list_of_lists):
            snapshots =list(zip(*list_of_lists))
            return [[max(snapshot) for snapshot in snapshots],
                    [min(snapshot) for snapshot in snapshots]]
        multi_agent = multi_list(
            func=f_many, in_streams=[x, u], out_streams=[n, o],
            name='multi_agent')
        nn, oo = multi_list_f(func=f_many, in_streams=[x, u], num_out_streams=2)
        #-------------------------------------------------------------------

        #-------------------------------------------------------------------
        #-------------------------------------------------------------------
        x.extend(list(range(5)))
        run()
        assert recent_values(x) == list(range(5))
        assert recent_values(y) == [0, 2, 4, 6, 8]
        assert recent_values(z) == [0, 3, 6, 9, 12]
        assert recent_values(v) == []
        assert out_list == list(range(5))
        assert out_list == out_list_stream
        assert recent_values(s) == []
        assert recent_values(r) == [1, 2, 3, 4, 5]
        assert recent_values(t) == [0, 2, 4, 6, 8]
        assert recent_values(p) == [0, 2, 4, 6, 8]
        assert recent_values(q) == [0, 1, 4, 9, 16]
        assert recent_values(n) == []
        assert recent_values(o) == []
        assert recent_values(y) == recent_values(yy)
        assert recent_values(z) == recent_values(zz)
        assert recent_values(s) == recent_values(ss)
        assert recent_values(r) == recent_values(rr)
        assert recent_values(t) == recent_values(tt)
        assert recent_values(p) == recent_values(pp)
        assert recent_values(q) == recent_values(qq)
        assert recent_values(n) == recent_values(nn)
        assert recent_values(o) == recent_values(oo)


                    
        #-------------------------------------------------------------------    

        
        #-------------------------------------------------------------------
        w.append(0)
        run()

        assert recent_values(x) == list(range(5))
        assert recent_values(y) == [0, 2, 4, 6, 8]
        assert recent_values(z) == [0, 3, 6, 9, 12]
        assert recent_values(v) == [10, 13, 16, 19, 22]
        assert out_list == list(range(5))
        assert recent_values(s) == []
        assert recent_values(r) == [1, 2, 3, 4, 5]
        assert recent_values(t) == [0, 2, 4, 6, 8]
        assert recent_values(p) == [0, 2, 4, 6, 8]
        assert recent_values(q) == [0, 1, 4, 9, 16]
        assert recent_values(n) == []
        assert recent_values(o) == []
        assert recent_values(y) == recent_values(yy)
        assert recent_values(z) == recent_values(zz)
        assert recent_values(s) == recent_values(ss)
        assert recent_values(r) == recent_values(rr)
        assert recent_values(t) == recent_values(tt)
        assert recent_values(p) == recent_values(pp)
        assert recent_values(q) == recent_values(qq)
        assert recent_values(n) == recent_values(nn)
        assert recent_values(o) == recent_values(oo)
        #-------------------------------------------------------------------

        
        #-------------------------------------------------------------------
        u.extend([10, 15, 18])
        run()
        assert recent_values(s) == [10, 16, 20]
        assert recent_values(n) == [10, 15, 18]
        assert recent_values(o) == [0, 1, 2]

        u.append(37)
        run()
        assert recent_values(s) == [10, 16, 20, 40]
        assert recent_values(n) == [10, 15, 18, 37]
        assert recent_values(o) == [0, 1, 2, 3]

        u.extend([96, 95])
        run()
        assert recent_values(x) == list(range(5))
        assert recent_values(y) == [0, 2, 4, 6, 8]
        assert recent_values(z) == [0, 3, 6, 9, 12]
        assert recent_values(v) == [10, 13, 16, 19, 22]
        assert out_list == list(range(5))
        assert recent_values(s) == [10, 16, 20, 40, 100]
        assert recent_values(r) == [1, 2, 3, 4, 5]
        assert recent_values(t) == [0, 2, 4, 6, 8]
        assert recent_values(p) == [0, 2, 4, 6, 8]
        assert recent_values(q) == [0, 1, 4, 9, 16]
        assert recent_values(n) == [10, 15, 18, 37, 96]
        assert recent_values(o) == [0, 1, 2, 3, 4]
        
        assert recent_values(y) == recent_values(yy)
        assert recent_values(z) == recent_values(zz)
        assert recent_values(s) == recent_values(ss)
        assert recent_values(r) == recent_values(rr)
        assert recent_values(t) == recent_values(tt)
        assert recent_values(p) == recent_values(pp)
        assert recent_values(q) == recent_values(qq)
        assert recent_values(n) == recent_values(nn)
        assert recent_values(o) == recent_values(oo)


        #------------------------------------------------------------------
        #------------------------------------------------------------------
        # Test NumPy arrays: StreamArray
        #------------------------------------------------------------------
        #------------------------------------------------------------------
        # Test list map on StreamArray (dimension is 0).  
        a_stream_array = StreamArray(name='a_stream_array')
        b_stream_array = StreamArray(name='b_stream_array')
        def f_np(input_array):
            return input_array+1
        a_np_agent = map_list(func=f_np, in_stream=a_stream_array, out_stream=b_stream_array,
                                    name='a_np_agent')
        bb_stream_array = map_array_f(f_np, a_stream_array)

        run()
        assert np.array_equal(recent_values(b_stream_array), np.array([], dtype=np.float64))
        assert np.array_equal(recent_values(b_stream_array),recent_values(bb_stream_array))

        a_stream_array.extend(np.arange(5.0))
        run()
        assert np.array_equal(recent_values(b_stream_array), np.arange(5.0)+1)
        assert np.array_equal(recent_values(b_stream_array),recent_values(bb_stream_array))

        
        a_stream_array.extend(np.arange(5.0, 10.0, 1.0))
        run()
        assert np.array_equal(recent_values(b_stream_array), np.arange(10.0)+1)
        assert np.array_equal(recent_values(b_stream_array),recent_values(bb_stream_array))

        # Test list map with state on StreamArray (dimension is 0)
        c_stream_array = StreamArray(name='c_stream_array')
        d_stream_array = StreamArray(name='d_stream_array')
        def f_np_state(input_array, state):
            return np.cumsum(input_array)+state, np.sum(input_array)
        b_np_agent = map_list(func=f_np_state, in_stream=c_stream_array,
                                    out_stream=d_stream_array, state = 0.0,
                                    name='b_np_agent')
        dd_stream_array = map_array_f(f_np_state, c_stream_array, state=0.0)
        run()
        assert np.array_equal(recent_values(d_stream_array), np.array([], dtype=np.float64))
        assert np.array_equal(recent_values(d_stream_array),recent_values(dd_stream_array))

        c_stream_array.extend(np.arange(5.0))
        run()
        assert np.array_equal(
            d_stream_array.recent[:d_stream_array.stop], np.cumsum(np.arange(5.0)))
        assert np.array_equal(recent_values(d_stream_array),recent_values(dd_stream_array))

        c_stream_array.extend(np.arange(5.0, 10.0, 1.0))
        run()
        assert np.array_equal(
            d_stream_array.recent[:d_stream_array.stop], np.cumsum(np.arange(10.0)))
        assert np.array_equal(recent_values(d_stream_array),recent_values(dd_stream_array))

        # Test list map with positive integer dimension on StreamArray
        e_stream_array = StreamArray(name='e_stream_array', dimension=3)
        f_stream_array = StreamArray(name='f_stream_array', dimension=2)
        def f_np_dimension(input_array):
            output_array = np.zeros([len(input_array), 2])
            output_array[:,0] = input_array[:,0]+input_array[:,1]
            output_array[:,1] = input_array[:,2]
            return output_array        

        c_np_agent = map_list(func=f_np_dimension, in_stream=e_stream_array,
                                    out_stream=f_stream_array, name='c_np_agent')
        e_stream_array.extend(np.array([[1.0, 2.0, 3.0]]))
        run()
        assert np.array_equal(f_stream_array.recent[:f_stream_array.stop], np.array([[3.0, 3.0]]))

        e_stream_array.extend(np.array([[4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]))
        run()
        assert np.array_equal(f_stream_array.recent[:f_stream_array.stop],
                              np.array([[3.0, 3.0], [9.0, 6.0], [15.0, 9.0]]))

        # Test list map with a dimension which is a tuple of integers.
        g_stream_array = StreamArray(name='g_stream_array', dimension=(2,2))
        h_stream_array = StreamArray(name='h_stream_array', dimension=(2,2))
        def f_np_tuple_dimension(input_array):
            return input_array*2    

        d_np_agent = map_list(func=f_np_tuple_dimension, in_stream=g_stream_array,
                                    out_stream=h_stream_array, name='d_np_agent')
        a_array = np.array([[[1.0, 2.0],[3.0, 4.0]],
                                        [[5.0, 6.0],[7.0, 8.0]]])
        g_stream_array.extend(a_array)
        run()
        assert np.array_equal(h_stream_array.recent[:h_stream_array.stop],
                              a_array*2)

        b_array = np.array([[[9.0, 10.0], [11.0, 12.0]]])
        g_stream_array.extend(b_array)
        run()
        assert np.array_equal(h_stream_array.recent[:h_stream_array.stop],
                              np.vstack((a_array, b_array))*2)

        # Test list map with a datatype and dimension of 0.
        dt_0 = np.dtype([('time', int), ('value', (float, 3))])
        dt_1 = np.dtype([('time', int), ('value', float)])
        i_stream_array = StreamArray(name='i_stream_array', dtype=dt_0)
        j_stream_array = StreamArray(name='j_stream_array', dtype=dt_1)
        def f_datatype(input_array):
            output_array = np.zeros(len(input_array), dtype=dt_1)
            output_array['time'] = input_array['time']
            output_array['value'] = np.sum(input_array['value'], axis=1)
            return output_array
                
        e_np_agent = map_list(func=f_datatype, in_stream=i_stream_array,
                                    out_stream=j_stream_array, name='e_np_agent')
        c_array = np.array([(1, [2.0, 3.0, 4.0])], dtype=dt_0)
        assert j_stream_array.stop == 0

        i_stream_array.extend(c_array)
        run()
        assert np.array_equal(j_stream_array.recent[:j_stream_array.stop],
                              f_datatype(c_array))

        d_array = np.array([(10, [6.0, 7.0, 8.0]), (20, [10.0, 11.0, 12.0])], dtype=dt_0)
        i_stream_array.extend(d_array)
        run()
        assert np.array_equal(j_stream_array.recent[:j_stream_array.stop],
                              f_datatype(np.hstack((c_array, d_array))))


        # Test list map with a datatype and positive integer dimension.
        k_stream_array = StreamArray(name='k_stream_array', dtype=dt_0, dimension=2)
        l_stream_array = StreamArray(name='l_stream_array', dtype=dt_1)
        def f_datatype_int_dimension(input_array):
            m = len(input_array)
            output_array = np.zeros(m, dtype=dt_1)
            for i in range(m):
                output_array[i]['time'] = np.max(input_array[i]['time'])
                output_array[i]['value'] = np.sum(input_array[i]['value'])
            return output_array
                
        f_np_agent = map_list(func=f_datatype_int_dimension, in_stream=k_stream_array,
                                    out_stream=l_stream_array, name='f_np_agent')
        e_array = np.array([[(1, [2.0, 3.0, 4.0]), (2, [5.0, 6.0, 7.0])]], dtype=dt_0)
        assert l_stream_array.stop == 0

        k_stream_array.extend(e_array)
        run()
        assert np.array_equal(l_stream_array.recent[:l_stream_array.stop],
                              f_datatype_int_dimension(e_array))

        f_array = np.array([[(3, [8.0, 9.0, 10.0]), (4, [11.0, 12.0, 13.0])],
                            [(5, [-1.0, 0.0, 1.0]), (6, [-2.0, 2.0, -2.0])]],
                           dtype=dt_0)
        k_stream_array.extend(f_array)
        run()
        assert np.array_equal(l_stream_array.recent[:l_stream_array.stop],
                              f_datatype_int_dimension(np.vstack((e_array, f_array))))


        # Test list map with a datatype and a dimension which is a tuple
        m_stream_array = StreamArray(name='m_stream_array', dtype=dt_0, dimension=(2,2))
        n_stream_array = StreamArray(name='n_stream_array', dtype=dt_1)
        g_np_agent = map_list(func=f_datatype_int_dimension, in_stream=m_stream_array,
                                    out_stream=n_stream_array, name='g_np_agent')
        assert n_stream_array.stop == 0

        g_array = np.array([
            # zeroth 2x2 array
            [[(1, [2.0, 3.0, 4.0]), (2, [5.0, 6.0, 7.0])],
             [(3, [8.0, 9.0, 10.0]), (4, [11.0, 12.0, 13.0])]],
            # first 2x2 array
            [[(5, [12.0, 13.0, 14.0]), (6, [15.0, 16.0, 17.0])],
             [(7, [18.0, 19.0, 20.0]), (8, [21.0, 22.0, 23.0])]]
             ], dtype=dt_0)
        m_stream_array.extend(g_array)
        run()
        assert np.array_equal(n_stream_array.recent[:n_stream_array.stop],
                              f_datatype_int_dimension(g_array))

        h_array = np.array([
            [[(9, [0.0, 1.0, -1.0]), (10, [2.0, 2.0, -4.0])],
             [(11, [80.0, -71.0, -9.0]), (15, [0.0, 0.0, 0.0])]]
             ], dtype=dt_0)
        m_stream_array.extend(h_array)
        run()
        assert np.array_equal(n_stream_array.recent[:n_stream_array.stop],
                              f_datatype_int_dimension(np.vstack((g_array, h_array))))

        # Test list merge with StreamArray and no dimension and no data type
        a_in_0 = StreamArray(name='a_in_0')
        a_in_1 = StreamArray(name='a_in_1')
        a_out = StreamArray(name='a_out')
        def a_merge(list_of_lists):
            array_0, array_1 = list_of_lists
            return array_0 + array_1
        a_s_agent = merge_list(func=a_merge, in_streams=[a_in_0, a_in_1],
                                    out_stream=a_out, name='a_s_agent')
        
        assert a_out.stop == 0

        #a_in_0.extend(np.array([1.0, 2.0, 3.0]))
        a_in_0.extend(np.array([1.0, 2.0, 3.0]))
        run()
        assert a_out.stop == 0

        a_in_0.extend(np.array([4.0, 5.0, 6.0]))
        run()
        assert a_out.stop == 0

        a_in_1.extend(np.array([10.0, 20.0]))
        run()
        assert np.array_equal(a_out.recent[:a_out.stop],
                              np.array([11.0, 22.0]))

        a_in_1.extend(np.array([30.0, 40.0]))
        run()
        assert np.array_equal(a_out.recent[:a_out.stop],
                              np.array([11.0, 22.0, 33.0, 44.0]))

        
        # Test list merge with StreamArray and no dimension and data type
        a_in_dt_0 = StreamArray(name='a_in_dt_0', dtype=dt_0)
        a_in_dt_1 = StreamArray(name='a_in_dt_1', dtype=dt_0)
        a_out_dt = StreamArray(name='out', dtype=dt_0)
        def a_merge_dtype(list_of_arrays):
            input_array_0, input_array_1 = list_of_arrays
            output_array = np.zeros(len(input_array_0), dtype=dt_0)
            output_array['time'] = \
              np.max((input_array_0['time'], input_array_1['time']), axis=0)
            output_array['value'] = input_array_0['value'] + input_array_1['value']
            return output_array
        a_s_dt_agent = merge_list(func=a_merge_dtype, in_streams=[a_in_dt_0, a_in_dt_1],
                                    out_stream=a_out_dt, name='a_s_dt_agent')
        a_in_dt_0.extend(np.array([(1, [1.0, 2.0, 3.0])], dtype=dt_0))
        run()
        assert a_out_dt.stop == 0

        a_in_dt_1.extend(np.array([(2, [10.0, 20.0, 30.0])], dtype=dt_0))
        run()
        assert np.array_equal(a_out_dt.recent[:a_out_dt.stop],
                              np.array([(2, [11.0, 22.0, 33.0])], dtype=dt_0))

        a_in_dt_0.extend(np.array([(5, [21.0, 23.0, 32.0]),
                                   (9, [27.0, 29.0, 31.0])], dtype=dt_0))
        run()
        assert np.array_equal(a_out_dt.recent[:a_out_dt.stop],
                              np.array([(2, [11.0, 22.0, 33.0])], dtype=dt_0))

        a_in_dt_1.extend(np.array([(6, [19.0, 17.0, 8.0]),
                                   (8, [13.0, 11.0, 9.0]),
                                   (10, [3.0, 1.0, 5.0])], dtype=dt_0))
        run()
        assert np.array_equal(a_out_dt.recent[:a_out_dt.stop],
                              np.array([(2, [11.0, 22.0, 33.0]),
                                        (6, [40.0, 40.0, 40.0]),
                                        (9, [40.0, 40.0, 40.0])], dtype=dt_0))


        # Test list split with StreamArray and positive integer dimension and no data type
        dim = 2
        b_in = StreamArray(name='b_in', dimension=dim)
        b_out_0 = StreamArray(name='b_out_0', dimension=dim)
        b_out_1 = StreamArray(name='b_out_1')
        def b_split(array_of_arrays):
            length = len(array_of_arrays)
            output_array_0 = np.zeros((length, dim,))
            output_array_1 = np.zeros(length)
            for i in range(length):
                input_array = array_of_arrays[i]
                output_array_0[i] = np.array([[np.max(input_array), np.min(input_array)]])
                output_array_1[i] = np.array([np.sum(input_array)])
            return output_array_0, output_array_1
        b_split_agent = split_list(func=b_split, in_stream=b_in,
                                    out_streams=[b_out_0, b_out_1], name='b_split_agent')
        
        b_array_0 = np.array([[1.0, 9.0]])
        b_in.extend(b_array_0)
        run()
        assert np.array_equal(b_out_0.recent[:b_out_0.stop],
                              np.array([[9.0, 1.0]]))
        assert np.array_equal(b_out_1.recent[:b_out_1.stop],
                              np.array([10.0]))

        b_array_1 = np.array([[98.0, 2.0]])
        b_in.extend(b_array_1)
        run()
        assert np.array_equal(b_out_0.recent[:b_out_0.stop],
                              np.array([[9.0, 1.0], [98.0, 2.0]]))
        assert np.array_equal(b_out_1.recent[:b_out_1.stop],
                              np.array([10.0, 100.0]))

        b_array_3 = np.array([[10.0, 20.0], [3.0, 37.0], [55.0, 5.0]])
        b_in.extend(b_array_3)
        run()
        assert np.array_equal(b_out_0.recent[:b_out_0.stop],
                              np.array([[9.0, 1.0], [98.0, 2.0],
                                        [20.0, 10.0], [37.0, 3.0],
                                        [55.0, 5.0]]))
        assert np.array_equal(b_out_1.recent[:b_out_1.stop],
                              np.array([10.0, 100.0, 30.0, 40.0, 60.0]))


        # Test list many with StreamArray and no dimension and no data type
        c_in_0 = StreamArray(name='c_in_0')
        c_in_1 = StreamArray(name='c_in_1')
        c_out_0 = StreamArray(name='c_out_0')
        c_out_1 = StreamArray(name='c_out_1')
        def c_many(list_of_arrays):
            length = len(list_of_arrays)
            input_array_0, input_array_1 = list_of_arrays
            output_array_0 = np.zeros(length)
            output_array_1 = np.zeros(length)
            output_array_0 = input_array_0 + input_array_1
            output_array_1 = input_array_0 - input_array_1
            return [output_array_0, output_array_1]
        
        c_multi_agent = multi_list(func=c_many, in_streams=[c_in_0, c_in_1],
                                       out_streams=[c_out_0, c_out_1],
                                       name='c_multi_agent')
        c_array_0_0 = np.arange(3.0)*3
        c_array_1_0 = np.arange(3.0)
        c_in_0.extend(c_array_0_0)
        run()
        c_in_1.extend(c_array_1_0)
        run()
        assert np.array_equal(c_out_0.recent[:c_out_0.stop],
                       np.array([0.0, 4.0, 8.0]))
        assert np.array_equal(c_out_1.recent[:c_out_1.stop],
                       np.array([0.0, 2.0, 4.0]))

        c_array_0_1 = np.array([100.0])
        c_array_1_1 = np.array([4.0, 5.0, 6.0])
        c_in_0.extend(c_array_0_1)
        c_in_1.extend(c_array_1_1)
        run()
        assert np.array_equal(c_out_0.recent[:c_out_0.stop],
                       np.array([0.0, 4.0, 8.0, 104.0]))
        assert np.array_equal(c_out_1.recent[:c_out_1.stop],
                       np.array([0.0, 2.0, 4.0, 96.0]))
        


        ## # Test list many with StreamArray and no dimension and no data type
        ## z_in_0 = StreamArray(name='z_in_0')
        ## z_in_1 = StreamArray(name='z_in_1')
        ## z_out_0 = StreamArray(name='z_out_0')
        ## z_out_1 = StreamArray(name='z_out_1')
        ## def execute_list_of_np_func(v, list_of_np_func):
        ##     length = len(list_of_arrays)
        ##     input_array_0, input_array_1 = list_of_arrays
        ##     output_array_0 = np.zeros(length)
        ##     output_array_1 = np.zeros(length)
        ##     output_array_0 = input_array_0 + input_array_1
        ##     output_array_1 = input_array_0 - input_array_1
        ##     return [output_array_0, output_array_1]

        
        # Test list many with StreamArray and positive integer dimension and no data type
        dim = 2
        d_in_0 = StreamArray(name='d_in_0', dimension=dim)
        d_in_1 = StreamArray(name='d_in_1', dimension=dim)
        d_out_0 = StreamArray(name='d_out_0', dimension=dim)
        d_out_1 = StreamArray(name='d_out_1')
        def d_many(list_of_arrays):
            length = len(list_of_arrays)
            input_array_0, input_array_1 = list_of_arrays
            output_array_0 = input_array_0 + input_array_1
            output_array_1 = np.array([np.sum(input_array_0+input_array_1)])
            return output_array_0, output_array_1

        d_multi_agent = multi_list(func=d_many, in_streams=[d_in_0, d_in_1],
                                       out_streams=[d_out_0, d_out_1],
                                       name='d_multi_agent')

        d_array_0_0 = np.array([[1.0, 2.0]])
        d_array_1_0 = np.array([[0.0, 10.0]])
        d_in_0.extend(d_array_0_0)
        run()
        d_in_1.extend(d_array_1_0)
        run()
        assert np.array_equal(d_out_0.recent[:d_out_0.stop],
                       np.array([[1.0, 12.0]]))
        assert np.array_equal(d_out_1.recent[:d_out_1.stop],
                       np.array([13.0]))


        d_array_0_1 = np.array([[4.0, 8.0]])
        d_array_1_1 = np.array([[2.0, 4.0]])
        d_in_0.extend(d_array_0_1)
        d_in_1.extend(d_array_1_1)
        run()
        assert np.array_equal(d_out_0.recent[:d_out_0.stop],
                       np.array([[1.0, 12.0], [6.0, 12.0]]))
        assert np.array_equal(d_out_1.recent[:d_out_1.stop],
                       np.array([13.0, 18.0]))

        d_array_0_2 = np.array([[20.0, 30.0], [40.0, 50.0]])
        d_array_1_2 = np.array([[-10.0, -20.0]])
        d_in_0.extend(d_array_0_2)
        d_in_1.extend(d_array_1_2)
        run()
        assert np.array_equal(d_out_0.recent[:d_out_0.stop],
                       np.array([[1.0, 12.0], [6.0, 12.0], [10.0, 10.0]]))
        assert np.array_equal(d_out_1.recent[:d_out_1.stop],
                       np.array([13.0, 18.0, 20.0]))


        # Test list many with StreamArray and tuple dimension and no data type
        dim = (2,2)
        e_in_0 = StreamArray(name='e_in_0', dimension=dim)
        e_in_1 = StreamArray(name='e_in_1', dimension=dim)
        e_out_0 = StreamArray(name='e_out_0', dimension=dim)
        e_out_1 = StreamArray(name='e_out_1')

        def e_many(list_of_arrays):
            input_array_0, input_array_1 = list_of_arrays
            output_array_0 = input_array_0 + input_array_1
            output_array_1 = \
              np.array([np.sum(input_array_0[i]+ input_array_1[i])
                        for i in range(len(input_array_0))])
            return output_array_0, output_array_1

        e_multi_agent = multi_list(func=e_many, in_streams=[e_in_0, e_in_1],
                                       out_streams=[e_out_0, e_out_1],
                                       name='e_multi_agent')


        e_array_0_0 = np.array([[[10.0, 20.0], [30.0, 40.0]]])
        e_in_0.extend(e_array_0_0)
        e_array_1_0 = np.array([[[1.0, 2.0], [3.0, 4.0]]])
        e_in_1.extend(e_array_1_0)
        run()
        assert np.array_equal(e_out_0.recent[:e_out_0.stop],
                       np.array([[[11.0, 22.0], [33.0, 44.0]]]))
        assert np.array_equal(e_out_1.recent[:e_out_1.stop],
                       np.array([110.0]))

        
        e_array_0_1 = np.array([[[11.0, 13.0], [17.0, 19.0]],
                               [[2.0, 4.0], [6.0, 8.0]]])
        e_in_0.extend(e_array_0_1)
        run()
        assert np.array_equal(e_out_0.recent[:e_out_0.stop],
                       np.array([[[11.0, 22.0], [33.0, 44.0]]]))
        assert np.array_equal(e_out_1.recent[:e_out_1.stop],
                       np.array([110.0]))

        
        e_array_1_1 = np.array([[[1.0, 2.0], [3.0, 4.0]],
                                [[5.0, 6.0], [7.0, 8.0]]])
        e_in_1.extend(e_array_1_1)
        run()
        assert np.array_equal(e_out_0.recent[:e_out_0.stop],
                       np.array([[[11.0, 22.0], [33.0, 44.0]],
                                 [[12.0, 15.0], [20.0, 23.0]],
                                 [[7.0, 10.0], [13.0, 16.0]]]))
        assert np.array_equal(e_out_1.recent[:e_out_1.stop],
                       np.array([110.0, 70.0, 46.0]))

        
        e_array_1_2 = np.array([[[11.0, 12.0], [13.0, 14.0]],
                                [[15.0, 16.0], [17.0, 18.0]]])
        e_in_1.extend(e_array_1_2)
        run()
        e_array_0_2 = np.array([[[-10.0, -11.0], [12.0, 16.0]],
                                [[-14.0, -15.0], [-16.0, -17.0]]])
        e_in_0.extend(e_array_0_2)
        run()
        assert np.array_equal(e_out_0.recent[:e_out_0.stop],
                       np.array([[[11.0, 22.0], [33.0, 44.0]],
                                 [[12.0, 15.0], [20.0, 23.0]],
                                 [[7.0, 10.0], [13.0, 16.0]],
                                 [[1.0, 1.0], [25.0, 30.0]],
                                 [[1.0, 1.0], [1.0, 1.0]]]))
        assert np.array_equal(e_out_1.recent[:e_out_1.stop],
                       np.array([110.0, 70.0, 46.0, 57.0, 4.0]))



        #------------------------------------------------------------------
        #------------------------------------------------------------------
        # Test args and kwargs
        #------------------------------------------------------------------
        #------------------------------------------------------------------
        # Test map
        
        def map_args(lst, multiplicand):
            return [multiplicand*element for element in lst]

        in_stream_map_args_stream = Stream('in_stream_map_args_stream')
        out_stream_map_args_stream = Stream('out_stream_map_args_stream')
        out_stream_map_kwargs_stream = Stream('out_stream_map_kwargs_stream')


        map_args_agent = map_list(
            map_args, in_stream_map_args_stream, out_stream_map_args_stream,
            None, None, 'map_args_agent', 2)

        map_kwargs_agent = map_list(func=map_args,
                                        in_stream=in_stream_map_args_stream,
                                        out_stream=out_stream_map_kwargs_stream,
                                        name='map_args_agent',
                                        multiplicand=2)
        run()
        assert out_stream_map_args_stream.recent[:out_stream_map_args_stream.stop] == \
          []
        assert out_stream_map_kwargs_stream.recent[:out_stream_map_kwargs_stream.stop] == \
          []

        in_stream_map_args_stream.extend(list(range(5)))
        run()
        assert out_stream_map_args_stream.recent[:out_stream_map_args_stream.stop] == \
          [0, 2, 4, 6, 8]
        assert out_stream_map_kwargs_stream.recent[:out_stream_map_kwargs_stream.stop] == \
          [0, 2, 4, 6, 8]

        in_stream_map_args_stream.append(5)
        run()
        assert out_stream_map_args_stream.recent[:out_stream_map_args_stream.stop] == \
          [0, 2, 4, 6, 8, 10]
        assert out_stream_map_kwargs_stream.recent[:out_stream_map_kwargs_stream.stop] == \
          [0, 2, 4, 6, 8, 10]


        # Test list map on StreamArray (dimension is 0).  
        a_stream_array_args = StreamArray(name='a_stream_array_args')
        b_stream_array_args = StreamArray(name='b_stream_array_args')
        c_stream_array_args_kwargs = StreamArray(name='c_stream_array_args_kwargs')

        def f_np_args(input_array_args, addend):
            return input_array_args+addend

        def f_np_args_kwargs(input_array_args_kwargs, multiplicand, addend):
            return input_array_args_kwargs*multiplicand + addend

        a_np_agent_args = map_list(
            f_np_args, a_stream_array_args, b_stream_array_args,
            None, None, 'a_np_agent_args',
            1)
        
        a_np_agent_args_kwargs = map_list(
            f_np_args_kwargs, a_stream_array_args, c_stream_array_args_kwargs,
            None, None, 'a_np_agent_args_kwargs',
            2, addend=10)
        run()
        assert np.array_equal(
            b_stream_array_args.recent[:b_stream_array_args.stop],
            np.array([]))
        assert np.array_equal(
            c_stream_array_args_kwargs.recent[:c_stream_array_args_kwargs.stop],
            np.array([]))
            
        a_stream_array_args.extend(np.arange(5.0))
        run()
        assert np.array_equal(b_stream_array_args.recent[:b_stream_array_args.stop],
                              np.arange(5.0)+1)
        assert np.array_equal(c_stream_array_args_kwargs.recent[:c_stream_array_args_kwargs.stop],
                              np.arange(5.0)*2 + 10)

        a_stream_array_args.extend(np.arange(5.0, 10.0, 1.0))
        run()
        assert np.array_equal(b_stream_array_args.recent[:b_stream_array_args.stop],
                              np.arange(10.0)+1)
        assert np.array_equal(c_stream_array_args_kwargs.recent[:c_stream_array_args_kwargs.stop],
                              np.arange(10.0)*2 + 10)


        print ('TEST OF OP (LISTS) IS SUCCESSFUL')

if __name__ == '__main__':
    unittest.main()
    
    
    
    
    

