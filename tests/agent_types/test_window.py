

import numpy as np 
import unittest
from IoTPy.core.stream import Stream, StreamArray, run
from IoTPy.core.agent import Agent
from IoTPy.agent_types.op import *
from IoTPy.agent_types.merge import merge_window, merge_window_f
from IoTPy.agent_types.split import split_window
from IoTPy.agent_types.multi import multi_window, multi_window_f
from IoTPy.agent_types.sink import sink_window
from IoTPy.agent_types.basics import map_w
from IoTPy.helper_functions.recent_values import recent_values
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#     WINDOW AGENT TESTS
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------

class test_window_agents(unittest.TestCase):
    
    def test_window(self):
        scheduler = Stream.scheduler

        q = Stream('q')
        qq = Stream('qq')
        r = Stream('r')
        s = Stream('s')
        t = Stream('t')
        u = Stream('u')
        v = Stream('v')
        w = Stream('w')
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        a = Stream('a')
        b = Stream('b')
        c = Stream('c')
        yy = Stream('yy')
        zz = Stream('zz')
        
        #----------------------------------------------------------------
        # Test simple window map agent with the same window size and step size
        smap = map_window_f(func=sum, in_stream=r, window_size=4, step_size=4)
        map_window(
            func=sum, in_stream=r, out_stream=s, window_size=4, step_size=4)
        #----------------------------------------------------------------
        
        #----------------------------------------------------------------
        # Test simple window list agent with the same window size and step size
        def f_map_window_list(lst):
            return [max(lst)]*len(lst)
        s_list = Stream('s list')
        map_window_list(func=f_map_window_list, in_stream=r, out_stream=s_list,
                    window_size=4, step_size=4)
        #----------------------------------------------------------------

        #----------------------------------------------------------------
        # Test window map agent with different window and step sizes
        map_window(
            func=sum, in_stream=r, out_stream=t, window_size=3, step_size=2)
        #----------------------------------------------------------------

        #----------------------------------------------------------------
        # Test window map agent with a NumPy function
        map_window(
            func=np.mean, in_stream=r, out_stream=q,
            window_size=3, step_size=2, name='bb')
        #----------------------------------------------------------------

        #----------------------------------------------------------------
        # Test window map agent with arguments
        def map_with_args(window, addend):
            return np.mean(window) + addend
        map_window(
            func=map_with_args, in_stream=r, out_stream=qq,
            window_size=3, step_size=2,
            addend=1)
        #----------------------------------------------------------------

        #----------------------------------------------------------------
        # Test window map agent with user-defined function and no state
        map_window(
            func=lambda v: sum(v)+1,
            in_stream=r, out_stream=u,
            window_size=4, step_size=4)
        #----------------------------------------------------------------

        #----------------------------------------------------------------
        # Test window map agent with state
        def g(lst, state):
            return sum(lst)+state, sum(lst)+state
        map_window(
            func=g, in_stream=r, out_stream=v,
            window_size=4, step_size=4, state=0)
        #----------------------------------------------------------------


        #----------------------------------------------------------------
        # Test window merge agent with no state
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
        # Test window split agent with no state
        def splt(window):
            return sum(window), max(window)

        split_window(
            func=splt, in_stream=r, out_streams=[y,z],
            window_size=3, step_size=3)
        #----------------------------------------------------------------


        #----------------------------------------------------------------
        # Test window split agent with state
        def split_with_state(window, state):
            return (sum(window)+state, max(window)+state), state+1

        split_window(
            func=split_with_state, in_stream=r, out_streams=[yy,zz],
            window_size=3, step_size=3, state=0)
        #----------------------------------------------------------------


        #----------------------------------------------------------------
        # Test window many-to-many with state and args
        def func_multi_window_with_state_and_args(
                windows, state, cutoff):
            return (
                (max(max(windows[0]), max(windows[1]), cutoff, state),
                min(min(windows[0]), min(windows[1]), cutoff, state)),
                state+2)
        multi_window(
            func=func_multi_window_with_state_and_args,
            in_streams=[r,w], out_streams=[b,c], state=0,
            window_size=3, step_size=3, cutoff=15)
        multi_window_b, multi_window_c = multi_window_f(
            func=func_multi_window_with_state_and_args,
            in_streams=[r,w], num_out_streams=2, state=0,
            window_size=3, step_size=3, cutoff=15)
            
                
        #----------------------------------------------------------------


        #----------------------------------------------------------------    
        r.extend(list(range(16)))
        scheduler.step()
        assert recent_values(r) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        assert recent_values(s) == [0+1+2+3, 4+5+6+7, 8+9+10+11, 12+13+14+15]
        assert recent_values(smap) == recent_values(s)
        assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14]
        assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13]
        assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14]
        assert recent_values(u) == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1]
        assert recent_values(v) == [6, 28, 66, 120]
        assert recent_values(w) == []
        assert recent_values(x) == []
        assert recent_values(merge_stream) == recent_values(x)
        # y is sum of windows of r with window and step size of 3
        assert recent_values(y) == [3, 12, 21, 30, 39]
        assert recent_values(yy) == [3, 13, 23, 33, 43]
        #  y is max of windows of r with window and step size of 3
        assert recent_values(z) == [2, 5, 8, 11, 14]
        assert recent_values(zz) == [2, 6, 10, 14, 18]
        assert recent_values(a) == []
        assert recent_values(b) == []
        assert recent_values(c) == []


        #----------------------------------------------------------------
        #----------------------------------------------------------------
        # Step through the scheduler
        #----------------------------------------------------------------
        #----------------------------------------------------------------
        w.extend([10, 12, 14, 16, 18])
        scheduler.step()
        assert recent_values(r) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        assert recent_values(s) == [0+1+2+3, 4+5+6+7, 8+9+10+11, 12+13+14+15]
        assert recent_values(s_list) == [3, 3, 3, 3, 7, 7, 7, 7, 11, 11, 11, 11, 15, 15, 15, 15]
        assert recent_values(smap) == recent_values(s)
        assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14]
        assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13]
        assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14]
        assert recent_values(u) == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1]
        assert recent_values(v) == [6, 28, 66, 120]
        assert recent_values(w) == [10, 12, 14, 16, 18]
        assert recent_values(x) == [(0+1+2)+(10+12+14)]
        assert recent_values(merge_stream) == recent_values(x)
        assert recent_values(y) == [3, 12, 21, 30, 39]
        assert recent_values(yy) == [3, 13, 23, 33, 43]
        assert recent_values(z) == [2, 5, 8, 11, 14]
        assert recent_values(zz) == [2, 6, 10, 14, 18]
        assert recent_values(a) == [39]
        assert recent_values(b) == [15]
        assert recent_values(c) == [0]
        

        #----------------------------------------------------------------    
        r.extend([10, -10, 21, -20])
        scheduler.step()
        assert recent_values(s) == [6, 22, 38, 54, 1]
        assert recent_values(s_list) == \
          [3, 3, 3, 3, 7, 7, 7, 7, 11, 11, 11, 11, 15, 15, 15, 15, 21, 21, 21, 21]
          
        assert recent_values(smap) == recent_values(s)
        assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14,
                                     14+15+10, 10+(-10)+21]
        assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13, 13, 7]
        assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14, 14, 8]
        assert recent_values(u) == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1,
                                    10 + (-10) + 21 + (-20) + 1]
        assert recent_values(v) == [6, 28, 66, 120, 121]
        assert recent_values(w) == [10, 12, 14, 16, 18]
        assert recent_values(x) == [(0+1+2)+(10+12+14)]
        assert recent_values(merge_stream) == recent_values(x)
        assert recent_values(y) == [3, 12, 21, 30, 39, 15]
        assert recent_values(yy) == [3, 13, 23, 33, 43, 20]
        assert recent_values(z) == [2, 5, 8, 11, 14, 15]
        assert recent_values(zz) == [2, 6, 10, 14, 18, 20]
        assert recent_values(a) == [39]
        assert recent_values(b) == [15]
        assert recent_values(c) == [0]


        #----------------------------------------------------------------    
        w.append(20)
        scheduler.step()
        assert recent_values(s) == [6, 22, 38, 54, 1]
        assert recent_values(smap) == recent_values(s)
        assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14,
                                     14+15+10, 10+(-10)+21]
        assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13, 13, 7]
        assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14, 14, 8]
        assert recent_values(u) == [0+1+2+3+1, 4+5+6+7+1, 8+9+10+11+1, 12+13+14+15+1,
                                    10 + (-10) + 21 + (-20) + 1]
        assert recent_values(v) == [6, 28, 66, 120, 121]
        assert recent_values(w) == [10, 12, 14, 16, 18, 20]
        assert recent_values(x) == [(0+1+2)+(10+12+14), (3+4+5)+(16+18+20)]
        assert recent_values(merge_stream) == recent_values(x)
        assert recent_values(y) == [3, 12, 21, 30, 39, 15]
        assert recent_values(yy) == [3, 13, 23, 33, 43, 20]
        assert recent_values(z) == [2, 5, 8, 11, 14, 15]
        assert recent_values(zz) == [2, 6, 10, 14, 18, 20]
        assert recent_values(a) == [39, 67]
        assert recent_values(b) == [15, 20]
        assert recent_values(multi_window_b) == recent_values(b)
        assert recent_values(c) == [0, 2]
        assert recent_values(multi_window_c) == recent_values(c)

        #----------------------------------------------------------------        
        r.extend([-1, 1, 0])
        scheduler.step()
        assert recent_values(s) == [6, 22, 38, 54, 1]
        assert recent_values(smap) == recent_values(s)
        assert recent_values(t) == [0+1+2, 2+3+4, 4+5+6, 6+7+8, 8+9+10, 10+11+12, 12+13+14,
                                     14+15+10, 10+(-10)+21, 21-20-1, -1+1+0]
        assert recent_values(q) == [1, 3, 5, 7, 9, 11, 13, 13, 7, 0, 0]
        assert recent_values(qq) == [2, 4, 6, 8, 10, 12, 14, 14, 8, 1, 1]
        assert recent_values(u) == [7, 23, 39, 55, 2]
        assert recent_values(v) == [6, 28, 66, 120, 121]
        assert recent_values(w) == [10, 12, 14, 16, 18, 20]
        assert recent_values(x) == [(0+1+2)+(10+12+14), (3+4+5)+(16+18+20)]
        assert recent_values(merge_stream) == recent_values(x)
        assert recent_values(y) == [3, 12, 21, 30, 39, 15, 0]
        assert recent_values(yy) == [3, 13, 23, 33, 43, 20, 6]
        assert recent_values(z) == [2, 5, 8, 11, 14, 15, 21]
        assert recent_values(zz) == [2, 6, 10, 14, 18, 20, 27]
        assert recent_values(a) == [39, 67]
        assert recent_values(b) == [15, 20]
        assert recent_values(multi_window_b) == recent_values(b)
        assert recent_values(c) == [0, 2]
        assert recent_values(multi_window_c) == recent_values(c)

        #----------------------------------------------------------------
        #----------------------------------------------------------------
        # TEST WINDOW WITH STREAM ARRAY
        #----------------------------------------------------------------
        #----------------------------------------------------------------
        # Simple linear arrays
        x = StreamArray('x')
        y = StreamArray('y')

        #----------------------------------------------------------------
        # Test window map agent with stream arrays and a NumPy function
        map_window(
            func=np.mean, in_stream=x, out_stream=y,
            window_size=3, step_size=3, name='window map agent for arrays')
        #----------------------------------------------------------------

        #----------------------------------------------------------------
        x.extend(np.linspace(0.0, 11.0, 12))
        scheduler.step()
        assert np.array_equal(recent_values(x), np.linspace(0.0, 11.0, 12))
        # y[0] = (0+1+2)//3.0, y[1] = (3+4+5)//3.0
        assert np.array_equal(recent_values(y), np.array([1.0, 4.0, 7.0, 10.0]))
        
        x = StreamArray('x', dimension=2)
        y = StreamArray('y', dimension=2)
        z = StreamArray('z', dimension=2)
        a = StreamArray('a', dimension=2)
        b = StreamArray('b', dimension=2)
        c = StreamArray('c', dimension=2)
        d = StreamArray('d', dimension=2)
        p = StreamArray('p', dimension=2)
        q = StreamArray('q', dimension=2)
        r = StreamArray('r', dimension=2)
        s = StreamArray('s', dimension=2)
        t = StreamArray('t', dimension=2)

        #----------------------------------------------------------------
        # Test window map agent with stream arrays and a NumPy function
        # f() and ff() differ only in the axis.
        def f(input_array):
            return np.mean(input_array, axis=0)
        def ff(input_array):
            return np.mean(input_array, axis=1)
        map_window(
            func=f, in_stream=x, out_stream=y,
            window_size=2, step_size=2, name='window map agent for arrays')
        map_window(
            func=ff, in_stream=x, out_stream=t,
            window_size=2, step_size=2, name='window map agent for arrays ff')
        
        #----------------------------------------------------------------

        #----------------------------------------------------------------
        # Test window sink with stream arrays
        def sum_array(input_array, output_list):
            output_list.append(sum(input_array))
        sum_array_list = []
        sink_window(
            func=sum_array, in_stream=x,
            window_size=2, step_size=2, name='sum array',
            output_list=sum_array_list)
        #----------------------------------------------------------------
        
        #----------------------------------------------------------------
        # Test window map agent with state
        def g(lst, state):
            return sum(lst)+state, state+1
        map_window(
            func=g, in_stream=x, out_stream=z,
            window_size=2, step_size=2, state=0)
        #----------------------------------------------------------------


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

            
        #----------------------------------------------------------------
        # Test window split agent with state
        def split_with_state(window, state):
            return [np.sum(window, axis=0)+state, np.max(window, axis=0)+state], \
              state+1.0

        split_window(
            func=split_with_state, in_stream=x, out_streams=[c,d],
            window_size=2, step_size=2, state=0.0)
        #----------------------------------------------------------------

        
        #----------------------------------------------------------------
        # Test window many-to-many with state and args
        def func_multi_window_with_state_and_args(
                windows, state, cutoff):
            max_value = np.maximum(
                np.max(windows[0], axis=0),
                np.max(windows[1], axis=0))
            max_value = np.maximum(max_value, cutoff)+state

            min_value = np.minimum(
                np.min(windows[0], axis=0),
                np.min(windows[1], axis=0))
            min_value = np.minimum(min_value, cutoff)+state
            
            return (max_value, min_value), state+1

        multi_window(
            func=func_multi_window_with_state_and_args,
            in_streams= [x,a], out_streams=[r,s], state=0,
            window_size=2, step_size=2, cutoff=10)
        #----------------------------------------------------------------

        x.extend(np.array([[1., 5.], [7., 11.]]))
        a.extend(np.array([[0., 1.], [2., 3.]]))
        scheduler.step()
        # sum_array_list is the sum of x with window size, step size of 2
        assert np.array_equal(sum_array_list,
                              [np.array([1. + 7., 5. + 11.])])
        # y is the mean of x with window size and step size of 2
        assert np.array_equal(recent_values(x),
                              np.array([[1., 5.], [7., 11.]]))
        assert np.array_equal(recent_values(y),
                              np.array([[(1.+7.)//2.0, (5.+11.)//2.]]))
        assert np.array_equal(recent_values(t),
                              np.array([[(1.+5.)//2.0, (7.+11.)//2.]]))
        assert np.array_equal(recent_values(z), np.array([[1. + 7., 5. + 11]]))
        assert np.array_equal(recent_values(b),
                              [np.array([1.+ 7. + 0. + 2., 5. + 11. + 1. + 3.])])
        assert np.array_equal(recent_values(c), np.array([[8., 16.]]))
        assert np.array_equal(recent_values(d), np.array([[7., 11.]]))
        assert np.array_equal(recent_values(r), np.array([[10., 11.]]))
        assert np.array_equal(recent_values(s), np.array([[0., 1.]]))


        a.extend(np.array([[0., 1.], [1., 0.]]))
        scheduler.step()
        assert np.array_equal(recent_values(y), np.array([[(1.+7.)/2.0, (5.+11.)/2.]]))
        assert np.array_equal(recent_values(z), np.array([[1. + 7., 5. + 11]]))
        assert np.array_equal(recent_values(b),
                              [np.array([1.+ 7. + 0. + 2., 5. + 11. + 1. + 3.])])
        assert np.array_equal(recent_values(c), np.array([[8., 16.]]))
        assert np.array_equal(recent_values(d), np.array([[7., 11.]]))
        assert np.array_equal(recent_values(r), np.array([[10., 11.]]))
        assert np.array_equal(recent_values(s), np.array([[0., 1.]]))
        

        x.extend(np.array([[14., 18.], [18., 30.], [30., 38.], [34., 42.]]))
        scheduler.step()
        assert np.array_equal(recent_values(y), np.array([[4., 8.], [16., 24.], [32., 40.]]))
        assert np.array_equal(recent_values(z), np.array([[8., 16.], [33., 49.], [66., 82.]]))
        assert np.array_equal(recent_values(c), np.array([[8., 16.], [33., 49.], [66., 82.]]))
        assert np.array_equal(recent_values(d), np.array([[7., 11.], [19., 31.],[36., 44.]]))
        assert np.array_equal(recent_values(r), np.array([[10., 11.], [19., 31.]]))
        assert np.array_equal(recent_values(s), np.array([[0., 1.], [1., 1.]]))

        print ('TEST OF OP (WINDOW) IS SUCCESSFUL')
        return

    def test_halt_agent(self):
        x = Stream('x')
        y = Stream('y')
        a = map_window(func=sum, in_stream=x, out_stream=y, window_size=2, step_size=2)
        x.extend(list(range(6)))
        run()
        assert recent_values(y) == [1, 5, 9]
        a.halt()
        run()
        assert recent_values(y) == [1, 5, 9]
        x.extend(list(range(10,15)))
        run()
        assert recent_values(y) == [1, 5, 9]

    def test_decorator(self):
        @map_w
        def sliding_window_mean(lst):
            return np.mean(lst)
        x = Stream()
        y = Stream()
        sliding_window_mean(in_stream=x, out_stream=y, window_size=4, step_size=4)
        x.extend(list(range(20)))
        run()
        print (recent_values(y))
        

if __name__ == '__main__':
    unittest.main()