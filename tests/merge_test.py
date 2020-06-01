"""
This module consists of functions that merge multiple input streams
into a single output stream.

"""

import math
import unittest

from IoTPy.core.agent import Agent
from IoTPy.core.stream import Stream, StreamArray
from IoTPy.core.stream import _no_value, _multivalue
from IoTPy.agent_types.check_agent_parameter_types import *
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.agent_types.merge import *
from IoTPy.agent_types.multi import *
from IoTPy.agent_types.op import timed_window, timed_window_f
from IoTPy.agent_types.merge import merge_list, zip_map_list

def run(): Stream.scheduler.step()
#--------------------------------------------------------
#--------------------------------------------------------

class test_merge_agents(unittest.TestCase):

    def test_some_merge_agents(self):
        import numpy as np
        scheduler = Stream.scheduler

        #----------------------------------------------------
        # Declare streams
        s = Stream('s')
        t = Stream('t')
        u = Stream('u')
        v_stream = Stream('v')
        x = Stream('x')

        #----------------------------------------------------    
        # Define functions
        def g(lst): return sum(lst)

        def g_args(lst, multiplier):
            return sum(lst)*multiplier

        def general_f(lst, f):
            return f(lst)

        def fff(lst, f, addend):
            return f(lst, addend)

        def hhh(lst, addend):
            return sum(lst)+addend

        #----------------------------------------------------
        # Define agents
        d = zip_map(func=sum, in_streams=[x,u], out_stream=s, name='d')
        def magnitude(vector):
            return math.sqrt(sum([w*w for w in vector]))
        ssssss = Stream()
        ddd = zip_map(func=magnitude, in_streams=[x,u], out_stream=ssssss)
        zipxu = zip_stream_f([x,u])
        zip_map_xu = zip_map_f(sum, [x,u])
        zip_map_xu_merge = Stream('zip map xu merge')
        zip_map(sum, [x,u], zip_map_xu_merge)
        zip_map_g_args = zip_map_f(g_args, [x,u], multiplier=2)
        dd = zip_map(
            func=general_f, in_streams=[x,u], out_stream=t, name='dd', f=np.mean)
        zip_map_ss = zip_map_f(np.mean, [x,u])
        dddd = zip_map(
            func=fff, in_streams=[x,u], out_stream=v_stream, name='dddd', f=hhh,
            addend=10)


        #----------------------------------------------------
        #----------------------------------------------------
        # Append values to stream
        x.extend(list(range(3)))
        u.extend([10, 15, 18])
        scheduler.step()
        assert recent_values(s) == [10, 16, 20]
        assert recent_values(zip_map_g_args) == [2*v for v in recent_values(s)]
        assert recent_values(zipxu) == [(0, 10), (1, 15), (2, 18)]
        assert recent_values(t) == [5, 8, 10]
        assert recent_values(zip_map_ss) == [5.0, 8.0, 10.0]
        assert recent_values(v_stream) == [20, 26, 30]
        assert recent_values(zip_map_xu) == s.recent[:s.stop]
        assert recent_values(zip_map_xu) == recent_values(zip_map_xu_merge)

        #----------------------------------------------------
        u.append(37)
        x.extend(list(range(3, 5, 1)))
        scheduler.step()
        assert recent_values(s) == [10, 16, 20, 40]
        assert recent_values(zip_map_g_args) == [2*v for v in recent_values(s)]
        assert recent_values(zipxu) == [(0, 10), (1, 15), (2, 18), (3, 37)]
        assert recent_values(t) == [5, 8, 10, 20]
        assert recent_values(v_stream) == [20, 26, 30, 50]
        assert recent_values(zip_map_xu) == recent_values(zip_map_xu_merge)
        assert recent_values(ssssss) == [10.0, 15.033296378372908, 18.110770276274835, 37.12142238654117]

        #----------------------------------------------------
        u.extend([96, 95])
        scheduler.step()
        assert recent_values(s) == [10, 16, 20, 40, 100]
        assert recent_values(zipxu) == [(0, 10), (1, 15), (2, 18), (3, 37), (4, 96)]
        assert recent_values(t) == [5, 8, 10, 20, 50]
        assert recent_values(v_stream) == [20, 26, 30, 50, 110]
        assert recent_values(zip_map_xu) == recent_values(zip_map_xu_merge)


        #----------------------------------------------------
        # TEST MERGE_ASYNCH AND MIX
        #----------------------------------------------------

        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        w = Stream('w')

        def g_asynch(pair):
            index, value = pair
            if index == 0:
                return value*10
            elif index == 1:
                return value*2
            else:
                raise Exception()
        
        merge_asynch(func=lambda v: v, in_streams=[x,y], out_stream=z)
        merge_asynch(func=g_asynch, in_streams=[x,y], out_stream=w)
        mix_z = mix_f([x,y])
        scheduler.step()
        assert recent_values(z) == []
        assert recent_values(mix_z) == []
        assert recent_values(w) == []

        x.append(10)
        scheduler.step()
        assert recent_values(z) == [(0, 10)]
        assert recent_values(mix_z) == recent_values(z)
        assert recent_values(w)== [100]

        y.append('A')
        scheduler.step()
        assert recent_values(z) == [(0, 10), (1, 'A')]
        assert recent_values(mix_z) == recent_values(z)
        assert recent_values(w) == [100, 'AA']
        
        y.append('B')
        scheduler.step()
        assert recent_values(z) == [(0, 10), (1, 'A'), (1, 'B')]
        assert recent_values(mix_z) == recent_values(z)
        assert recent_values(w) == [100, 'AA', 'BB']
        
        x.append(20)
        scheduler.step()
        assert recent_values(z) == [(0, 10), (1, 'A'), (1, 'B'), (0, 20)]
        assert recent_values(z) == recent_values(mix_z)
        assert recent_values(w) == [100, 'AA', 'BB', 200]

        
        fahrenheit = Stream('fahrenheit')
        celsius = Stream('celsius')

        def fahrenheit_and_celsius(pair):
            index, value = pair
            if index == 0:
                return (value - 32.0)/1.8
            elif index == 1:
                return value
            else:
                raise Exception()

        fahrenheit_stream = Stream('fahrenheit temperatures')
        celsius_stream = Stream('celsius temperatures')
        centigrade_stream = Stream('centigrade temperatures')
        
        merge_asynch(func=fahrenheit_and_celsius,
                     in_streams=[fahrenheit_stream, celsius_stream],
                     out_stream=centigrade_stream)

        fahrenheit_stream.append(32)
        scheduler.step()
        assert recent_values(centigrade_stream) == [0.0]

        fahrenheit_stream.append(50)
        scheduler.step()
        assert recent_values(centigrade_stream) == [0.0, 10.0]

        fahrenheit_stream.append(68)
        scheduler.step()
        assert recent_values(centigrade_stream) == [0.0, 10.0, 20.0]

        celsius_stream.append(-10.0)
        scheduler.step()
        assert recent_values(centigrade_stream) == [0.0, 10.0, 20.0, -10.0]

        #----------------------------------------------------
        # TEST BLEND
        #----------------------------------------------------

        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        z_addend = Stream('z_addend')

        def double(v): return 2*v
        def double_add(v, addend): return 2*v+addend

        blend(func=double, in_streams=[x, y], out_stream=z)
        blend(func=double, in_streams=[x, y], out_stream=z_addend)
        blend_z = blend_f(double, [x, y])
        blend_add_z = blend_f(double_add, [x,y], addend=10)

        x.append(1)
        scheduler.step()
        assert recent_values(z) == [2]
        assert recent_values(blend_z) == recent_values(z)
        assert recent_values(blend_add_z) == [v+10 for v in recent_values(z)]

        x.extend(list(range(2,4)))
        scheduler.step()
        assert recent_values(z) == [2, 4, 6]
        assert recent_values(blend_z) == recent_values(z)
        assert recent_values(blend_add_z) == [v+10 for v in recent_values(z)]

        y.extend(list(range(100, 102)))
        scheduler.step()
        assert recent_values(z) == [2, 4, 6, 200, 202]
        assert recent_values(blend_z) == recent_values(z)
        assert recent_values(blend_add_z) == [v+10 for v in recent_values(z)]

        x.extend([10, 20])
        scheduler.step()
        assert recent_values(z) == [2, 4, 6, 200, 202, 20, 40]
        assert recent_values(blend_z) == recent_values(z)
        assert recent_values(blend_add_z) == [v+10 for v in recent_values(z)]

        #----------------------------------------------------
        # TEST MANY
        #----------------------------------------------------

        # func operates on a list with one element for each input stream.
        # func returns a list with one element for each output stream.
        def f_many(lst):
            return [sum(lst), sum(lst)+1]

        u_stream = Stream(name='u_stream')
        v_stream = Stream(name='v_stream')
        w_stream = Stream(name='w_stream')
        x_stream = Stream(name='x_stream')

        multi_agent = multi_element(
            func=f_many, in_streams=[u_stream, v_stream], out_streams=[w_stream, x_stream],
            name='multi_agent')
        ww_stream, xx_stream = multi_element_f(
            func=f_many, in_streams=[u_stream, v_stream],
            num_out_streams=2)

        u_stream.extend(list(range(5)))
        v_stream.extend(list(range(0, 40, 4)))
        scheduler.step()
        assert recent_values(w_stream) == [0, 5, 10, 15, 20]
        assert recent_values(x_stream) == [1, 6, 11, 16, 21]
        assert recent_values(ww_stream) == recent_values(w_stream)
        assert recent_values(xx_stream) == recent_values(x_stream)
        

        # ------------------------------------
        # Test many with args and kwargs
        # func operates on a list with one element for each input stream.
        # func returns a list with one element for each output stream.
        def f_multi_args_kwargs(lst, multiplicand, addend):
            return sum(lst)*multiplicand, sum(lst)+addend
        u_args_kwargs_stream = Stream(name='u_args_kwargs_stream')
        v_args_kwargs_stream = Stream(name='v_args_kwargs_stream')
        w_args_kwargs_stream = Stream(name='w_args_kwargs_stream')
        x_args_kwargs_stream = Stream(name='x_args_kwargs_stream')

        multi_args_kwargs_agent = multi_element(
            func=f_multi_args_kwargs,
            in_streams=[u_args_kwargs_stream, v_args_kwargs_stream],
            out_streams=[w_args_kwargs_stream, x_args_kwargs_stream],
            name='multi_args_kwargs_agent', multiplicand=2, addend=10)
        ww_args_kwargs_stream, xx_args_kwargs_stream = multi_element_f(
            func=f_multi_args_kwargs,
            in_streams=[u_args_kwargs_stream, v_args_kwargs_stream],
            num_out_streams=2,  multiplicand=2, addend=10)
        assert (recent_values(ww_args_kwargs_stream) ==
                recent_values(w_args_kwargs_stream))
        assert (recent_values(xx_args_kwargs_stream) ==
                recent_values(x_args_kwargs_stream))
            
        
        u_args_kwargs_stream.extend(list(range(5)))
        v_args_kwargs_stream.extend(list(range(0, 40, 4)))
        scheduler.step()
        assert recent_values(w_args_kwargs_stream) == [0, 10, 20, 30, 40] 
        assert recent_values(x_args_kwargs_stream) == [10, 15, 20, 25, 30]
        assert (recent_values(ww_args_kwargs_stream) ==
                recent_values(w_args_kwargs_stream))
        assert (recent_values(xx_args_kwargs_stream) ==
                recent_values(x_args_kwargs_stream))

        u_args_kwargs_stream.append(100)
        v_args_kwargs_stream.extend(list(range(40, 80, 4)))
        scheduler.step()
        assert recent_values(w_args_kwargs_stream) == \
          [0, 10, 20, 30, 40, 240]
        assert recent_values(x_args_kwargs_stream) == \
          [10, 15, 20, 25, 30, 130]
        assert (recent_values(ww_args_kwargs_stream) ==
                recent_values(w_args_kwargs_stream))
        assert (recent_values(xx_args_kwargs_stream) ==
                recent_values(x_args_kwargs_stream))

        u_args_kwargs_stream.extend([200, 300])
        scheduler.step()
        v_args_kwargs_stream.append(100)
        scheduler.step()
        assert recent_values(w_args_kwargs_stream) == \
          [0, 10, 20, 30, 40, 240, 448, 656]
        assert recent_values(x_args_kwargs_stream) == \
          [10, 15, 20, 25, 30, 130, 234, 338]
        assert (recent_values(ww_args_kwargs_stream) ==
                recent_values(w_args_kwargs_stream))
        assert (recent_values(xx_args_kwargs_stream) ==
                recent_values(x_args_kwargs_stream))

        #----------------------------------------------------
        #----------------------------------------------------
        # TEST STREAM ARRAY
        #----------------------------------------------------
        #----------------------------------------------------


        #----------------------------------------------------
        # Test zip_map with StreamArray
        #----------------------------------------------------
        x = StreamArray('x')
        y = StreamArray('y')
        z = StreamArray('z')
        a = StreamArray('a')

        def sum_array_axis_0(a_list_of_arrays): return np.sum(a_list_of_arrays, axis=0)
        merge_list(func=sum_array_axis_0, in_streams=[x,y], out_stream=z)
        
        def mean_array_axis_0(a_list_of_arrays): return np.mean(a_list_of_arrays, axis=0)
        zip_map_list(func=mean_array_axis_0, in_streams=[x,y], out_stream=a)

        x.extend(np.linspace(0.0, 9.0, 10))
        scheduler.step()
        y.extend(np.linspace(0.0, 4.0, 5))
        scheduler.step()
        expected_array = np.sum([np.linspace(0.0, 4.0, 5), np.linspace(0.0, 4.0, 5)], axis=0)
        assert isinstance(z, StreamArray)
        assert np.array_equal(recent_values(z), expected_array)
        expected_means = np.linspace(0.0, 4.0, 5)
        assert np.array_equal(recent_values(a), expected_means)


        #----------------------------------------------------
        # Test blend with StreamArray
        #----------------------------------------------------
        x = StreamArray('x')
        y = StreamArray('y')
        z = StreamArray('z')
        a = StreamArray('a')

        def double(v): return 2*v
        def double_add(v, addend): return 2*v+addend

        ## blend(func=double, in_streams=[x, y], out_stream=z)
        ## blend(func=double_add, in_streams=[x, y], out_stream=a, addend=10.0)

        ## x.append(np.array(1.0))
        ## scheduler.step()
        ## assert np.array_equal(recent_values(z), np.array([2.0]))
        ## assert np.array_equal(recent_values(a), recent_values(z)+10.0)

        ## x.extend(np.linspace(2.0, 3.0, 2))
        ## scheduler.step()
        ## assert np.array_equal(recent_values(z), np.array([2., 4., 6.]))
        ## assert np.array_equal(recent_values(a), recent_values(z)+10.0)

        ## y.extend(np.linspace(100.0, 101.0, 2))
        ## scheduler.step()
        ## assert np.array_equal(recent_values(z), [2., 4., 6., 200., 202.])
        ## assert np.array_equal(recent_values(a), recent_values(z)+10.0)

        ## x.extend([10., 20.])
        ## scheduler.step()
        ## assert np.array_equal(recent_values(z), [2., 4., 6., 200., 202., 20., 40.])
        ## assert np.array_equal(recent_values(a), recent_values(z)+10.0)


        #----------------------------------------------------
        # Test merge_asynch with StreamArray
        #----------------------------------------------------

        x = StreamArray('x')
        y = StreamArray('y')
        dt_0 = np.dtype([('time', int), ('value', float)])
        z = StreamArray('z', dimension=2)

        merge_asynch(func=lambda v: v, in_streams=[x,y], out_stream=z)
        scheduler.step()
        assert np.array_equal(recent_values(z), np.empty(shape=(0,2)))

        x.append(np.array(10.0))
        scheduler.step()
        assert np.array_equal(recent_values(z), np.array([(0, 10.0)]))

        y.append(np.array(1.0))
        scheduler.step()
        assert np.array_equal(recent_values(z), [(0, 10.), (1, 1.0)])
        
        y.append(np.array(2.0))
        scheduler.step()
        assert np.array_equal(recent_values(z), [(0, 10.), (1, 1.0), (1, 2.0)])
        
        x.append(np.array(20.0))
        scheduler.step()
        assert np.array_equal(recent_values(z), [(0, 10.), (1, 1.), (1, 2.), (0, 20.)])

        
        #----------------------------------------------------------------
        # Test window merge agent with no state
        r = Stream('r')
        w = Stream('w')
        x = Stream('x')
        a = Stream('a')
        def h(list_of_windows):
            return sum([sum(window) for window in list_of_windows])
        merge_window(
            func=h, in_streams=[r,w], out_stream=x,
            window_size=3, step_size=3)
        merge_stream = merge_window_f(
            func=h, in_streams=[r,w],
            window_size=3, step_size=3)
            
        #----------------------------------------------------------------
        
        #----------------------------------------------------------------
        # Test window merge agent with state
        def h_with_state(list_of_windows, state):
            return (sum([sum(window) for window in list_of_windows])+state,
                    state+1)
        merge_window(
            func=h_with_state, in_streams=[r,w], out_stream=a,
            window_size=3, step_size=3,
            state=0)
        #----------------------------------------------------------------

        #----------------------------------------------------------------    
        r.extend(list(range(16)))
        scheduler.step()
        assert recent_values(r) == list(range(16))
        assert recent_values(x) == []
        assert recent_values(merge_stream) == recent_values(x)
        assert recent_values(a) == []

        w.extend([10, 12, 14, 16, 18])
        scheduler.step()
        assert recent_values(r) == list(range(16))
        assert recent_values(w) == [10, 12, 14, 16, 18]
        assert recent_values(x) == [(0+1+2)+(10+12+14)]
        assert recent_values(a) == [39]

        #----------------------------------------------------------------    
        r.extend([10, -10, 21, -20])
        scheduler.step()
        assert recent_values(x) == [(0+1+2)+(10+12+14)]
        assert recent_values(a) == [39]

        #----------------------------------------------------------------    
        w.append(20)
        scheduler.step()
        assert recent_values(x) == [(0+1+2)+(10+12+14), (3+4+5)+(16+18+20)]
        assert recent_values(a) == [39, 67]

        #----------------------------------------------------------------        
        r.extend([-1, 1, 0])
        scheduler.step()
        assert recent_values(x) == [(0+1+2)+(10+12+14), (3+4+5)+(16+18+20)]
        assert recent_values(a) == [39, 67]

        #----------------------------------------------------------------
        # TEST MERGE_WINDOW WITH STREAM ARRAY
        #----------------------------------------------------------------
        x = StreamArray('x', dimension=2)
        b = StreamArray('b', dimension=2)
        a = StreamArray('a', dimension=2)
        
        #----------------------------------------------------------------
        # Test window merge agent with state
        def h_array(list_of_windows, state):
            return (sum([sum(window) for window in list_of_windows])+state,
                    state+1)
        merge_window(
            func=h_array, in_streams=[x,a], out_stream=b,
            window_size=2, step_size=2,
            state=0)
        #----------------------------------------------------------------
        x.extend(np.array([[1., 5.], [7., 11.]]))
        a.extend(np.array([[0., 1.], [2., 3.]]))
        scheduler.step()
        np.array_equal(recent_values(b), np.empty(shape=(0,2)))

        a.extend(np.array([[0., 1.], [1., 0.]]))
        scheduler.step()
        np.array_equal(recent_values(b), np.empty(shape=(0,2)))

        x.extend(np.array([[14., 18.], [18., 30.], [30., 38.], [34., 42.]]))
        scheduler.step()
        
        
        #-------------------------------------------------------------------
        # TEST MERGE_LIST
        #-------------------------------------------------------------------
        # Function g  operates on a list of lists, one list for each input
        # stream, to return a single list for the output stream.
        x = Stream('x list merge')
        u = Stream('u list merge')
        s = Stream('s list merge')
        def g(list_of_lists):
            return [sum(snapshot) for snapshot in list(zip(*list_of_lists))]
        d = merge_list(func=g, in_streams=[x,u], out_stream=s, name='d')
        ss = merge_list_f(g, [x,u])
        x.extend(list(range(4)))
        u.extend(list(range(10, 20, 2)))
        scheduler.step()
        assert recent_values(x) == [0, 1, 2, 3]
        assert recent_values(u) == [10, 12, 14, 16, 18]
        assert recent_values(s) == [10, 13, 16, 19]

        x = StreamArray()
        y = StreamArray()
        z = StreamArray(dtype='bool')
        def f(two_lists):
            return np.array(two_lists[0]) > np.array(two_lists[1])
        merge_list(f, [x,y], z)
        x.extend(np.array([3.0, 5.0, 7.0]))
        y.extend(np.array([4.0, 3.0, 10.0]))
        run()
        #-------------------------------------------------------------------
        

    def test_timed_mix_agents(self):
        scheduler = Stream.scheduler

        x = Stream('x')
        y = Stream('y')
        z = Stream('z')

        timed_mix([x,y], z)

        x.append((0, 'a'))
        scheduler.step()
        assert recent_values(z) == [(0, (0, 'a'))]

        x.append((1, 'b'))
        scheduler.step()
        assert recent_values(z) == [(0, (0, 'a')), (1, (0, 'b'))]

        y.append((2, 'A'))
        scheduler.step()
        assert recent_values(z) == \
          [(0, (0, 'a')), (1, (0, 'b')), (2, (1, 'A'))]

        y.append((5, 'B'))
        scheduler.step()
        assert recent_values(z) == \
          [(0, (0, 'a')), (1, (0, 'b')), (2, (1, 'A')), (5, (1, 'B'))]

        x.append((3, 'c'))
        scheduler.step()
        assert recent_values(z) == \
          [(0, (0, 'a')), (1, (0, 'b')), (2, (1, 'A')), (5, (1, 'B'))]

        x.append((4, 'd'))
        scheduler.step()
        assert recent_values(z) == \
          [(0, (0, 'a')), (1, (0, 'b')), (2, (1, 'A')), (5, (1, 'B'))]

        x.append((8, 'e'))
        scheduler.step()
        assert recent_values(z) == \
          [(0, (0, 'a')), (1, (0, 'b')), (2, (1, 'A')), (5, (1, 'B')), (8, (0, 'e'))]

    def test_timed_zip_agents(self):
        scheduler = Stream.scheduler

        x = Stream('x')
        y = Stream('y')
        z = Stream('z')

        # timed_zip_agent(in_streams=[x,y], out_stream=z, name='a')
        z = timed_zip_f([x, y])

        def concat_operator(timed_list):
            result = ''
            for timestamp_value in timed_list:
                result = result + timestamp_value[1]
            return result

        r = timed_window_f(concat_operator, x, 5, 5)
        s = timed_window_f(concat_operator, x, 20, 10)

        x.extend([[1, 'a'], [3, 'b'], [10, 'd'], [15, 'e'], [17, 'f']])
        y.extend([[2, 'A'], [3, 'B'], [9, 'D'], [20, 'E']])
        scheduler.step()
        assert z.recent[:z.stop] == \
          [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
           [10, ['d', None]], [15, ['e', None]], [17, ['f', None]]]
        assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd')]
        assert s.recent[:s.stop] == []
        
        x.extend([[21, 'g'], [23, 'h'], [40, 'i'], [55, 'j'], [97, 'k']])
        y.extend([[21, 'F'], [23, 'G'], [29, 'H'], [55, 'I']])
        scheduler.step()
        assert z.recent[:z.stop] == \
          [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
           [10, ['d', None]], [15, ['e', None]], [17, ['f', None]],
           [20, [None, 'E']], [21, ['g', 'F']], [23, ['h', 'G']],
           [29, [None, 'H']], [40, ['i', None]], [55, ['j', 'I']]]
        assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd'), (20, 'ef'),
                                     (25, 'gh'), (45, 'i'), (60, 'j')]
        assert s.recent[:s.stop] == [(20, 'abdef'), (30, 'defgh'), (40, 'gh'),
                                     (50, 'i'), (60, 'ij'), (70, 'j')]

        x.extend([[100, 'l'], [105, 'm']])
        y.extend([[100, 'J'], [104, 'K'], [105, 'L'], [107, 'M']])
        scheduler.step()
        assert z.recent[:z.stop] == \
          [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
           [10, ['d', None]], [15, ['e', None]], [17, ['f', None]],
           [20, [None, 'E']], [21, ['g', 'F']], [23, ['h', 'G']],
           [29, [None, 'H']], [40, ['i', None]], [55, ['j', 'I']],
           [97, ['k', None]], [100, ['l', 'J']], [104, [None, 'K']], [105, ['m', 'L']]]
        assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd'), (20, 'ef'),
                                     (25, 'gh'), (45, 'i'), (60, 'j'),
                                     (100, 'k'), (105, 'l')]
        assert s.recent[:s.stop] == [(20, 'abdef'), (30, 'defgh'), (40, 'gh'),
                                     (50, 'i'), (60, 'ij'), (70, 'j'), (100, 'k')
                                     ]

        x.extend([[106, 'n'], [110, 'o']])
        scheduler.step()
        assert z.recent[:z.stop] == \
          [[1, ['a', None]], [2, [None, 'A']], [3, ['b', 'B']], [9, [None, 'D']],
           [10, ['d', None]], [15, ['e', None]], [17, ['f', None]],
           [20, [None, 'E']], [21, ['g', 'F']], [23, ['h', 'G']],
           [29, [None, 'H']], [40, ['i', None]], [55, ['j', 'I']],
           [97, ['k', None]], [100, ['l', 'J']], [104, [None, 'K']], [105, ['m', 'L']],
           [106, ['n', None]], [107, [None, 'M']]
         ]
        assert r.recent[:r.stop] == [(5, 'ab'), (15, 'd'), (20, 'ef'),
                                     (25, 'gh'), (45, 'i'), (60, 'j'),
                                     (100, 'k'), (105, 'l'), (110, 'mn')]
        assert s.recent[:s.stop] == [(20, 'abdef'), (30, 'defgh'), (40, 'gh'),
                                     (50, 'i'), (60, 'ij'), (70, 'j'), (100, 'k'),
                                     (110, 'klmn')]
        return

    def simple_zip_map_test(self):
        # Get scheduler
        scheduler = Stream.scheduler
        # Define streams
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        # Define functions which are encapsulated
        def f(lst):
            return 2*sum(lst)
        # Define agents
        zip_map(func=f, in_streams=[x,y], out_stream=z)

        # A STEP
        # Put test data into input streams
        x.extend(list(range(4)))
        y.extend(list(range(10, 20, 2)))
        # Execute a step
        run()
        # Look at output data
        assert recent_values(z) == [20, 26, 32, 38]
        
        # Put test data into input streams
        x.extend([82, 10])
        y.extend([-10, 200, 300])
        # Execute a step
        scheduler.step()
        # Look at output data
        assert recent_values(z) == [20, 26, 32, 38, 200, 0]

        # Put test data into input streams
        x.extend([-200, -300])
        # Execute a step
        scheduler.step()
        # Look at output data
        assert recent_values(z) == [20, 26, 32, 38, 200, 0, 0, 0]

    def test_merge_multiple_windows(selfself):
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        def f(windows):
            return sum([sum(window) for window in windows])
        merge_multiple_windows(
            func=f, in_streams=[x,y], out_stream=z, window_sizes=[3, 1], step_sizes=[2, 1])
        x.extend(list(range(12)))
        y.extend(list(range(10)))
        Stream.scheduler.step()
        assert recent_values(z) == [3, 10, 17, 24, 31]

    def test_operator_overloading(selfself):
        x = Stream('x')
        y = Stream('y')
        u = Stream('u')
        v = Stream('v')
        z = x + y
        a = x - y
        b = x * y
        c = x % u
        d = x // u
        e = x // u
        f = u < v
        x.extend(list(range(100, 120, 2)))
        y.extend(list(range(10)))
        u.extend(list(range(1, 11, 1)))
        v.extend(list(range(0, 20, 2)))
        Stream.scheduler.step()
        assert (recent_values(z) ==
                [100, 103, 106, 109, 112, 115,
                 118, 121, 124, 127])
        assert (recent_values(a) ==
                [100, 101, 102, 103, 104, 105,
                 106, 107, 108, 109])
        assert (recent_values(b) ==
                [0, 102, 208, 318, 432, 550,
                 672, 798, 928, 1062])
        assert (recent_values(c) ==
                [0, 0, 2, 2, 3, 2, 0, 2, 8, 8])
        assert (recent_values(d) ==
                [100, 51, 34, 26, 21, 18, 16, 14, 12, 11])
        assert (recent_values(f) ==
                [False, False, True, True, True, True, True, True, True, True])

    def test_simple_merge_2(self):
        scheduler = Stream.scheduler
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')

        zip_map(func=sum, in_streams=[x,y], out_stream=z)

        x.extend(list(range(5)))
        y.extend(list(range(10)))
        
        run()
        
        assert(recent_values(z) == [0, 2, 4, 6, 8])

    def test_simple_merge_1(self):
        scheduler = Stream.scheduler
        x = Stream('x')
        u = Stream('u')
        s = Stream('s')
        d = zip_map(func=sum, in_streams=[x,u], out_stream=s, name='d')
        x.extend(list(range(3)))
        u.extend([10, 15, 18])
        
        run()
        assert(recent_values(s) == [10, 16, 20])
        
if __name__ == '__main__':
    unittest.main()


    
    
    
    
    

