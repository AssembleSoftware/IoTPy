"""
This module has the basic decorators of IoTPy

"""
import numpy as np

import sys
sys.path.append("../../IoTPy/core")
sys.path.append("../../IoTPy/agent_types")
sys.path.append("../../IoTPy/helper_functions")

# agent and stream are in IoTPy/IoTPy/core
from stream import Stream, run
# recent_values is in IoTPy/IoTPy/helper_functions
from recent_values import recent_values
# basics is in IoTPy/IoTPy/agent_types
from basics import merge_e, fmerge_e, merge_asynch
from basics import fmerge_2e, fmerge_w, fmerge_2w


def examples_merge():
    #----------------------------------------------
    # Simple merge of list of streams.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_e
    def sum_stream(l):
        # l is a list.
        return sum(l)
    # Create streams.
    x = Stream('X')
    y = Stream('Y')
    # Call decorated function.
    t = sum_stream([x, y])
    # Put data into input streams.
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(t) == [
       100, 102, 104, 106, 108,
       110, 112, 114, 116, 118]

    #----------------------------------------------
    # Merge list of streams with keyword argument.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_e
    def h(l, addend):
        # l is a list.
        return sum(l) + addend
    # Create streams.
    x = Stream('X')
    y = Stream('Y')
    # Call decorated function.
    t = h([x, y], addend=1000)
    # Put data into input streams.
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(t) == [
        1100, 1102, 1104, 1106, 1108,
        1110, 1112, 1114, 1116, 1118]

    #----------------------------------------------
    # Merge list of streams with keyword argument
    # and state.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_e
    def h(l, state, addend):
        # l is a list.
        next_state = state + 1
        return sum(l) + addend + state, next_state
    # Create streams.
    x = Stream('X')
    y = Stream('Y')
    # Call decorated function.
    t = h([x, y], state=0, addend=1000)
    # Put data into input streams
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(t) == [
        1100, 1103, 1106, 1109, 1112,
        1115, 1118, 1121, 1124, 1127]

    #----------------------------------------------
    # Merge list of streams with state.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_e
    def h(l, state):
        # l is a list.
        next_state = state + 1
        return sum(l) + state, next_state
    # Create streams.
    x = Stream('X')
    y = Stream('Y')
    # Call decorated function.
    t = h([x, y], state=0)
    # Put data into input streams
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(t) == [
        100, 103, 106, 109, 112, 115,
        118, 121, 124, 127]

    #----------------------------------------------
    # Asynchonous merge.
    # Decorate a conventional function to get a
    # stream function.
    @merge_asynch
    def h(v):
        # v is an argument of any input stream.
        return 2*v
    # Create streams.
    x = Stream('X')
    y = Stream('Y')
    # Call decorated function.
    h([x, y], t)
    # Put data into input streams.
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    # Run the decorated function.
    run()
    # Print contents of output streams.
    #print recent_values(t)

    #----------------------------------------------
    # Asynchonous merge with state.
    # Decorate a conventional function to get a
    # stream function.
    @merge_asynch
    def h(v, state):
        next_state = state+1
        return 2*v+state, next_state
    # Create streams.
    x = Stream('x')
    y = Stream('y')
    # Call decorated function.
    h([x, y], t, state=0)
    # Put data into input streams.
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    # Run the decorated function.
    run()
    #print recent_values(t)

    #----------------------------------------------
    # Asynchonous merge with keyword parameter.
    @merge_asynch
    def h(v, addend):
        return 2*v + addend
    # Create streams.
    x = Stream('X')
    y = Stream('Y')
    # Call decorated function.
    h([x, y], t, addend=1000)
    # Put data into input streams.
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    # Run the decorated function.
    run()
    #print recent_values(t)

    #----------------------------------------------
    # Merge two streams.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_2e
    def h(x,y):
        # x,y are elements of the two input streams.
        return x+2*y
    # Create streams.
    x = Stream()
    y = Stream()
    # Call decorated function.
    t = h(x, y)
    # Put data into input streams.
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(t) == [
        200, 203, 206, 209, 212, 215,
        218, 221, 224, 227]

    #----------------------------------------------
    # Merge two streams with keyword parameters.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_2e
    def h(x, y, addend):
        # x,y are elements of the two input streams.
        return x+2*y + addend
    x = Stream()
    y = Stream()
    t = h(x, y, addend=1000)
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    run()
    assert recent_values(t) == [
        1200, 1203, 1206, 1209, 1212, 1215,
        1218, 1221, 1224, 1227]

    #----------------------------------------------
    # Merge two streams with keyword parameters and
    # state.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_2e
    def h(x, y, state, addend):
        # x,y are elements of the two input streams.
        next_state = state + 1
        return x+2*y + addend + state, next_state
    x = Stream()
    y = Stream()
    t = h(x, y, state= 0, addend=1000)
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    run()
    assert recent_values(t) == [
        1200, 1204, 1208, 1212, 1216,
        1220, 1224, 1228, 1232, 1236]

    #----------------------------------------------
    # Merge two streams with state.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_2e
    def h(x, y, state):
        # x,y are elements of the two input streams.
        next_state = state + 1
        return x+2*y + state, next_state
    x = Stream()
    y = Stream()
    t = h(x, y, state= 0)
    x.extend(list(range(10)))
    y.extend(list(range(100, 120)))
    run()
    assert recent_values(t) == [
        200, 204, 208, 212, 216,
        220, 224, 228, 232, 236]


    #----------------------------------------------
    # Merge list of streams: window operation.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_w
    def h(list_of_windows):
        window_0, window_1 = list_of_windows
        return sum(window_0) + 2*sum(window_1)
    # Create streams.
    x = Stream()
    y = Stream()
    # Call decorated function.
    in_streams = [x, y]
    t = h(in_streams, window_size=2, step_size=2)
    # Put data into input streams.
    x.extend(list(range(20)))
    y.extend(list(range(100, 120)))
    # Run the decorated function.
    run()
    # Check values of output streams.
    assert recent_values(t) == [
        403, 415, 427, 439, 451, 463,
        475, 487, 499, 511]


    #----------------------------------------------
    # Merge list of streams with keyword argument:
    # window operation.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_w
    def h(list_of_windows, addend):
        window_0, window_1 = list_of_windows
        return sum(window_0) + 2*sum(window_1) + addend
    x = Stream()
    y = Stream()
    in_streams = [x, y]
    t = h(in_streams, window_size=2, step_size=2, addend=1000)

    x.extend(list(range(20)))
    y.extend(list(range(100, 120)))
    
    Stream.scheduler.step()
    assert recent_values(t) == [
        1403, 1415, 1427, 1439, 1451, 1463,
        1475, 1487, 1499, 1511]

    #----------------------------------------------
    # Merge list of streams with state and keyword argument:
    # window operation.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_w
    def h(list_of_windows, state, addend):
        next_state = state + 1
        window_0, window_1 = list_of_windows
        return sum(window_0) + 2*sum(window_1) + addend + state, next_state
    x = Stream()
    y = Stream()
    in_streams = [x, y]
    t = h(in_streams, window_size=2, step_size=2, state=0, addend=1000)
    x.extend(list(range(20)))
    y.extend(list(range(100, 120)))
    run()
    assert recent_values(t) == [
        1403, 1416, 1429, 1442, 1455,
        1468, 1481, 1494, 1507, 1520]

    #----------------------------------------------
    # Merge list of streams with state:
    # window operation.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_w
    def h(list_of_windows, state):
        next_state = state + 1
        window_0, window_1 = list_of_windows
        return sum(window_0) + 2*sum(window_1) + state, next_state
    x = Stream()
    y = Stream()
    in_streams = [x, y]
    t = h(in_streams, window_size=2, step_size=2, state=0)
    x.extend(list(range(20)))
    y.extend(list(range(100, 120)))
    run()
    assert recent_values(t) == [
        403, 416, 429, 442, 455, 468, 481, 494, 507, 520]

    #----------------------------------------------
    # Merge two streams: window operation.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_2w
    def h(window_x, window_y):
        return sum(window_x) + 2*sum(window_y)
    x = Stream()
    y = Stream()
    t = h(x, y, window_size=2, step_size=2)
    x.extend(list(range(20)))
    y.extend(list(range(100, 120)))
    run()
    assert recent_values(t) == [
        403, 415, 427, 439, 451, 463,
        475, 487, 499, 511]

    #----------------------------------------------
    # Merge two streams with keyword argument:
    # window operation.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_2w
    def h(window_0, window_1, addend):
        return sum(window_0) + 2*sum(window_1) + addend
    x = Stream()
    y = Stream()
    in_streams = [x, y]
    t = h(x, y, window_size=2, step_size=2, addend=1000)
    x.extend(list(range(20)))
    y.extend(list(range(100, 120)))
    run()
    assert recent_values(t) == [
        1403, 1415, 1427, 1439, 1451, 1463,
        1475, 1487, 1499, 1511]

    #----------------------------------------------
    # Merge two streams with state and keyword argument:
    # window operation.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_2w
    def h(window_0, window_1, state, addend):
        next_state = state + 1
        return ((sum(window_0) + 2*sum(window_1) +
                 addend + state), next_state)
    x = Stream()
    y = Stream()
    in_streams = [x, y]
    t = h(x, y, window_size=2, step_size=2, state=0, addend=1000)
    x.extend(list(range(20)))
    y.extend(list(range(100, 120)))
    run()
    assert recent_values(t) == [
        1403, 1416, 1429, 1442, 1455,
        1468, 1481, 1494, 1507, 1520]

    #----------------------------------------------
    # Merge two streams with state:
    # window operation.
    # Decorate a conventional function to get a
    # stream function.
    @fmerge_2w
    def h(window_0, window_1, state):
        next_state = state + 1
        return sum(window_0) + 2*sum(window_1) + state, next_state
    x = Stream()
    y = Stream()
    in_streams = [x, y]
    t = h(x, y, window_size=2, step_size=2, state=0)
    x.extend(list(range(20)))
    y.extend(list(range(100, 120)))
    run()
    assert recent_values(t) == [
        403, 416, 429, 442, 455, 468,
        481, 494, 507, 520]

if __name__ == '__main__':
    examples_merge()
