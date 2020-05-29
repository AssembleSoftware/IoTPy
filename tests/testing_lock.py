import multiprocessing

main_lock = multiprocessing.Lock()

global n
n = 0

class c(object):
    def __init__(self, n):
        self.n = n
        self.main_lock = None
    def f(self):
        print (self.main_lock)
        with self.main_lock:
            self.n +=1
            print ('n is ', self.n)

x = c(0)
y = c(0)
x.main_lock = main_lock
y.main_lock = main_lock
assert x.main_lock == y.main_lock

x.f()
y.f()
