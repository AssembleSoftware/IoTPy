import sys
sys.path.append("../")
from IoTPy.core.stream import Shared, activate, run

def swap(the_list, i, j):
    the_list[i], the_list[j] = the_list[j], the_list[i]

class sort_UNITY(object):
    def __init__(self, i, j, l, signals, name):
        self.i, self.j, self.l = i, j, l
        self.signals = signals
        self.name = name
        signals[i-1].register(self)
        signals[j].register(self)
        activate(self)
    def next(self):
        self.l[self.i : self.j] = sorted(self.l[self.i : self.j])
        if (self.l[self.i-1] > self.l[self.i]):
            swap(self.l, self.i-1, self.i)
            self.signals[self.i].activate()
            activate(self)
        if (self.l[self.j-1] > self.l[self.j]):
            swap(self.l, self.j-1, self.j)
            self.signals[self.j-1].activate()
            activate(self)

def test(a_list, step_size=3):
    the_list =[min(a_list)] + a_list + [max(a_list)]
    initial_a_list = list(a_list)
    cutoffs = list(range(1, len(the_list) - 1, step_size))
    cutoffs.append(len(the_list)-1)

    M = len(cutoffs)
    signals = [Shared() for i in range(len(the_list)+1)]
    actors = [sort_UNITY(cutoffs[k-1], cutoffs[k], the_list, signals, name=str(k)) for k in range(1, M)]
    run()
    assert the_list[1:-1] == sorted(initial_a_list)

if __name__ == '__main__':
    import random
    N = 20
    for step_size in range(2, 6):
        a_list = [random.randint(1, 100) for i in range(N)]
        test(a_list, step_size)
