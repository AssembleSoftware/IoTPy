from multiprocessing import Process, Value, Array
import unittest


class test_multicore37(unittest.TestCase):

    def f(self, n, a, b):
        n.value = 3.1415927
        for i in range(len(a)):
            a[i] = -a[i]
        for i in range(len(b)):
            b[i] = 2*b[i]
    def g(self, n, l):
        A, B = l
        name_a, arr_a = A
        name_b, arr_b = B
        print ('names are ', name_a, name_b)    
        self.f(n,arr_a,arr_b)

    def h(self, l):
        A, B = l
        name_a, arr_a = A
        name_b, arr_b = B
        print ('names are ', name_a, name_b)    
        for i in range(len(arr_a)):
            arr_a[i] = arr_a[i] * 100   
        for i in range(len(arr_b)):
            arr_b[i] = arr_b[i] * 1000
        

    def test(self):
        import numpy as np
        num = Value('d', 0.0)
        arr_a = Array('i', range(10))
        arr_b = Array('i', range(10))
        np_a = np.arange(10)
        np_b = np.arange(10)
        print ('num.value = ', num.value)
        print ('arr_a[:] = ', arr_a[:])
        print ('np_a[:] = ', np_a)
        print ('np_b[:] = ', np_b)
        l = [('a', np_a), ('b', np_b)]
        l_arr = [('a', arr_a), ('b', arr_b)]

        p = Process(target=self.g, args=(num, l,))
        q = Process(target=self.h, args=(l,))
        p.start()
        q.start()
        p.join()
        q.join()

        print('num.value = ', num.value)
        print('np_a[:] = ', np_a[:])
        print('np_b[:] = ', np_b[:])



        p = Process(target=self.g, args=(num, l_arr,))
        q = Process(target=self.h, args=(l_arr,))
        p.start()
        q.start()
        p.join()
        q.join()

        print('num.value = ', num.value)
        print('arr_a[:] = ', arr_a[:])
        print('arr_b[:] = ', arr_b[:])


if __name__ == '__main__':
    unittest.main()
