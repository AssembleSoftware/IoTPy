import sys
sys.path.append("../")
from IoTPy.core.stream import Shared, activate, run, Stream

class triangle_inequality(object):
    def __init__(self, d, i, j, k):
        self.d, self.i, self.j, self.k = d, i, j, k
        self.actors = None
    def next(self):
        if self.d[self.i][self.k] > self.d[self.i][self.j] + self.d[self.j][self.k]:
            self.d[self.i][self.k] = self.d[self.i][self.j] + self.d[self.j][self.k]
            for r in range(len(self.d)):
                activate(self.actors[self.i][self.k][r])
                activate(self.actors[r][self.i][self.k])

def shortest_path(d):
    R = range(len(d))
    actors = [[[[] for k in R] for j in R] for i in R]
    for i in R:
        for j in R:
            for k in R:
                actors[i][j][k] = triangle_inequality(d, i, j, k)
                actors[i][j][k].actors = actors
                activate(actors[i][j][k])
    run()

#----------------------------------------------------------------------
# TESTS
#----------------------------------------------------------------------

def test_shortest_path():
    d = [[0, 2, 4], [3, 0, 9], [15, 32, 0]]
    shortest_path(d)
    assert d == [[0, 2, 4], [3, 0, 7], [15, 17, 0]]

def test_shortest_path_random():
    import numpy as np
    N = 5
    d = np.random.randint(100, size=(N, N))
    for i in range(N): d[i, i] = 0
    D = d.copy()
    # Run the agent-based shortest path algorithm. The result is in d.
    shortest_path(d)
    # Run the traditional sequential shortest path algorithm.
    # Result is in D.
    for n in range(int(np.ceil(np.log2(N)))):
        for i in range(N):
            for j in range(N):
                for k in range(N):
                    D[i][k] = min(D[i][k], D[i][j]+D[j][k])
    # Assert that the results of both algorithms are the same.
    assert (D == d).all()

if __name__ == '__main__':
    test_shortest_path()
    for _ in range(10):
        test_shortest_path_random()
