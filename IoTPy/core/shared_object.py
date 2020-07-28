# compute_engine is in IoTPy/IoTPy/core
import numpy as np

from .compute_engine import ComputeEngine

scheduler = ComputeEngine()
def run(): scheduler.step()
    
lst = [30, 15, 11, 8, 3, 1]
N = 3

class Shared(object):
    def __init__(self, name="NoName", initial_value=None):
        self.name = name
        self.initial_value = initial_value
        self.subscribers_set = set()

    def register(self, agent):
        self.subscribers_set.add(agent)

    def delete(self, agent):
        self.subscribers_set.discard(agent)

    def activate(self):
        # Put subscribers into the compute_engine's scheduler queue.
        for subscriber in self.subscribers_set:
            scheduler.put(subscriber)

class Actor(object):
    def __init__(self, inputs, outputs, name=None):
        self.inputs = inputs
        self.outputs = outputs
        self.name = name
        for input in self.inputs:
            input.register(self)
    def activate(self):
        scheduler.put(self)

def swap(the_list, i, j):
    the_list[i], the_list[j] = the_list[j], the_list[i]

class sort_agent(Actor):
    def __init__(self, left_neighbor, right_neighbor, left_me, right_me, left_N, right_N, the_list, name):
        self.left_neighbor = left_neighbor
        self.right_neighbor = right_neighbor
        self.left_me = left_me
        self.right_me = right_me
        self.left_N = left_N
        self.right_N = right_N
        self.the_list = the_list
        super().__init__(inputs=[left_neighbor, right_neighbor],
                         outputs=[left_me, right_me],
                         name=name)
        self.activate()
    def next(self):
        self.the_list[self.left_N : self.right_N] = sorted(self.the_list[self.left_N : self.right_N])
        if (self.the_list[self.left_N-1] > self.the_list[self.left_N]):
            swap(self.the_list, self.left_N-1, self.left_N)
            self.left_me.activate()
            self.activate()
        if (self.the_list[self.right_N-1] > self.the_list[self.right_N]):
            swap(self.the_list, self.right_N-1, self.right_N)
            self.right_me.activate()
            self.activate()

class srt(Actor):
    def __init__(self, i, j, l, signals, name):
        self.i, self.j, self.l = i, j, l
        self.signals = signals
        self.name = name
        super().__init__(inputs=[signals[i-1], signals[j]],
                         outputs=[signals[i], signals[j-1]],
                         name=name)
        self.activate()
    def next(self):
        self.l[self.i : self.j] = sorted(self.l[self.i : self.j])
        if (self.l[self.i-1] > self.l[self.i]):
            swap(self.l, self.i-1, self.i)
            self.signals[self.i].activate()
            self.activate()
        if (self.l[self.j-1] > self.l[self.j]):
            swap(self.l, self.j-1, self.j)
            self.signals[self.j-1].activate()
            self.activate()

class srt_2(object):
    def __init__(self, i, j, l, signals, name):
        self.i, self.j, self.l = i, j, l
        self.signals = signals
        self.name = name
        signals[i-1].register(self)
        signals[j].register(self)
        scheduler.put(self)
        #self.activate()
    def next(self):
        self.l[self.i : self.j] = sorted(self.l[self.i : self.j])
        if (self.l[self.i-1] > self.l[self.i]):
            swap(self.l, self.i-1, self.i)
            self.signals[self.i].activate()
            scheduler.put(self)
        if (self.l[self.j-1] > self.l[self.j]):
            swap(self.l, self.j-1, self.j)
            self.signals[self.j-1].activate()
            scheduler.put(self)

class triangle_inequality(object):
    def __init__(self, d, signals, i, j, k, name):
        self.d, self.signals = d, signals
        self.i, self.j, self.k = i, j, k
        self.name = name
        self.N = d.shape[0]
        for r in range(self.N):
            signals[i][r].register(self)
            signals[r][k].register(self)
            scheduler.put(self)
    def next(self):
        if self.d[self.i, self.k] > self.d[self.i, self.j] + self.d[self.j, self.k]:
            self.d[self.i, self.k] = self.d[self.i, self.j] + self.d[self.j, self.k]
            for r in range(self.N):
                self.signals[self.i][r].activate()
                self.signals[r][self.k].activate()

def test_1(a_list, step_size=3):
    the_list =[min(a_list)] + a_list + [max(a_list)]
    initial_a_list = list(a_list)
    cutoffs = list(range(1, len(the_list) - 1, step_size))
    cutoffs.append(len(the_list)-1)

    M = len(cutoffs)
    left_end = [Shared() for i in range(M+1)]
    right_end = [Shared() for i in range(M+1)]
    
    actors = [sort_agent(
        left_neighbor=right_end[i-1], right_neighbor=left_end[i+1],
        left_me=left_end[i], right_me=right_end[i],
        left_N=cutoffs[i-1], right_N=cutoffs[i],
        the_list=the_list, name = str(i))
        for i in range(1, M)]

    scheduler.step()

    assert the_list[1:-1] == sorted(initial_a_list)

def test_2(a_list, step_size=3):
    the_list =[min(a_list)] + a_list + [max(a_list)]
    initial_a_list = list(a_list)
    cutoffs = list(range(1, len(the_list) - 1, step_size))
    cutoffs.append(len(the_list)-1)

    M = len(cutoffs)
    signals = [Shared() for i in range(len(the_list)+1)]
    
    actors = [srt(cutoffs[k-1], cutoffs[k], the_list, signals, name=str(k)) for k in range(1, M)]

    scheduler.step()

    assert the_list[1:-1] == sorted(initial_a_list)

def test_3(a_list, step_size=3):
    the_list =[min(a_list)] + a_list + [max(a_list)]
    initial_a_list = list(a_list)
    cutoffs = list(range(1, len(the_list) - 1, step_size))
    cutoffs.append(len(the_list)-1)

    M = len(cutoffs)
    signals = [Shared() for i in range(len(the_list)+1)]
    
    actors = [srt_2(cutoffs[k-1], cutoffs[k], the_list, signals, name=str(k)) for k in range(1, M)]

    scheduler.step()

    assert the_list[1:-1] == sorted(initial_a_list)

def test_shortest_path():
    d = np.array([[0, 2, 4], [3, 0, 9], [15, 32, 0]])
    dimension = d.shape[0]
    signals = [[Shared() for i in range(dimension)] for j in range(dimension)]
    for i in range(dimension):
        for j in range(dimension):
            for k in range(dimension):
                triangle_inequality(d, signals, i, j, k, str(i)+'_'+str(j)+'_'+str(k))
    print ('d')
    print (d)
    scheduler.step()
    print ('d')
    print (d)

if __name__ == '__main__':
    import random
    N = 12
    for step_size in range(2, 6):
        a_list = [random.randint(1, 100) for i in range(N)]
        test_1(a_list, step_size)
        test_2(a_list, step_size)
        test_3(a_list, step_size)
    test_1([10, 9, 8, 7, 6, 5, 4, 3, 2, 1], 3)
    test_2([10, 9, 8, 7, 6, 5, 4, 3, 2, 1], 3)

    test_shortest_path()

