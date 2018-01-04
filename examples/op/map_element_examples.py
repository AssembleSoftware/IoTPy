"""
====================
Map Element Examples
====================
agent maps the function func from its single input stream to its
single output stream.
    
This example demonstrates how to use :function:`map_element` in 
agent_types/op.py on streams.
"""

import sys
import os
sys.path.append(os.path.abspath("../../IoTPy/"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))

from agent import Agent
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from op import map_element

scheduler = Stream.scheduler
# In the following, x and y are streams that must be declared
# before the functions are called.
x = Stream('x')
y = Stream('y')
#----------------------------------------------------------------    
# map_element with no state and no additional arguments
#----------------------------------------------------------------
def double(a):
    return 2*a
doubles = Stream()
map_element(func=double, in_stream=x, out_stream=doubles) 
#y[j] = 2*x[j] for j = 0, 1, 2,...

#----------------------------------------------------------------    
# map_element with no state and with keyword arguments
#----------------------------------------------------------------
# The arguments in this example are multiplicand and addend
 
def multiply_and_add(a, multiplicand, addend):
    return multiplicand*a + addend
mult_add = Stream()
map_element(func=multiply_and_add, in_stream=x, out_stream=mult_add,
            multiplicand=2, addend=10)
# y[j] = x[j]*2 + 10, for j = 0, 1, 2,...

#----------------------------------------------------------------    
# map_element with state and with no additional arguments
#----------------------------------------------------------------
# At each step, the state is increased by 2. So, at the j-th
# step, state is 2*j
 
def add_twice_position(a, state):
    return a+state, state+2
add_twice = Stream()
map_element(func=add_twice_position, in_stream=x, out_stream=add_twice,
            state=0)
# y[j] = x[j] + 2*j


#----------------------------------------------------------------
# Same example merely to illustrate that the name of the state
# parameter of func does not have to be "state"
def add_twice_position(a, position):
    # Next output is: a + position
    # Next state is: position + 2
    return a+position, position+2
# The initial state is 0.
add_twice_pos = Stream()
map_element(func=add_twice_position, in_stream=x, out_stream=add_twice_pos,
            state=0)
# y[j] = x[j] + 2*j

#----------------------------------------------------------------
# Same example with different initial value of "state"
# Initial state is 10.
# At the j-th step state is 10 + 2*j
add_twice_state = Stream()
map_element(func=add_twice_position, in_stream=x, out_stream=add_twice_state,
            state=10)
# y[j] = x[j] + 2*j + 10


#----------------------------------------------------------------    
# map_element with state and with keyword arguments
#----------------------------------------------------------------
# The arguments in this example are multiplicand and addend

def f(a, position, multiplicand, addend):
    # Next output is a*multiplicand + position
    # Next state is position + addend
    return a*multiplicand + position, position + addend
addends = Stream()
map_element(func=f, in_stream=x, out_stream=addends, state=0,
            multiplicand=2, addend=1)
# Initial state is 0.
# y[j] = x[j]*2 + j, for j = 0, 1, 2, ....

x.extend(range(4))
"""
====================
Map Element Examples
====================
agent maps the function func from its single input stream to its
single output stream.
    
This example demonstrates how to use :function:`map_element` in 
agent_types/op.py on streams.
"""

import sys
import os
sys.path.append(os.path.abspath("../"))
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))

from agent import Agent
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from op import map_element

scheduler = Stream.scheduler
# In the following, w, x, y, z are streams that must be declared
# before the functions are called.
v = Stream('v')
w = Stream('w')
x = Stream('x')
y = Stream('y')
z = Stream('z')
#----------------------------------------------------------------    
# map_element with no state and no additional arguments
#----------------------------------------------------------------
def double(a):
    return 2*a
doubles = Stream()
map_element(func=double, in_stream=x, out_stream=doubles) 
#y[j] = 2*x[j] for j = 0, 1, 2,...

#----------------------------------------------------------------    
# map_element with no state and with keyword arguments
#----------------------------------------------------------------
# The arguments in this example are multiplicand and addend
 
def multiply_and_add(a, multiplicand, addend):
    return multiplicand*a + addend
mult_add = Stream()
map_element(func=multiply_and_add, in_stream=x, out_stream=mult_add,
            multiplicand=2, addend=10)
# y[j] = x[j]*2 + 10, for j = 0, 1, 2,...

#----------------------------------------------------------------    
# map_element with state and with no additional arguments
#----------------------------------------------------------------
# At each step, the state is increased by 2. So, at the j-th
# step, state is 2*j
 
def add_twice_position(a, state):
    return a+state, state+2
add_twice = Stream()
map_element(func=add_twice_position, in_stream=x, out_stream=add_twice,
            state=0)
# y[j] = x[j] + 2*j


#----------------------------------------------------------------
# Same example merely to illustrate that the name of the state
# parameter of func does not have to be "state"
def add_twice_position(a, position):
    # Next output is: a + position
    # Next state is: position + 2
    return a+position, position+2
# The initial state is 0.
add_twice_pos = Stream()
map_element(func=add_twice_position, in_stream=x, out_stream=add_twice_pos,
            state=0)
# y[j] = x[j] + 2*j

#----------------------------------------------------------------
# Same example with different initial value of "state"
# Initial state is 10.
# At the j-th step state is 10 + 2*j
add_twice_state = Stream()
map_element(func=add_twice_position, in_stream=x, out_stream=add_twice_state,
            state=10)
# y[j] = x[j] + 2*j + 10


#----------------------------------------------------------------    
# map_element with state and with keyword arguments
#----------------------------------------------------------------
# The arguments in this example are multiplicand and addend

def f(a, position, multiplicand, addend):
    # Next output is a*multiplicand + position
    # Next state is position + addend
    return a*multiplicand + position, position + addend
addends = Stream()
map_element(func=f, in_stream=x, out_stream=addends, state=0,
            multiplicand=2, addend=1)
# Initial state is 0.
# y[j] = x[j]*2 + j, for j = 0, 1, 2, ....

x.extend(range(4))
print 'x'
print recent_values(x)
scheduler.step()
print 'doubles'
print recent_values(doubles)
print 'multiply_and_add'
print recent_values(mult_add)
print 'add_twice_position'
print recent_values(add_twice)
print 'add_twice_position: same example'
print recent_values(add_twice_pos)
print 'add_twice_position. different state'
print recent_values(add_twice_state)
print 'multiplicand and addend'
print recent_values(addends)