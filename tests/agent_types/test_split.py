"""
Tests split.py
   
"""
import unittest
import numpy as np
from IoTPy.core.agent import Agent, InList
from IoTPy.core.stream import StreamArray, Stream, _no_value, _multivalue, run
from IoTPy.agent_types.sink import sink_window
from IoTPy.agent_types.basics import split_e, split_w, fsplit_2e, fsplit_2w
from IoTPy.agent_types.check_agent_parameter_types import *
from IoTPy.helper_functions.recent_values import recent_values
from IoTPy.agent_types.split import *

#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#                                     TEST SPLIT
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------


class test_split_agents(unittest.TestCase):
    
    def test_split_agents(self):
    
        scheduler = Stream.scheduler
        
        s = Stream('s')
        
        u = Stream('u')
        v = Stream('v')
        w = Stream('w')
        
        y = Stream('y')
        z = Stream('z')


        # Test split
        # func operates on a single element of the single input stream and
        # return a list of elements, one for each output stream.
        def h(element):
            return [element+1, element*2]
        def h_args(element, addend, multiplier):
            return [element+addend, element*multiplier]

        in_stream_split = Stream('in_stream_split')
        r = Stream('r')
        t = Stream('t')
        e = split_element(func=h, in_stream=in_stream_split,
                                out_streams=[r, t], name='e')
        r_split, t_split = split_element_f(function=h, in_stream=in_stream_split,
                                        num_out_streams=2, )
        r_args, t_args = split_element_f(
            h_args, in_stream_split, 2, addend=1, multiplier=2)

        scheduler.step()
        assert recent_values(r) == []
        assert recent_values(t) == []
        assert recent_values(r_split) == recent_values(r)
        assert recent_values(t_split) == recent_values(t)
        assert recent_values(r_args) == recent_values(r)
        assert recent_values(t_args) == recent_values(t)

        in_stream_split.extend(list(range(5)))
        scheduler.step()
        assert recent_values(r) == [1, 2, 3, 4, 5]
        assert recent_values(t) == [0, 2, 4, 6, 8]
        assert recent_values(r_split) == recent_values(r)
        assert recent_values(t_split) == recent_values(t)
        assert recent_values(r_args) == recent_values(r)
        assert recent_values(t_args) == recent_values(t)

        in_stream_split.append(10)
        scheduler.step()
        assert recent_values(r) == [1, 2, 3, 4, 5, 11]
        assert recent_values(t) == [0, 2, 4, 6, 8, 20]

        in_stream_split.extend([20, 100])
        scheduler.step()
        assert recent_values(r) == [1, 2, 3, 4, 5, 11, 21, 101]
        assert recent_values(t) == [0, 2, 4, 6, 8, 20, 40, 200]
        assert recent_values(r_split) == recent_values(r)
        assert recent_values(t_split) == recent_values(t)
        assert recent_values(r_args) == recent_values(r)
        assert recent_values(t_args) == recent_values(t)

        # Test split with kwargs
        def f_list(element, list_of_functions):
            return [f(element) for f in list_of_functions]

        def f_0(element):
            return element*2
        def f_1(element):
            return element+10

        x = Stream('x')
        rr = Stream('rr')
        tt = Stream('tt')
        ee = split_element(func=f_list, in_stream=x, out_streams=[rr, tt], name='ee',
                                 list_of_functions=[f_0, f_1])
        x.extend(list(range(5)))
        scheduler.step()
        assert recent_values(rr) == [0, 2, 4, 6, 8]
        assert recent_values(tt) == [10, 11, 12, 13, 14]

        # ------------------------------------
        # Test split with state
        # func operates on an element of the single input stream and state.
        # func returns a list with one element for each output stream.
        def h_state(element, state):
            return ([element+state, element*state], state+1)
        r_state = Stream(name='r_state')
        t_state = Stream(name='t_state')
        in_stream_split_state = Stream('in_stream_split_state')
        
        e_state = split_element(
            func=h_state, in_stream=in_stream_split_state,
             out_streams=[r_state, t_state], name='e', state=0)

        scheduler.step()
        assert recent_values(r_state) == []
        assert recent_values(t_state) == []

        in_stream_split_state.extend(list(range(5)))
        scheduler.step()
        assert recent_values(r_state) == [0, 2, 4, 6, 8]
        assert recent_values(t_state) == [0, 1, 4, 9, 16]

        in_stream_split_state.append(20)
        scheduler.step()
        assert recent_values(r_state) == [0, 2, 4, 6, 8, 25]
        assert recent_values(t_state) == [0, 1, 4, 9, 16, 100]

        in_stream_split_state.extend([44, 93])
        scheduler.step()
        assert recent_values(r_state) == [0, 2, 4, 6, 8, 25, 50, 100]
        assert recent_values(t_state) == [0, 1, 4, 9, 16, 100, 264, 651]

        # ------------------------------------
        # Test split with state and args
        
        def hh_state(element, state, increment):
            return ([element+state, element*state], state+increment)
        
        rr_state = Stream(name='rr_state')
        tt_state = Stream(name='tt_state')
        in_stream_split_state_funcargs = Stream('in_stream_split_state_funcargs')

        ee_state_agent = split_element(
            func=hh_state,
            in_stream=in_stream_split_state_funcargs,
            out_streams=[rr_state, tt_state],
            name='ee_state_agent', state=0, increment=10)

        scheduler.step()
        assert recent_values(rr_state) == []
        assert recent_values(tt_state) == []

        in_stream_split_state_funcargs.extend(list(range(5)))
        scheduler.step() 
        assert recent_values(rr_state) == [0, 11, 22, 33, 44]
        assert recent_values(tt_state) == [0, 10, 40, 90, 160]

    #------------------------------------------------------------------------------------------------
    #                                     UNZIP AGENT TESTS
    #------------------------------------------------------------------------------------------------

        s_unzip = Stream('s_unzip')
        u_unzip = Stream('u_unzip')
        x_unzip = Stream('x_unzip')
     
        # ------------------------------------
        # Test unzip
        unzip(in_stream=s_unzip, out_streams=[x_unzip, u_unzip])
        d_unzip_fn = unzip_f(s_unzip, 2) 
     
     
        s_unzip.extend([(1,10), (2,15), (3,18)])
        scheduler.step()
        assert recent_values(x_unzip) == [1, 2, 3]
        assert recent_values(u_unzip) == [10, 15, 18]
        assert recent_values(d_unzip_fn[0]) == x_unzip.recent[:3]
        assert recent_values(d_unzip_fn[1]) == u_unzip.recent[:3]
     
        s_unzip.extend([(37,96)])
        scheduler.step()
        assert recent_values(x_unzip) == [1, 2, 3, 37]
        assert recent_values(u_unzip) == [10, 15, 18, 96]
        assert recent_values(d_unzip_fn[0]) == x_unzip.recent[:4]
        assert recent_values(d_unzip_fn[1]) == u_unzip.recent[:4]


        #------------------------------------------------------------------------------------------------
        #                                     SEPARATE AGENT TESTS
        #------------------------------------------------------------------------------------------------
        s_separate = Stream('s separate')
        u_separate = Stream('u separate')
        x_separate = Stream('x separate')

        d_separate = separate(
            in_stream=s_separate, out_streams=[x_separate,u_separate],
            name='d separate')
        x_sep_func, u_sep_func = separate_f(s_separate, 2)

        s_separate.extend([(0,10), (1,15), (0,20)])
        scheduler.step()
        assert recent_values(x_separate) == [10, 20]
        assert recent_values(u_separate) == [15]
        assert x_sep_func.recent == x_separate.recent
        assert u_sep_func.recent == u_separate.recent

        s_separate.extend([(1,96)])
        scheduler.step()
        assert recent_values(x_separate) == [10, 20]
        assert recent_values(u_separate) == [15, 96]
        assert recent_values(x_sep_func) == recent_values(x_separate)
        assert recent_values(u_sep_func) == recent_values(u_separate)

        #------------------------------------------------------------------------------------------------
        #                                     TIMED_UNZIP TESTS
        #------------------------------------------------------------------------------------------------
        # timed_unzip tests
        t_unzip = Stream()
        a_unzip = Stream('a_unzip')
        b_unzip = Stream('b_unzip')

        timed_unzip(t_unzip, [a_unzip, b_unzip])
        t_unzip_0, t_unzip_1 = timed_unzip_f(in_stream=t_unzip, num_out_streams=2)

        t_unzip.extend(
            [(1, ["A", None]), (5, ["B", "a"]), (7, [None, "b"]),
             (9, ["C", "c"]), (10, [None, "d"])])

        
        scheduler.step()
        assert recent_values(t_unzip_0) == [(1, 'A'), (5, 'B'), (9, 'C')]
        assert recent_values(t_unzip_1) == [(5, 'a'), (7, 'b'), (9, 'c'), (10, 'd')]
        assert recent_values(a_unzip) == recent_values(t_unzip_0)
        assert recent_values(b_unzip) == recent_values(t_unzip_1)


        #------------------------------------------------------------------------------------------------
        #                               TEST SPLIT WITH STREAM_ARRAY
        #------------------------------------------------------------------------------------------------
        # Test split_element with StreamArray
        x = StreamArray('x')
        y = StreamArray('y')
        z = StreamArray('z')

        def h_args(element, addend, multiplier):
                return [element+addend, element*multiplier]

        this_agent = split_element(func=h_args, in_stream=x, out_streams=[y,z],
                                         addend=1.0 , multiplier=2.0, name='this_agent')

        add_to_x = np.linspace(0.0, 4.0, 5)
        x.extend(add_to_x)
        scheduler.step()
        assert np.array_equal(recent_values(y), add_to_x+1.0)
        assert np.array_equal(recent_values(z), add_to_x*2.0)

        # Test separate with StreamArray
        x = StreamArray('x', dimension=2)
        y = StreamArray('y')
        z = StreamArray('z')

        separate(x, [y,z])
        x.append(np.array([1.0, 10.0]))
        scheduler.step()
        assert np.array_equal(recent_values(z), np.array([10.0]))
        assert np.array_equal(recent_values(y), np.array([]))

        x.extend(np.array([[0.0, 2.0], [1.0, 20.0], [0.0, 4.0]]))
        scheduler.step()
        assert np.array_equal(recent_values(z), np.array([10.0, 20.0]))
        assert np.array_equal(recent_values(y), np.array([2.0, 4.0]))

        # ------------------------------------------------------
        # TEST split_list
        # ------------------------------------------------------
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')

        def f(lst):
            return [v*2 for v in lst], [v*10 for v in lst]

        split_list(f, x, [y, z])

        x.extend(list(range(3)))
        scheduler.step()
        assert recent_values(y) == [v*2 for v in recent_values(x)]
        assert recent_values(z) == [v*10 for v in recent_values(x)]

        x.append(100)
        scheduler.step()
        assert recent_values(y) == [v*2 for v in recent_values(x)]
        assert recent_values(z) == [v*10 for v in recent_values(x)]
        

        # ------------------------------------------------------
        # TEST split_window
        # ------------------------------------------------------
        def f(window):
            return max(window), min(window)

        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        
        split_window(
            func=f, in_stream=x, out_streams=[y, z], window_size=2, step_size=2)

        x.extend(list(range(7)))
        scheduler.step()
        assert recent_values(y) == [1, 3, 5]
        assert recent_values(z) == [0, 2, 4]

        
        def f(window):
            return max(window), min(window)

        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        
        split_window(
            func=f, in_stream=x, out_streams=[y, z], window_size=3, step_size=3)

        x.extend(list(range(12)))
        scheduler.step()
        assert recent_values(y) == [2, 5, 8, 11]
        assert recent_values(z) == [0, 3, 6, 9]

        # ------------------------------------------------------
        # TEST split_tuple
        # ------------------------------------------------------
        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        split_tuple(in_stream=x, out_streams=[y, z])
        x.append((0, 'A'))
        x.extend([(1, 'B'), (2, 'C')])
        scheduler.step()
        assert recent_values(y) == [0, 1, 2]
        assert recent_values(z) == ['A', 'B', 'C']
        

        def f(window):
            return max(window), min(window)

        x = Stream('x')
        y = Stream('y')
        z = Stream('z')
        
        split_window(
            func=f, in_stream=x, out_streams=[y, z], window_size=3, step_size=3)

        x.extend(list(range(12)))
        scheduler.step()
        assert recent_values(y) == [2, 5, 8, 11]
        assert recent_values(z) == [0, 3, 6, 9]

    def test_split_with_basics(self):
        #----------------------------------------------
        # EXAMPLE: SIMPLE SPLIT
        # Split a stream into a list of streams. In this
        # example, a stream (s) is split into two streams:
        # u and v.
        # Decorate a conventional function to get a
        # stream function. This function returns a list
        # of two values corresponding to the two output
        # streams.
        @split_e
        def h(x):
            return [2*x, x+1000]

        # Create streams.
        s = Stream()
        u = Stream()
        v = Stream()

        # Create agents by calling the decorated function.
        h(s, [u,v])

        # Put data into input streams.
        DATA = list(range(5))
        s.extend(DATA)

        # Run the agents.
        run()

        # Check values of output streams.
        assert recent_values(u) == [2*x for x in DATA]
        assert recent_values(v) == [x+1000 for x in DATA]

        #----------------------------------------------
        # EXAMPLE: SPLIT WITH KEYWORD ARGUMENT
        # Split a stream into a list of streams. Use
        # a keyword argument in the splitting function.
        # Decorate a conventional function to get a
        # stream function. This function returns a list
        # of two values corresponding to the two output
        # streams. addend is a keyword argument in the
        # function that creates agents.
        @split_e
        def h(x, addend):
            return [x+addend, x+1000+addend]

        # Create streams.
        s = Stream()
        u = Stream()
        v = Stream()
        # Call decorated function.
        ADDEND=10
        h(s, [u,v], addend=ADDEND)
        # Put data into input streams.
        s.extend(DATA)
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == [x+ADDEND for x in DATA]
        assert recent_values(v) == [x+1000+ADDEND for x in DATA]

        #----------------------------------------------
        # EXAMPLE: SPLIT WITH KEYWORD ARGUMENT AND STATE
        # Split a stream into a list of streams, with
        # a keyword argument and state.
        # Decorate a conventional function to get a
        # stream function. addend and multiplicand are
        # keyword arguments used in the call to create
        # agents. The function h returns 2 values:
        # (1) a list of two numbers corresponding to the
        #     two output streams and
        # (2) the next state.
        @split_e
        def h(v, state, addend, multiplicand):
            next_state = state + 2
            return ([v+addend+state, v*multiplicand+state],
                    next_state)

        # Create streams.
        s = Stream()
        u = Stream()
        v = Stream()

        # Call decorated function to create agents. The initial state
        # is 0. Include keyword arguments in the call.
        ADDEND = 10
        MULTIPLICAND = 2
        h(s, [u,v], state=0, addend=ADDEND, multiplicand=MULTIPLICAND)

        # Put data into input streams.
        s.extend(DATA)

        # Run the agent.
        run()

        # Check values of output streams.
        assert recent_values(u) == [10, 13, 16, 19, 22]
        assert recent_values(v) == [0, 4, 8, 12, 16]

        #----------------------------------------------
        # EXAMPLE: SPLIT WITH STATE AND NO KEYWORD ARGUMENTS
        # Split a stream into a list of streams, with
        # a state.
        # Decorate a conventional function to get a
        # stream function. This function returns two values
        # a list and the next state, where the list has two
        # values with one value for each output streams.
        @split_e
        def h(v, state):
            next_state = state + 1
            return [v+state, v+1000+state], next_state

        # Create streams.
        s = Stream()
        u = Stream()
        v = Stream()

        # Call decorated function to create agents.
        h(in_stream=s, out_streams=[u,v], state=0)
        # Put data into input streams.
        s.extend(DATA)

        # Run the decorated function.
        run()

        # Check values of output streams.
        assert recent_values(u) == [0, 2, 4, 6, 8]
        assert recent_values(v) == [1000, 1002, 1004, 1006, 1008]

        #----------------------------------------------
        # EXAMPLE: SPLIT USING FUNCTIONAL FORM FOR
        # SPLITTING A STREAM INTO 2 STREAMS.
        # Split a stream into exactly two streams.
        # This is in functional form, i.e. it creates
        # and returns two streams.
        # Decorate a conventional function to get a
        # stream function.
        @fsplit_2e
        def h(v):
            return [v, v+1000]

        # Create streams.
        s = Stream()

        # Call decorated function to create agents
        # Note that h creates streams u, v. It creates
        # 2 streams because the decorator is fsplit_2e 
        u, v = h(s)
        # Put data into input streams.
        s.extend(DATA)
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == DATA
        assert recent_values(v) == [1000+x for x in DATA]

        #----------------------------------------------
        # EXAMPLE: SPLIT USING FUNCTIONAL FORM FOR
        # SPLITTING A STREAM INTO 2 STREAMS.
        # Split a stream into exactly two streams, with a
        # keyword argument. This is in functional 
        # form, i.e. it creates and returns two streams.
        # Decorate a conventional function to get a
        # stream function.
        @fsplit_2e
        def h(v, addend):
            return [v+addend, v+1000+addend]

        # Create streams.
        s = Stream()

        # Call decorated function to create agents. Note
        # functional form.
        u, v = h(s, addend=10)

        # Put data into input streams.
        s.extend(DATA)

        # Run the agents.
        run()

        # Check values of output streams.
        assert recent_values(u) == [10, 11, 12, 13, 14]
        assert recent_values(v) == [1010, 1011, 1012, 1013, 1014]

        #----------------------------------------------
        # EXAMPLE: FUNCTIONAL FORM
        # Split a stream into exactly two streams, with a
        # state and keyword argument. This is in functional 
        # form, i.e. it creates and returns two streams.
        # Decorate a conventional function to get a
        # stream function.
        @fsplit_2e
        def h(v, state, addend):
            next_state = state + 1
            return ([v+addend+state, v+1000+addend+state],
                    next_state)
        # Create streams.
        s = Stream()
        # Call decorated function.
        u, v = h(s, state=0, addend=10)
        # Put data into input streams.
        s.extend(list(range(5)))
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == [10, 12, 14, 16, 18]
        assert recent_values(v) == [1010, 1012, 1014, 1016, 1018]

        #----------------------------------------------
        # Split a stream into exactly two streams, with a
        # state. This is in functional form,
        # i.e. it creates and returns two streams.
        # Decorate a conventional function to get a
        # stream function.
        @fsplit_2e
        def hk(v, state):
            next_state = state + 1
            return [v+state, v+1000+state], next_state
        # Create streams.
        s = Stream()
        # Call decorated function.
        u, v = h(s, state=0, addend=10)
        u, v = hk(s, state=0)
        # Put data into input streams.
        s.extend(list(range(5)))
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == [0, 2, 4, 6, 8]
        assert recent_values(v) == [1000, 1002, 1004, 1006, 1008]

        #----------------------------------------------
        # Split a stream into a list of streams.
        # Window operation
        # Decorate a conventional function to get a
        # stream function.
        @split_w
        def h(window):
            return [sum(window), max(window)]
        # Create streams.
        s = Stream()
        u = Stream()
        v = Stream()
        # Call decorated function.
        h(s, [u,v], window_size=3, step_size=2)
        # Put data into input streams.
        s.extend(list(range(12)))
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == [3, 9, 15, 21, 27]
        assert recent_values(v) == [2, 4, 6, 8, 10]

        #----------------------------------------------
        # Split a stream into a list of streams with
        # keyword argument. Window operation
        # Decorate a conventional function to get a
        # stream function.
        @split_w
        def h(window, addend):
            return [sum(window)+addend, max(window)+addend]

        # Create streams.
        s = Stream()
        u = Stream()
        v = Stream()

        # Call decorated function to create agents.
        h(s, [u,v], window_size=3, step_size=2, addend=1000)

        # Put data into input streams.
        s.extend(list(range(12)))

        # Run the agents.
        run()

        # Check values of output streams.
        assert recent_values(u) == [1003, 1009, 1015, 1021, 1027]
        assert recent_values(v) == [1002, 1004, 1006, 1008, 1010]

        #----------------------------------------------
        # Split a stream into a list of streams with state and
        # keyword argument. Window operation
        # Decorate a conventional function to get a
        # stream function.
        @split_w
        def h(window, state, addend):
            next_state = state + 1
            return ([sum(window)+addend+state,
                    max(window)+addend+state], next_state)
        # Create streams.
        s = Stream()
        u = Stream()
        v = Stream()
        # Call decorated function.
        h(s, [u,v], window_size=3, step_size=2, state=0, addend=1000)
        # Put data into input streams.
        s.extend(list(range(12)))
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == [1003, 1010, 1017, 1024, 1031]
        assert recent_values(v) == [1002, 1005, 1008, 1011, 1014]

        #----------------------------------------------
        #       SPLITTING WITH WINDOWS
        #----------------------------------------------
        # EXAMPLE
        # Split a stream into a list of streams with state.
        # Window operation
        # Decorate a conventional function to get a
        # stream function. The first argument of the function
        # is a list, i.e., the window. The function returns
        # two values: a list and the next state where the list
        # has one item for eah output stream.
        @split_w
        def h(window, state):
            next_state = state + 1
            return [sum(window)+state, max(window)+state], next_state

        # Create streams.
        s = Stream()
        u = Stream()
        v = Stream()

        # Call decorated function to create agents.
        h(s, [u,v], window_size=3, step_size=2, state=0)

        # Put data into input streams.
        s.extend(list(range(12)))

        # Run the agents.
        run()

        # Check values of output streams.
        assert recent_values(u) == [3, 10, 17, 24, 31]
        assert recent_values(v) == [2, 5, 8, 11, 14]

        #----------------------------------------------
        # Split a stream into exactly TWO streams.
        # WINDOW operation
        # Decorate a conventional function to get a
        # stream function. This is in functional form,
        # i.e. it creates and returns a list of streams.
        @fsplit_2w
        def h(window):
            return sum(window), max(window)
        # Create streams.
        s = Stream()
        # Call decorated function. This function
        # creates and returns two streams.
        u, v = h(s, window_size=3, step_size=2)
        # Put data into input streams.
        s.extend(list(range(12)))
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == [3, 9, 15, 21, 27]
        assert recent_values(v) == [2, 4, 6, 8, 10]

        #----------------------------------------------
        # Split a stream into exactly two streams with 
        # keyword argument. Window operation
        # Decorate a conventional function to get a
        # stream function. This is in functional form,
        # i.e. it creates and returns two streams.
        @fsplit_2w
        def h(window, addend):
            return sum(window)+addend, max(window)+addend*2
        # Create streams.
        s = Stream()
        # Call decorated function. This function
        # creates and returns two streams.
        u, v = h(s, window_size=3, step_size=2, addend=1000)
        # Put data into input streams.
        s.extend(list(range(12)))
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == [1003, 1009, 1015, 1021, 1027]
        assert recent_values(v) == [2002, 2004, 2006, 2008, 2010]


        #----------------------------------------------
        # Split a stream into exactly two streams with 
        # state and keyword argument. Window operation
        # Decorate a conventional function to get a
        # stream function. This is in functional form,
        # i.e. it creates and returns two streams.
        @fsplit_2w
        def h(window, state, addend):
            next_state = state + 1
            return ([sum(window)+addend+state,
                    max(window)+addend*2-state], next_state)
        # Create streams.
        s = Stream()
        # Call decorated function. This function
        # creates and returns two streams.
        u, v = h(s, window_size=3, step_size=2,
                 state=0, addend=1000)
        # Put data into input streams.
        s.extend(list(range(12)))
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == [1003, 1010, 1017, 1024, 1031]
        assert recent_values(v) == [2002, 2003, 2004, 2005, 2006]

        #----------------------------------------------
        # Split a stream into exactly two streams with 
        # state. Window operation
        # Decorate a conventional function to get a
        # stream function. This is in functional form,
        # i.e. it creates and returns two streams.
        @fsplit_2w
        def h(window, state):
            next_state = state + 1
            return [sum(window)+state, max(window)-state], next_state
        # Create streams.
        s = Stream()
        # Call decorated function. This function
        # creates and returns two streams.
        u, v = h(s, window_size=3, step_size=2, state=0)
        # Put data into input streams.
        s.extend(list(range(12)))
        # Run the decorated function.
        run()
        # Check values of output streams.
        assert recent_values(u) == [3, 10, 17, 24, 31]
        assert recent_values(v) == [2, 3, 4, 5, 6]
        print ('success')


    

if __name__ == '__main__':
    unittest.main()    
    
    
    
    
    
    

