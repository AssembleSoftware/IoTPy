import sys
sys.path.append("../")
from IoTPy.core.stream import Shared, activate, run

class sort_pair(object):
    """
    See documentation in AssembleSoftware.com, examples, UNITY.

    """
    def __init__(self, the_list, my_index):
        self.the_list, self.my_index = the_list, my_index
        self.actors = None
        self.N = len(self.the_list)
    def next(self):
        if self.the_list[self.my_index] > self.the_list[self.my_index+1]:
            self.the_list[self.my_index], self.the_list[self.my_index+1] = \
              self.the_list[self.my_index+1], self.the_list[self.my_index]
            if self.my_index > 0: activate(self.actors[self.my_index-1])
            if self.my_index < self.N-2: activate(self.actors[self.my_index+1])

class sort_1(object):
    """
    Similar to sort_pair except that a list is partitioned into contiguous lists whereas
    in sort_pair a list consists of overlapping pairs (i-1, i), (i, i+1), (i+1, i+2),...
    of values. Here, if the lengths of the sublists is L then the list is partioned into
    sublists [0:L], [L:2*L], [2*L:3*L], and so on.
    """ 
    def __init__(self, left_index, right_index, the_list):
        """
        Parameters
        ----------
        left_index: int
          The index into the_list where this sublist starts.
        right_index: int
          The index into the_list where this sublist ends.

        """
        self.left_index, self.right_index, self.the_list = left_index, right_index, the_list
        self.left_actor = None
        self.right_actor = None
        activate(self)
    def next(self):
        self.the_list[self.left_index : self.right_index] = \
          sorted(self.the_list[self.left_index : self.right_index])
        # If the leftmost element is out of order then order it and activate
        # oneself and the left neighboring agent.
        if ((self.left_index > 1) and
            (self.the_list[self.left_index-1] > self.the_list[self.left_index])):
            self.the_list[self.left_index-1], self.the_list[self.left_index] = \
              self.the_list[self.left_index], self.the_list[self.left_index-1]
            if self.left_actor: activate(self.left_actor)
            activate(self)
        # If the rightmost element is out of order then order it and activate
        # oneself and the right neighboring agent.
        if ((self.right_index < len(self.the_list)) and
             (self.the_list[self.right_index-1] > self.the_list[self.right_index])):
            self.the_list[self.right_index-1], self.the_list[self.right_index] = \
              self.the_list[self.right_index], self.the_list[self.right_index-1]
            if self.right_actor: activate(self.right_actor)
            activate(self)

class sort_2(object):
    """
    Same as sort_1 except that an agent registers with shared variables. Activating
    a shared variable activates all the agents registered with that variable.

    """
    def __init__(self, i, j, l, signals, name):
        """
        Parameters
        ----------
           i, j: int
              i, j are the left and right indexes of this sublist and l is the
              main list.
           signals: list of Shared
              signals[k] is a Shared variable for all k. An agent responsible for
              sublist [i:j] registers with the shared variable signals[i-1] and
              signals[j]. The neighboring agent to the left activates all agents
              registered with signals[i-1] when list[i] is changed. Similarly,
              the neighboring agent to the right activates all agents
              registered with signals[j] when list[j-1] is changed.

        """
        self.i, self.j, self.l = i, j, l
        self.signals = signals
        self.name = name
        signals[i-1].register(self)
        signals[j].register(self)
        activate(self)
    def next(self):
        self.l[self.i : self.j] = sorted(self.l[self.i : self.j])
        if (self.l[self.i-1] > self.l[self.i]):
            # The left boundary is out of order. So order it and then
            # activate all agents registered with the left signal and oneself.
            self.l[self.i-1], self.l[self.i] = self.l[self.i], self.l[self.i-1]
            self.signals[self.i].activate()
            activate(self)
        if (self.j < len(self.l)) and (self.l[self.j-1] > self.l[self.j]):
            # The right boundary is out of order. So order it and then
            # activate all agents registered with the right signal and oneself.
            self.l[self.j-1], self.l[self.j] = self.l[self.j], self.l[self.j-1]
            self.signals[self.j-1].activate()
            activate(self)

def SORT_2(the_list, cutoffs):
    the_list =[min(the_list)] + the_list + [max(the_list)]
    M = len(cutoffs)
    signals = [Shared() for i in range(len(the_list)+1)]
    actors = [sort_2(cutoffs[k-1], cutoffs[k], the_list, signals, name=str(k)) for k in range(1, M)]
    run()
    return the_list[1:-1]

def SORT_1(the_list, cutoffs):
    the_list =[min(the_list)] + the_list + [max(the_list)]
    M = len(cutoffs)
    actors = [None] + [sort_1(cutoffs[k-1], cutoffs[k], the_list) for k in range(1, M)] + [None]
    for k in range(1, M):
        actors[k].left_actor = actors[k-1]
        actors[k].right_actor = actors[k+1]
    run()
    return the_list[1:-1]

def test(a_list, step_size=3):
    initial_a_list = list(a_list)
    cutoffs = list(range(1, len(a_list) - 1, step_size))
    if cutoffs[-1] == len(a_list) - 1:
        cutoffs[-1] = len(a_list)
    else:
        cutoffs.append(len(a_list))

    returned_list_1 = SORT_1(a_list, cutoffs)
    assert returned_list_1 == sorted(initial_a_list)

    returned_list_2 = SORT_2(a_list, cutoffs)
    assert returned_list_2 == sorted(initial_a_list)

def sort_simple(the_list):
    initial_list = list(the_list)
    N = len(the_list)
    actors = [sort_pair(the_list, my_index) for my_index in range(N-1)]
    for actor in actors:
        actor.actors = actors
        activate(actor)
    run()
    initial_list.sort()
    assert the_list == initial_list
        

if __name__ == '__main__':
    sort_simple([10, 3, 7, 1])
    import random
    N = 6
    for _ in range(20):
        for step_size in range(6, 7):
            a_list = [random.randint(1, 100) for i in range(N)]
            test(a_list, step_size)
            sort_simple(a_list)
    
