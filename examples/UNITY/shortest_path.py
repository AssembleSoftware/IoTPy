import numpy as np
import sys
sys.path.append("../")
from IoTPy.core.stream import Shared, activate, run

class triangle_inequality(object):
    def __init__(self, d, signals, i, j, k, name):
        self.d, self.signals = d, signals
        self.i, self.j, self.k = i, j, k
        self.name = name
        self.N = d.shape[0]
        for r in range(self.N):
            signals[i][r].register(self)
            signals[r][k].register(self)
            activate(self)
    def next(self):
        if self.d[self.i, self.k] > self.d[self.i, self.j] + self.d[self.j, self.k]:
            self.d[self.i, self.k] = self.d[self.i, self.j] + self.d[self.j, self.k]
            for r in range(self.N):
                self.signals[self.i][r].activate()
                self.signals[r][self.k].activate()

def shortest_path(d):
    dimension = d.shape[0]
    signals = [[Shared() for i in range(dimension)] for j in range(dimension)]
    for i in range(dimension):
        for j in range(dimension):
            for k in range(dimension):
                triangle_inequality(d, signals, i, j, k, str(i)+'_'+str(j)+'_'+str(k))
    run()
    return d
    
def test_shortest_path():
    d = np.array([[0, 2, 4], [3, 0, 9], [15, 32, 0]])
    shortest_path(d)
    assert np.array_equal(d, np.array([[0, 2, 4], [3, 0, 7], [15, 17, 0]]))

def test_shortest_path_random():
    dimension = 4
    d = np.random.randint(100, size=(dimension, dimension))
    for i in range(dimension): d[i, i] = 0
    print ('initial d is ')
    print (d)
    # Run the shortest path algorithm
    shortest_path(d)
    print ('d is ')
    print (d)
    


if __name__ == '__main__':
    test_shortest_path()
    test_shortest_path_random()
