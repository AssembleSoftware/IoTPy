"""
This module has the basic decorators of IoTPy

"""
import numpy as np

from ..core.stream import Stream, StreamArray, _multivalue, run
from ..core.agent import Agent
from ..core.helper_control import _no_value, _multivalue
# agent, stream, helper_control are in ../core

from ..helper_functions.recent_values import recent_values
# recent_values is in ../helper_functions

from .op import map_element, map_element_f
from .op import filter_element, filter_element_f
from .op import map_list, map_list_f, timed_window
from .op import map_window_f, map_window, map_window_list
from .merge import zip_map, zip_map_f, merge_window_f, blend_f, blend
from .merge import merge_window
from .split import split_element_f, split_window_f, split_element
from .split import split_element, split_window
from .multi import multi_element_f, multi_window_f, multi_element, multi_window
from .sink import sink_element, sink_window
# op, merge, split, multi, sink are in the current directory


#------------------------------------------------------------
#       WRAPPERS FOR DECORATORS
#------------------------------------------------------------

#-------------------------------------------------------------------
# map_element
#-------------------------------------------------------------------
def fmap_e(func):
    def wrapper(**kwargs):
        def g(s, **kwargs):
            return map_element_f(func, s, **kwargs)
        return g
    return wrapper()

def map_e(func):
    def wrapper(**kwargs):
        def g(in_stream, out_stream, **kwargs):
            map_element(func, in_stream, out_stream, **kwargs)
            return out_stream
        return g
    return wrapper()


#-------------------------------------------------------------------
# map_list
#-------------------------------------------------------------------
def fmap_l(func):
    def wrapper(**kwargs):
        def g(s, **kwargs):
            return map_list_f(func, s, **kwargs)
        return g
    return wrapper()

def map_l(func):
    def wrapper(**kwargs):
        def g(in_stream, out_stream, **kwargs):
            map_list(func, in_stream, out_stream, **kwargs)
            return out_stream
        return g
    return wrapper()

#-------------------------------------------------------------------
# map_window
#-------------------------------------------------------------------
def fmap_w(func):
    def wrapper(**kwargs):
        def g(in_stream, window_size, step_size, **kwargs):
            return map_window_f(func, in_stream, window_size, step_size, **kwargs)
        return g
    return wrapper()

def map_w(func):
    def wrapper(**kwargs):
        def g(in_stream, out_stream, window_size, step_size, **kwargs):
            return map_window(func, in_stream, out_stream,
                                window_size, step_size, **kwargs)
        return g
    return wrapper()

#-------------------------------------------------------------------
# map_window_list
#-------------------------------------------------------------------
def map_wl(func):
    def wrapper(**kwargs):
        def g(in_stream, out_stream, window_size, step_size, **kwargs):
            return map_window_list(func, in_stream, out_stream,
                                   window_size, step_size, **kwargs)
        return g
    return wrapper()

def fmap_wl(func):
    def wrapper(**kwargs):
        def g(in_stream, window_size, step_size, **kwargs):
            return map_window_list_f(func, in_stream, window_size, step_size, **kwargs)
        return g
    return wrapper()

#-------------------------------------------------------------------
# merge_element: same as zip_map
#-------------------------------------------------------------------
def fmerge_e(func):
    def wrapper(**kwargs):
        def g(in_streams, **kwargs):
            return zip_map_f(func, in_streams, **kwargs)
        return g
    return wrapper()

def merge_e(func):
    def wrapper(**kwargs):
        def g(in_streams, out_stream, **kwargs):
            return zip_map(func, in_streams, out_stream, **kwargs)
        return g
    return wrapper()

def merge_sink_e(func):
    def wrapper(**kwargs):
        def g(in_streams, **kwargs):
            out_stream = Stream('discard')
            zip_map(func, in_streams, out_stream, **kwargs)
        return g
    return wrapper()

#-------------------------------------------------------------------
# merge_asynch
#-------------------------------------------------------------------

def merge_asynch(func):
    def wrapper(**kwargs):
        def g(in_streams, out_stream, **kwargs):
            return blend(func, in_streams, out_stream, **kwargs)
        return g
    return wrapper()

