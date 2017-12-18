import sys
import os
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))

from agent import Agent
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from op import *

def sort(lst):

    def flip(I, L):
        i = I[0]
        if lst[i] > lst[i+1]:
            lst[i], lst[i+1] = lst[i+1], lst[i]
            return (1)
        else:
            return (_no_value)

    x = Stream('x')

    for i in range(len(lst) - 1):
        signal_element(func=flip, in_stream=x, out_stream=x, name=i, I=[i], L=lst)
    scheduler = Stream.scheduler
    x.append(1)
    scheduler.step()

def shortest_path(D):
    def triangle_inequality(triple, D):
        i, j, k = triple
        if D[i][j] + D[j][k] < D[i][k]:
            D[i][k] = D[i][j] + D[j][k]
            D[k][i] = D[i][k]
            return(1)
        else:
            return (_no_value)

    x = Stream('x')
    size = len(D)
    for i in range(size):
        for j in range(i):
            for k in range(size):
                signal_element(func=triangle_inequality,
                               in_stream=x, out_stream=x,
                               name=str(i)+"_"+str(j)+"_"+str(k),
                               triple=[i, j, k], D=D)
    scheduler = Stream.scheduler
    x.append(1)
    scheduler.step()
    
    return D


def test_shared_variables():
    lst = [10, 6, 8, 3, 20, 2, 23, 35]
    sort(lst)
    assert lst == [2, 3, 6, 8, 10, 20, 23, 35]

    D = [[0, 20, 40, 60], [20, 0, 10, 1], [40, 10, 0, 100],
         [60, 1, 100, 0]]
    shortest_path(D)
    assert D == [[0, 20, 30, 21], [20, 0, 10, 1],
                 [30, 10, 0, 11], [21, 1, 11, 0]]
    print 'TEST OF SHARED VARIABLES IS SUCCESSFUL!'
    
                

if __name__ == '__main__':
    test_shared_variables()

    
            
