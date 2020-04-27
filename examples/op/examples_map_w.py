"""
This module has examples of @map_e and @fmap_e

"""
import sys
sys.path.append("../../IoTPy/core")
sys.path.append("../../IoTPy/agent_types")
sys.path.append("../../IoTPy/helper_functions")

# stream, helper_control are in IoTPy/IoTPy/core
from stream import Stream, _no_value, _multivalue, run
from helper_control import _no_value, _multivalue
# basics in in IoTPy/IoTPy/agent_types
from basics import map_e, fmap_e, map_w, fmap_w
# recent_values is in IoTPy/IoTPy/helper_functions
from recent_values import recent_values

def examples():
    #-----------------------------------------------
    # Example with @fmap_w and @map_w
    @fmap_w
    def sum_window(window): return sum(window)
    @map_w
    def total_window(window): return sum(window)

    r = Stream()
    s = Stream()
    t = sum_window(r, window_size=2, step_size=2)
    total_window(in_stream=r, out_stream=s, window_size=2, step_size=2)
    
    r.extend(list(range(10)))
    run()
    assert recent_values(t) == [1, 5, 9, 13, 17]
    assert recent_values(t) == recent_values(s)

    #-----------------------------------------------
    # Example with keyword argument
    @fmap_w
    def sum_add(v, addend): return sum(v) + addend

    s = Stream()
    t = sum_add(s, window_size=2, step_size=2, addend=10)
    s.extend(list(range(10)))
    Stream.scheduler.step()
    assert recent_values(t) == [11, 15, 19, 23, 27]

    # Example with keyword argument using map_w
    @map_w
    def sum_add_relation(v, addend): return sum(v) + addend

    s = Stream()
    t = Stream()
    sum_add_relation(s, t, window_size=2, step_size=2, addend=10)
    s.extend(list(range(10)))
    Stream.scheduler.step()
    assert recent_values(t) == [11, 15, 19, 23, 27]

    #-----------------------------------------------
    # Example with state and keyword argument
    @fmap_w
    def h(v, state, addend):
        next_state = state + 1
        return sum(v) + state + addend, next_state

    s = Stream()
    t = h(s, window_size=2, step_size=2, state= 0, addend=10)
    s.extend(list(range(10)))
    run()
    assert recent_values(t) == [11, 16, 21, 26, 31]

    #-----------------------------------------------
    # Output stream is the average of the max of
    # successive windows
    @fmap_w
    def h(window, state):
        count, total = state
        next_total = total + max(window)
        next_count = count+1
        next_output = next_total/next_count
        next_state = next_count, next_total
        return next_output, next_state

    s = Stream()
    t = h(s, window_size=4, step_size=4, state=(0,0.0))
    s.extend(list(range(20)))
    run()
    assert recent_values(t) == [3.0, 5.0, 7.0, 9.0, 11.0]    
    return

if __name__ == '__main__':
    examples()
