import unittest
import sys
import os
from IoTPy.core.stream import Stream, StreamArray, _no_value, _multivalue
from IoTPy.agent_types.check_agent_parameter_types import *
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.agent_types.sink import *
from IoTPy.helper_functions.Buffer import Buffer


class test_sink(unittest.TestCase):
    
    def test_sink(self):
        import numpy as np
        scheduler = Stream.scheduler

        ## ----------------------------------------------
        ## # Examples from AssembleSoftware website: KEEP!!
        ## ----------------------------------------------
        ## def print_index(v, state, delimiter):
        ##     print str(state) + delimiter + str(v)
        ##     return state+1 # next state
        ## s = Stream()
        ## sink(print_index, s, 0, delimiter=':')
        ## s.extend(list(range(100,105)))

        ## s = Stream()
        ## def print_index(v, state, delimiter):
        ##     print str(state) + delimiter + str(v)
        ##     return state+1 # next state
        ## sink(print_index, s, 0, delimiter=':')
        ## s.extend(list(range(100,105)))
        # Set up parameters for call to stream_to_list
        ## ----------------------------------------------
        ## # Finished examples from AssembleSoftware website
        ## ----------------------------------------------

        #-----------------------------------------------
        # Set up parameters for call to sink
        print_list = []
        print_list_for_array = []
        def print_index(v, state, print_list):
          print_list.append(str(state) + ':' + str(v))
          return state+1 # next state
        s = Stream('s')
        s_array = StreamArray('s_array', dtype=int)

        #-----------------------------------------------
        # Call sink with initial state of 0
        sink(func=print_index, in_stream=s, state=0,
             print_list=print_list)
        sink(func=print_index, in_stream=s_array, state=0,
             print_list=print_list_for_array)
        
        s.extend(list(range(100,103)))
        s_array.extend(np.arange(100, 103))
        scheduler.step()
        assert print_list == ['0:100', '1:101', '2:102']
        assert print_list_for_array == print_list
        s.extend(list(range(200, 203)))
        scheduler.step()
        assert print_list == ['0:100', '1:101', '2:102',
                              '3:200', '4:201', '5:202']

        #-----------------------------------------------
        input_stream = Stream('input stream')
        input_stream_array = StreamArray('input stream array', dtype=int)
        output_list = []
        output_list_array = []

        # Call stream_to_list with no function
        stream_to_list(input_stream, output_list)
        stream_to_list(input_stream_array, output_list_array)
        # A test
        a_test_list = list(range(100, 105))
        a_test_array = np.arange(100, 105)
        input_stream.extend(a_test_list)
        input_stream_array.extend(a_test_array)
        scheduler.step()
        assert output_list == a_test_list
        assert output_list_array == a_test_list

        #-----------------------------------------------
        # test stream to list with a function
        def h(v, multiplier, addend): return v*multiplier+addend
        ss = Stream('ss')
        ss_array = StreamArray('ss_array', dtype=int)
        l = []
        l_array = []
        stream_to_list(ss, l, h, multiplier=2, addend=100)
        stream_to_list(in_stream=ss_array, target_list=l_array,
                       element_function=h, multiplier=2, addend=100 )
        test_list = [3, 23, 14]
        ss.extend(test_list)
        ss_array.extend(np.array(test_list))
        scheduler.step()
        assert l == [v*2+100 for v in test_list]
        assert l_array == l


        #-----------------------------------------------
        # test stream to list with a function and state
        def h(v, state, multiplier, addend):
            return v*multiplier+addend+state, v+state

        ss = Stream('ss')
        ss_array = StreamArray('ss_array', dtype=int)
        l = []
        l_array = []
        stream_to_list(ss, l, h, 0, multiplier=2, addend=100)
        stream_to_list(in_stream=ss_array, target_list=l_array, 
                       element_function=h, state=0,
                       multiplier=2, addend=100 )
        test_list = [3, 23, 14]
        ss.extend(test_list)
        ss_array.extend(np.array(test_list))
        scheduler.step()
        assert l == [106, 149, 154]
        assert l_array == l

        ss = Stream('ss')
        ss_array = StreamArray('ss_array', dtype=int)
        l = []
        l_array = []
        stream_to_list(ss, l, h, 0, multiplier=2, addend=100)
        stream_to_list(in_stream=ss_array, target_list=l_array, 
                       element_function=h, state=0,
                       multiplier=2, addend=100 )
        test_list = list(range(5))
        ss.extend(test_list)
        ss_array.extend(np.array(test_list))
        scheduler.step()
        assert l == [100, 102, 105, 109, 114]
        assert l_array == l

        # Test sink
        # func operates on a single element of the single input stream and does
        # not return any value.
        def p(v, lst): lst.append(v)
        in_stream_sink = Stream('in_stream_sink')
        a_list = []
        b_list = []
        sink_agent = sink_element(
            func=p, in_stream=in_stream_sink, name='sink_agent',
            lst=a_list) 
        sink(func=p, in_stream=in_stream_sink, lst=b_list)
        test_list = [1, 13, 29]
        in_stream_sink.extend(test_list)
        scheduler.step()
        assert a_list == test_list
        assert b_list == test_list

        # ------------------------------------
        # Test sink with state
        # func operates on a single element of the single input stream and state.
        # func does not return any value.
        
        def p_s(element, state, lst, stream_name):
            lst.append([stream_name, element])
            return state+1
        
        in_stream_sink_with_state = Stream('s')
        c_list = []
        sink_with_state_agent = sink_element(
            func=p_s, in_stream=in_stream_sink_with_state,
            state=0, name='sink_with_state_agent',
            lst = c_list,
            stream_name ='s')

        #------------------------------------------------------------------------------
        # Test sink as a function with state
        d_list = []
        sink(p_s, in_stream_sink_with_state, state=0,
             lst=d_list, stream_name='s')
        in_stream_sink_with_state.extend(list(range(2)))
        scheduler.step()
        assert c_list == [['s', 0], ['s', 1]]
        assert d_list == c_list

        # ------------------------------------
        # Test sink with side effect
        # func operates on a single element of the single input stream and state.
        # func does not return any value.
        
        def sink_with_side_effect_func(element, side_effect_list, f):
            side_effect_list.append(f(element))
            return None

        side_effect_list_0 = []
        side_effect_list_1 = []
        side_effect_list_2 = []

        def ff(element):
            return element*2

        def fff(element):
            return element+10
        stm = Stream('stm')

        sink_with_side_effect_agent_0 = sink_element(
            func=sink_with_side_effect_func,
            in_stream=stm,
            name='sink_with_side_effect_agent_0',
            side_effect_list=side_effect_list_0, f=ff)

        sink_with_side_effect_agent_1 = sink_element(
            func=sink_with_side_effect_func,
            in_stream=stm,
            name='sink_with_side_effect_agent_1',
            side_effect_list=side_effect_list_1, f=fff)
        
        def f_stateful(element, state):
            return element+state, element+state
        def f_stateful_2(element, state):
            return element*state, element+state
        target_stream_to_list_simple= []
        stream_to_list(stm,
                       target_stream_to_list_simple)
        stream_to_list(
            in_stream=stm,
            target_list=side_effect_list_2,
            element_function=lambda v: 2*v)
        target_stream_to_list_stateful= []
        stream_to_list(
            in_stream=stm,
            target_list=target_stream_to_list_stateful,
            element_function=f_stateful, state=0)
        target_stream_to_list_stateful_2= []
        stream_to_list(
            in_stream=stm,
            target_list=target_stream_to_list_stateful_2,
            element_function=f_stateful_2, state=0)
        
        stream_to_file(stm, 'test1.txt') 
        stream_to_file(stm, 'test2.txt', lambda v: 2*v)
        stream_to_file(stm, 'test3.txt', f_stateful, state=0)

        
        is_py2 = sys.version[0] == '2'
        if is_py2:
            import Queue as queue
        else:
            import queue as queue
        queue_1 = queue.Queue()
        queue_2 = queue.Queue()
        queue_3 = queue.Queue()
        stream_to_queue(stm, queue_1)
        stream_to_queue(stm, queue_2, lambda v: 2*v)
        stream_to_queue(stm, queue_3, f_stateful, 0)

        stm.extend(list(range(5)))
        scheduler.step()
        assert target_stream_to_list_stateful == [0, 1, 3, 6, 10]
        assert target_stream_to_list_stateful_2 == [0, 0, 2, 9, 24]
        assert side_effect_list_0 == [0, 2, 4, 6, 8]
        assert side_effect_list_1 == [10, 11, 12, 13, 14]
        assert side_effect_list_0 == side_effect_list_2
        assert target_stream_to_list_simple == list(range(5))

        with open('test1.txt') as the_file:
            file_contents_integers = [int(v) for v in (the_file.readlines())]
        assert file_contents_integers == recent_values(stm)

        with open('test2.txt') as the_file:
            file_contents_integers = [int(v) for v in (the_file.readlines())]
        assert file_contents_integers == [2*v for v in recent_values(stm)]

        with open('test3.txt') as the_file:
            file_contents_integers = [int(v) for v in (the_file.readlines())]
        assert file_contents_integers == [0, 1, 3, 6, 10]
        os.remove('test1.txt')
        os.remove('test2.txt')
        os.remove('test3.txt')

        def h(v, multiplier, addend): return v*multiplier+addend
        ss = Stream()
        stream_to_file(ss, 'test4.txt', h, multiplier=2, addend=100)
        test_list = [3, 23, 14]
        ss.extend(test_list)
        scheduler.step()
        with open('test4.txt') as the_file:
            file_contents_integers = [
                int(v) for v in (the_file.readlines())]
        assert file_contents_integers == [v*2+100 for v in test_list]
        os.remove('test4.txt')

        def h(v, state, multiplier, addend):
            return v*multiplier+addend+state, v+state
        ss = Stream()
        stream_to_file(ss, 'test5.txt', h, 0, multiplier=2, addend=100)
        test_list = [3, 23, 14]
        ss.extend(test_list)
        scheduler.step()
        with open('test5.txt') as the_file:
            file_contents_integers = [
                int(v) for v in (the_file.readlines())]
        scheduler.step()
        assert file_contents_integers == [106, 149, 154]
        os.remove('test5.txt')

        # ------------------------------------
        # Testing stream_to_queue
        def h(v, state, multiplier, addend):
            return v*multiplier+addend+state, v+state
        ss = Stream()
        queue_4 = queue.Queue()
        stream_to_queue(ss, queue_4, h, 0, multiplier=2, addend=100)
        test_list = [3, 23, 14]
        ss.extend(test_list)
        scheduler.step()
        queue_contents = []
        while not queue_4.empty():
            queue_contents.append(queue_4.get())
        assert queue_contents == [106, 149, 154]

        # Test with state and keyword arguments
        def h(v, state, multiplier, addend):
            return v*multiplier+addend+state, v+state
        ss = Stream()
        stream_to_queue(ss, queue_4, h, 0, multiplier=2, addend=100)
        test_list = [3, 23, 14]
        ss.extend(test_list)
        queue_contents = []
        scheduler.step()
        while not queue_4.empty():
            queue_contents.append(queue_4.get())
        assert queue_contents == [106, 149, 154]

        # Another test with state and keyword arguments
        ss = Stream()
        queue_5 = queue.Queue()
        stream_to_queue(ss, queue_5, h, 0, multiplier=2, addend=100)
        test_list = list(range(5))
        ss.extend(test_list)
        scheduler.step()
        queue_contents = []
        while not queue_5.empty():
            queue_contents.append(queue_5.get())
        assert queue_contents == [100, 102, 105, 109, 114]

        # Test stream_to_buffer
        s = Stream()
        buf = Buffer(max_size=10)
        stream_to_buffer(s, buf)
        test_list = list(range(5))
        s.extend(test_list)
        scheduler.step()
        assert buf.get_all() == test_list
        next_test = list(range(5, 10, 1))
        s.extend(next_test)
        scheduler.step()
        assert buf.read_all() == next_test
        assert buf.get_all() == next_test

        s = Stream('s')
        print_list = []
        def f(lst):
            print_list.extend(lst)
        sink_window(
            func=f, in_stream=s, window_size=4, step_size=2)
        s.extend(list(range(10)))
        scheduler.step()
        assert print_list == [
            0, 1, 2, 3, 2, 3, 4, 5, 4,
            5, 6, 7, 6, 7, 8, 9]

        s = Stream('s')
        print_list = []
        def f(lst):
            print_list.extend(lst)
        sink_list(func=f, in_stream=s)
        s.extend(list(range(10)))
        Stream.scheduler.step()
        assert print_list == list(range(10))


        import numpy as np
        t = StreamArray('t', dtype='int')
        print_list = []
        def f(lst):
            print_list.extend(lst)
        sink_list(func=f, in_stream=t)
        t.extend(np.arange(10))
        Stream.scheduler.step()
        assert print_list == list(range(10))
        print ('TEST OF SINK IS SUCCESSFUL')

    def test_sink_conditional(self):
        import random
        s = Stream('s')
        def f(v):
            if v > 0.3:
                print ('True: v is ', v)
                return True
            else:
                print ('False: v is ', v)
                return False
        sink_conditional(func=f, in_stream=s)
        for i in range(20):
            s.append(random.random())
        Stream.scheduler.step()


    def test_sink_conditional(self):
        import random
        s = Stream('s')
        def f(v):
            if v > 0.3:
                print ('True: v is ', v)
                return True
            else:
                print ('False: v is ', v)
                return False
        sink_conditional(func=f, in_stream=s)
        for i in range(20):
            s.append(random.random())
        Stream.scheduler.step()
    
if __name__ == '__main__':
    unittest.main()
