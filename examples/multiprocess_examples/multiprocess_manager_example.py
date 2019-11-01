import multiprocessing as mp
from multiprocessing import Process, Manager

def f(d, l):
    d[1] = '1'
    d['2'] = 2
    d[0.25] = None
    l.reverse()


if __name__ == '__main__':
    mp.set_start_method('spawn')
    with Manager() as manager:
        d = manager.dict()
        l = manager.list(range(10))
        v = 100

        p = Process(target=f, args=(d, l))
        p.start()
        p.join()

        print(d)
        print(l)
