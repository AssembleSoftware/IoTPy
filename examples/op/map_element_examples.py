"""
This module contains examples of agents created using the map_element
wrapper. See IoTPy/IoTPy/tests/element_test.py for more examples.

map_element is a function in IoTPy/IoTPy/agents_types/op.py

The call to map_element is:
   map_element(func, in_stream, out_stream, state, name, **kwargs)
where
  func is a function from an element of in_stream to an element of
  out_stream.
  in_stream is the input stream of the agent
  out_stream is the output stream of the agent
  state: optional
    is the state of the agent if the agent has state.
    The state can be any object.
  name: str, optional
    is the name of the agent.
  **kwargs: keyword arguments, if any, of func.

The call creates an agent with a single input stream and a single
output stream. When a value v is appended to the input stream, the
agent appends func(v) to the output stream.

"""
import sys
sys.path.append("../../IoTPy/")
sys.path.append("../../IoTPy/core")
sys.path.append("../../IoTPy/agent_types")
sys.path.append("../../IoTPy/helper_functions")

# stream is in IoTPy/IoTPy/core/
from stream import Stream
from stream import _no_value, _multivalue
# op is in IoTPy/IoTPy/agent_types/
from op import map_element
# check_agent_parameter_types is in IoTPy/IoTPy/agent_types/
# recent_values, print_stream are in IoTPy/IoTPy/agent_types/
from check_agent_parameter_types import *
from recent_values import recent_values
from print_stream import print_stream

# In the following, x and y are streams that must be declared
# before the functions are called.
x = Stream('x')
y = Stream('y')

#----------------------------------------------------------------    
# map_element with no state and no additional arguments
#----------------------------------------------------------------
# GENERIC EXAMPLE
# f is a function from an element of the input stream to an element of
# the output stream.
# map_element(func=f, in_stream=x, out_stream=y) 
# y[j] = f(x[j]) for j = 0, 1, 2,...

# EXAMPLE 1
def f(v): return 2*v
map_element(func=f, in_stream=x, out_stream=y) 
#y[j] = 2*x[j] for j = 0, 1, 2,...


#----------------------------------------------------------------    
# EXAMPLE: map_element with no state and with keyword arguments
#----------------------------------------------------------------
# The keyword arguments of func in this example are multiplicand and
# addend.
# The first argument of func is an in_stream element. The remaining
# arguments are passed as keyword arguments specified in map_element.
 
def multiply_and_add(v, multiplicand, addend):
    return multiplicand * v + addend

map_element(func=multiply_and_add, in_stream=x, out_stream=y,
            multiplicand=2, addend=10)
# y[j] = x[j]*2 + 10, for j = 0, 1, 2,...

#----------------------------------------------------------------    
# EXAMPLE: map_element with state and with no additional arguments
#----------------------------------------------------------------
# 
# At each step, the state is increased by 2. So, at the j-th
# step, state is 2*j
 
def add_twice_position(in_stream_element, current_state):
    out_stream_element = in_stream_element + current_state
    next_state = current_state+2
    return out_stream_element, next_state

map_element(func=add_twice_position, in_stream=x, out_stream=y,
            state=0)
# y[j] = x[j] + 2*j
# If x is [0, 1, 2, 3, 4,..] then y is [0, 3, 6, 9, 12, ...]


#----------------------------------------------------------------
# EXAMPLE: Same example, short form
def add_twice_position(a, position):
    return a+position, position+2
map_element(func=add_twice_position, in_stream=x, out_stream=y,
            state=0)

#----------------------------------------------------------------
# EXAMPLE: Same example with different initial value of state
# Initial state is 10.
# At the j-th step state is 10 + 2*j
map_element(
    func=add_twice_position, in_stream=x, out_stream=y,
    state=10) 
# y[j] = x[j] + 2*j + 10

#----------------------------------------------------------------
# EXAMPLE: Example of a state that is a tuple.
def f(in_stream_element, current_state):
        next_state = (current_state[1], sum(current_state))
        out_stream_element = next_state[0]
        return out_stream_element, next_state

map_element(func=f, in_stream=x, out_stream=y, state=(0,1))
# The sequence of values of next_state are:
# (0, 1), (1, 1), (1, 2), (2, 3), (3, 5), (5, 8), ....
# and hence the output is 1, 1, 2, 3, 5, 8, ...
# which is the Fibonacci sequence. This is independent of the input
# stream. The length of y will be the same as the length of x.

#----------------------------------------------------------------    
# EXAMPLE: map_element with state and with keyword arguments
#----------------------------------------------------------------
# In this example, the keyword arguments passed to func are
# multiplicand and addend. Note the order of parameters of func:
# in_stream_element, then current_state, then keyword arguments.