#-------------------------------------------------------------------
# merge_2e merge 2 elements. 
#-------------------------------------------------------------------
def fmerge_2e(func):
    def wrapper(**kwargs):
        def g(x, y, state=None, **kwargs):
            in_streams = [x, y]
            if state is None:
                def h_fmerge_2e(pair, **kwargs):
                    return func(pair[0], pair[1], **kwargs)
                return zip_map_f(h_fmerge_2e, in_streams, **kwargs)
            else:
                def h_fmerge_2e(pair, state, **kwargs):
                    return func(pair[0], pair[1], state, **kwargs)
                return zip_map_f(h_fmerge_2e, in_streams, state, **kwargs)
        return g
    return wrapper()
        

def fmerge_w(func):
    def wrapper(**kwargs):
        def g(in_streams, window_size, step_size, state=None, **kwargs):
            if state is None:
                return merge_window_f(
                    func, in_streams, window_size, step_size, **kwargs)
            else:
                return merge_window_f(
                    func, in_streams, window_size, step_size, state, **kwargs)
        return g
    return wrapper()

#-------------------------------------------------------------------
# merge_window
#-------------------------------------------------------------------
def merge_w(func):
    def wrapper(**kwargs):
        def g(in_streams, out_stream, window_size, step_size, state=None, **kwargs):
            if state is None:
                return merge_window(
                    func, in_streams, out_stream, window_size, step_size, **kwargs)
            else:
                return merge_window(
                    func, in_streams, out_stream, window_size, step_size, state, **kwargs)
        return g
    return wrapper()

def fmerge_2w(func):
    def wrapper(**kwargs):
        def g(in_stream_0, in_stream_1, window_size, step_size, state=None, **kwargs):
            in_streams = [in_stream_0, in_stream_1]
            if state is None:
                def h(v, **kwargs):
                    return func(v[0], v[1], **kwargs)
                return merge_window_f(
                    h, in_streams, window_size, step_size, **kwargs)
            else:
                def h(v, state, **kwargs):
                    return func(v[0], v[1], state, **kwargs)
                return merge_window_f(
                    h, in_streams, window_size, step_size, state, **kwargs)
        return g
    return wrapper()

#-------------------------------------------------------------------
# split_element
#-------------------------------------------------------------------
def split_e(func):
    def wrapper(**kwargs):
        def g(in_stream, out_streams, state=None, **kwargs):
            if state is None:
                return split_element(func, in_stream, out_streams, **kwargs)
            else:
                return split_element(func, in_stream, out_streams, state, **kwargs)
        return g
    return wrapper()


def fsplit_2e(func):
    def wrapper(**kwargs):
        def g(v, **kwargs):
            num_out_streams=2
            return split_element_f(func, v, num_out_streams, **kwargs)
        return g
    return wrapper()

#-------------------------------------------------------------------
# split_window
#-------------------------------------------------------------------
def split_w(func):
    def wrapper(**kwargs):
        def g(in_streams,  out_streams, window_size, step_size, state=None, **kwargs):
            if state is None:
                return split_window(
                    func, in_streams, out_streams,
                    window_size, step_size, **kwargs)
            else:
                return split_window(
                    func, in_streams, out_streams,
                    window_size, step_size, state, **kwargs)
                
        return g
    return wrapper()

#-------------------------------------------------------------------
# split_window into 2 streams
#-------------------------------------------------------------------
def fsplit_2w(func):
    def wrapper(**kwargs):
        def g(in_streams, window_size, step_size, **kwargs):
            num_out_streams = 2
            return split_window_f(
                func, in_streams, num_out_streams,
                window_size, step_size, **kwargs)
        return g
    return wrapper()

#-------------------------------------------------------------------
# multi_element
#-------------------------------------------------------------------
def multi_e(func):
    def wrapper(**kwargs):
        def g_multi_e(in_streams, out_streams, state=None, **kwargs):
            if state is None:
                return multi_element(func, in_streams, out_streams, **kwargs)
            else:
                return multi_element(func, in_streams, out_streams, state, **kwargs)
        return g_multi_e
    return wrapper()

#-------------------------------------------------------------------
# multi_window
#-------------------------------------------------------------------
def multi_w(func):
    def wrapper(**kwargs):
        def g_multi_w(
                in_streams, out_streams, 
                window_size, step_size, state=None, **kwargs):
            if state is None:
                return multi_window(
                    func, in_streams, out_streams,
                    window_size, step_size, **kwargs)
            else:
                return multi_window(
                    func, in_streams, out_streams,
                    window_size, step_size, state, **kwargs)
        return g_multi_w
    return wrapper()

#-------------------------------------------------------------------
# sink_element
#-------------------------------------------------------------------
def sink_e(func):
    def wrapper(**kwargs):
        def g(in_stream, **kwargs):
            sink_element(func, in_stream, **kwargs)
        return g
    return wrapper()


#-------------------------------------------------------------------
# sink_window
#-------------------------------------------------------------------
def sink_w(func):
    def wrapper(**kwargs):
        def g(in_stream, window_size, step_size, **kwargs):
            sink_window(func, in_stream,  window_size, step_size, **kwargs)
        return g
    return wrapper()

#------------------------------------------------------------
#       USEFUL FUNCTIONS OTHER THAN WRAPPERS
#------------------------------------------------------------

def prepend(lst, in_stream, out_stream):
    out_stream.extend(lst)
    map_element(lambda v: v, in_stream, out_stream)

def fprepend(lst, in_stream):
    out_stream = Stream()
    out_stream.extend(lst)
    map_element(lambda v: v, in_stream, out_stream)
    return out_stream

@fmap_e
def exponential_smoothing(v, current_state, alpha):
   next_state = alpha*current_state + (1 - alpha)*v
   next_output = next_state
   return next_output, next_state

@fmap_e
def filter_min(x, min_value):
    return x if abs(x) >= min_value else _no_value

def f_mul(in_stream, arg):
    @fmap_e
    def times(v, arg): return v*arg
    return times(in_stream, arg=arg)

def r_mul(in_stream, out_stream, arg):
    @map_e
    def times(v, arg): return v*arg
    return times(in_stream, out_stream, arg=arg)

def r_add(in_stream, out_stream, arg):
    @map_e
    def plus(v, arg): return v+arg
    return plus(in_stream, out_stream, arg=arg)

## def f_add(in_stream, arg):
##     @fmap_e
##     def plus(v, arg): return v+arg
##     return plus(in_stream, arg=arg)

def f_add(in_stream, arg):
    out_stream = Stream('out_stream_of_f_add')
    r_add(in_stream, out_stream, arg)
    return out_stream

def f_sub(in_stream, arg):
    @fmap_e
    def f(v, arg): return v - arg
    return f(in_stream, arg=arg)

def r_sub(in_stream, out_stream, arg):
    @map_e
    def f(v, arg): return v - arg
    return f(in_stream, out_stream, arg=arg)

def minimum(in_stream, arg):
    @fmap_e
    def mini(x, arg): return min(x, arg)
    return mini(in_stream, arg=arg)

def maximum(in_stream, arg):
    @fmap_e
    def maxi(x, arg): return max(x, arg)
    return maxi(in_stream, arg=arg)

def clip(in_stream, arg):
    @fmap_e
    def f(x, arg):
        if x < -arg: return -arg
        elif x > arg: return arg
        else: return x
    return f(in_stream, arg=arg)

def sieve(in_stream, primes):
    out_stream = Stream()
    @map_e
    def f(v, state, primes):
        my_prime, last = state
        output = _no_value
        if my_prime == 0:
            my_prime = v
            primes.append(v)
        else:
            if v % my_prime != 0:
                output = v
                if last:
                    last = False
                    sieve(out_stream, primes)
        return output, (my_prime, last)
    f(in_stream, out_stream, state=(0, True), primes=primes)

def make_echo(spoken, D, A):
    echo = Stream(name='echo', initial_value=[0]*D)
    heard = spoken + echo
    map_element(func=lambda v: v*A, in_stream=heard, out_stream=echo)
    return heard

def make_echo_1(spoken, D, A):
    echo = Stream('echo')
    heard = spoken + echo
    prepend([0]*D, in_stream=f_mul(heard, A), out_stream=echo)
    return heard

@sink_e
def print_stream(v, stream_name=None):
    if stream_name is not None:
        print(stream_name, ' : ', v)
    else:
        print(v)