def f(in_stream_element, current_state, multiplicand, addend):
    out_stream_element = \
      in_stream_element*multiplicand + current_state
    next_state = current_state + addend
    return out_stream_element, next_state

map_element(func=f, in_stream=x, out_stream=y, state=0,
            multiplicand=3, addend=2)
# Initial state is 0.
# y[j] = x[j]*3 + 2*j, for j = 0, 1, 2, ....
# If x is [0, 1, 2, 3, 4,....] then y is [0, 5, 10, 15, 20, ...]


#----------------------------------------------------------------    
# EXAMPLE: Illustrates use of _no_value
#----------------------------------------------------------------
# In this example, the output stream is the same as the input stream
# except that multiples of 2 are filtered out.
def f(in_stream_element):
    if in_stream_element % 2:
            out_stream_element = in_stream_element
    else:
            out_stream_element = _no_value
    return out_stream_element
map_element(func=f, in_stream=x, out_stream=y)
# If x is [0, 1, 2, 3, 4,....] then y is [1, 5, 7, 11,...]


#----------------------------------------------------------------    
# EXAMPLE: Illustrates use of _no_value and a keyword argument
#----------------------------------------------------------------
# In this example, the output stream is the same as the input stream
# except that only values that are less than the threshold are passed
# through to the output stream. Here threshold is a keyword argument
def f(in_stream_element, threshold):
    if in_stream_element < threshold:
            out_stream_element = in_stream_element
    else:
            out_stream_element = _no_value
    return out_stream_element
map_element(func=f, in_stream=x, out_stream=y, threshold=5)
# If x is [0, 1, 2, 3, 4,....20] then y is [0, 1, 2, 3, 4]


#----------------------------------------------------------------    
# EXAMPLE: Illustrates use of _multivalue and _no_value
#----------------------------------------------------------------
# Elements of the input stream are tuples (x, y). Any x or y that
# exceeds 5 is placed in the output stream
def f(in_stream_element):
        x, y = in_stream_element
        if x > 5 and y > 5:
                out_stream_element = _multivalue((x,y))
        elif x > 5:
                out_stream_element = x
        elif y > 5:
                out_stream_element = y
        else:
                out_stream_element = _no_value
        return out_stream_element
map_element(func=f, in_stream=x, out_stream=y)
# If x is [(10, 10), (2, 20), (30, 3), (4, 4), (1, 3), (60, 70)] then
# y is [10, 10, 20, 30, 60, 70]

# Compare the above example with a function in which _multivalue is
# not used.

def f(in_stream_element):
        x, y = in_stream_element
        if x > 5 and y > 5:
                out_stream_element = (x,y)
        elif x > 5:
                out_stream_element = x
        elif y > 5:
                out_stream_element = y
        else:
                out_stream_element = _no_value
        return out_stream_element
map_element(func=f, in_stream=x, out_stream=y)
# If x is [(10, 10), (2, 20), (30, 3), (4, 4), (1, 3), (60, 70)] then
# y is [(10, 10), 20, 30, (60, 70)]

#----------------------------------------------------------------    
# EXAMPLE: map_element using a Class and _no_value
#----------------------------------------------------------------
class my_dict(object):
        """
        Example illustrating the use of a method of an object as func
        in map_element.
        This example also illustrates the use of _no_value. When func
        returns _no_value then no value (as opposed to None) is put on
        the output stream.

        This object keeps a dictionary (current_dict). If an element
        of the input stream is a pair (key, value) then the key-value
        is inserted into the dictionary and nothing is placed on the
        output stream. If the element is a key, and if the key is in
        the dictionary then the corresponding (key, value) tuple is
        placed on the output stream; if the key is not in the
        dictionary, then a warning is printed, and nothing is placed
        on the output stream.

        Example
        -------
        If the input stream is:
        [('b', 2), ('c', 3), 'a', 'b', 'a', 'd', ('a', 10), 'a', .. ]
        then the output stream is:
        [('a', 1), ('b', 2), ('a', 1), ('a', 10), ....]
        and the warning:
        Key d is not in the dictionary
        is printed to the screen.
        

        """
        def __init__(self):
            self.current_dict = {'a':1}
        def get_value(self, key):
            return self.current_dict[key]
        def put_value(self, key, value):
            self.current_dict[key] = value
        def f(self, in_stream_element):
            if isinstance(in_stream_element, tuple):
                key, value = in_stream_element
                self.put_value(key, value)
                return _no_value
            else:
                key = in_stream_element
                if key in self.current_dict:
                    return (key, self.get_value(key))
                else:
                    print ('Key', key, 'is not in the dictionary')
                    return _no_value

example_object = my_dict()
map_element(func=example_object.f, in_stream=x, out_stream=y)
