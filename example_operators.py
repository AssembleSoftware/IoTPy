from stream import Stream, StreamArray, run

class feed_streams(object):
    pass

class single_item(object):
    def __init__(self, in_stream, func, **kwargs):
        self.in_stream = in_stream
        self.func = func
        self.kwargs = kwargs
        self.in_stream.subscribe(self.callback)
    def callback(self):
        for v in self.in_stream.recent[self.in_stream.start[self.callback] : self.in_stream.stop]:
            self.func(v, **self.kwargs)
        self.in_stream.start[self.callback] = self.in_stream.stop


class join_synch(object):
    def __init__(self, in_streams, func, **kwargs):
        self.in_streams = in_streams
        self.func = func
        self.kwargs = kwargs
        for in_stream in self.in_streams: 
            in_stream.subscribe(self.callback)
    def callback(self):
        slices = [in_stream.recent[in_stream.start[self.callback] : in_stream.stop]
                  for in_stream in self.in_streams]
        zipped_slices = list(zip(*slices))
        for v in zipped_slices: self.func(v, **self.kwargs)
        for in_stream in self.in_streams:
            in_stream.start[self.callback] += len(zipped_slices)


class join_asynch(object):
    def __init__(self, in_streams, func, **kwargs):
        self.in_streams = in_streams
        self.func = func
        self.kwargs = kwargs
        for in_stream in self.in_streams:
            in_stream.subscribe(self.callback)
    def callback(self):
        for in_stream in self.in_streams:
            for v in in_stream.recent[in_stream.start[self.callback]: in_stream.stop]:
                self.func(v, **self.kwargs)
            in_stream.start[self.callback] = in_stream.stop


class join_timed(object):
    def __init__(self, in_streams, get_time, func, **kwargs):
        self.in_streams = in_streams
        self.get_time = get_time
        self.func = func
        self.kwargs = kwargs
        for in_stream in self.in_streams:
            in_stream.subscribe(self.callback)
    def callback(self):
        while all([in_stream.start[self.callback] < in_stream.stop 
                   for in_stream in self.in_streams]):        
            items = [in_stream.recent[in_stream.start[self.callback]] 
                     for in_stream in self.in_streams]
            times = [self.get_time(item) for item in items]
            min_time = min(times)
            operand = [None for in_stream in self.in_streams]
            for i, in_stream in enumerate(self.in_streams):
                if times[i] == min_time:
                    operand[i] = items[i]
                    in_stream.start[self.callback] += 1
            self.func((min_time, operand), **self.kwargs)


class sliding_window(object):
    def __init__(self, in_stream, window_size, step_size, func, **kwargs):
        self.in_stream = in_stream
        self.window_size = window_size
        self.step_size = step_size
        self.func = func
        self.kwargs = kwargs
        self.in_stream.subscribe(self.callback)
    def callback(self):
        while self.in_stream.start[self.callback] + self.window_size <= self.in_stream.stop:
            start = self.in_stream.start[self.callback] 
            window = self.in_stream.recent[start : start + self.window_size]
            self.func(window, **self.kwargs)
            self.in_stream.start[self.callback] += self.step_size


class subtract_mean_from_stream(object):
    def __init__(self, in_stream, window_size, func, **kwargs):
        self.in_stream = in_stream
        self.window_size = window_size
        self.func = func
        self.kwargs = kwargs
        self.in_stream.subscribe(self.callback)
    def callback(self):
        while self.in_stream.start[self.callback] + self.window_size <= self.in_stream.stop:
            start = self.in_stream.start[self.callback] 
            window = self.in_stream.recent[start : start + self.window_size]
            item = window[-1] - np.mean(window)
            self.func(item, **self.kwargs)
            self.in_stream.start[self.callback] += 1


class subtract_mean_from_StreamArray(object):
    def __init__(self, in_stream, window_size, func, **kwargs):
        self.in_stream = in_stream
        self.window_size = window_size
        self.func = func
        self.kwargs = kwargs
        self.in_stream.subscribe(self.callback)
    def callback(self):
        while self.in_stream.start[self.callback] + self.window_size <= self.in_stream.stop:
            start = self.in_stream.start[self.callback] 
            window = self.in_stream.recent[start : start + self.window_size]
            item = window[-1] - np.mean(window, axis=0)
            self.func(item, **self.kwargs)
            self.in_stream.start[self.callback] += 1



import numpy as np
class detect_anomaly(object):
    def __init__(self, in_stream, window_size, anomaly_size,
                     anomaly_factor, cloud_data_size,
                     cloud_func, **kwargs): 
        self.in_stream = in_stream
        self.W = window_size
        self.A = anomaly_size
        self.F = anomaly_factor
        self.C = cloud_data_size
        self.cloud_func = cloud_func
        self.kwargs = kwargs
        self.in_stream.subscribe(self.callback)
        self.anomaly = False
    def callback(self):
        start = self.in_stream.start[self.callback]
        stop = self.in_stream.stop
        R = self.in_stream.recent

        while ((self.anomaly and stop - start >= self.C) or
                   (not self.anomaly and start + self.W <= stop)):
            if self.anomaly:
                data_to_cloud = R[start : start+self.C]
                self.anomaly = False
                start += self.C
                self.in_stream.set_start(self.callback, start)
                self.cloud_func(data_to_cloud, **self.kwargs)
            else:
                window = R[start : start + self.W]
                window_mean = np.mean(window[:self.A])
                window_std = np.std(window[:self.A])
                anomaly_mean = np.mean(window[-self.A: ])
                # if (np.abs(np.mean(window[-self.A: ])) >
                #         np.abs(np.mean(window)*self.F)):
                if (np.abs(anomaly_mean - window_mean) > self.F * window_std):
                    # print(window[-self.A: ].shape)
                    # print(window.shape)

                    # print(window[-self.A: ])
                    # print(window)

                    # print(window_mean, window_std, anomaly_mean, np.abs(anomaly_mean - window_mean))
                    # print()
                    self.anomaly = True
                    # print(window)
                    print('window_mean:', window_mean)
                    print('window_std: ', window_std)
                    print('anomaly_mean: ', anomaly_mean)
                    start += self.W - self.A
                    self.in_stream.set_start(self.callback, start)
                else:
                    start += 1
                    self.in_stream.set_start(self.callback, start)


def append_item_to_stream(v, out_stream):
    out_stream.append(v)

def append_item_to_StreamArray(v, out_stream):
    out_stream.append(np.stack(v, axis=0))



#------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------
def example_single_item():

    x, y, z = Stream(name='x'), Stream(name='y'), Stream(name='z')

    # Examples of functions passed to map_stream objects below
    # Function f has two parameters: an item v of the input stream
    # and a keyword parameter, out_stream, which is the output stream.
    def f(v, out_stream): 
        out_stream.append(2*v)

    # This function has three parameters: the first is an item v of the
    # input stream, the second is a keyword argument (see kwargs) out_stream,
    # which is the output stream, and another keyword argument, multiplier.
    def h(v, out_stream, multiplier): 
        out_stream.append(multiplier*v)

    # Set up the agent with input stream x and output stream y.
    single_item(in_stream=x, out_stream=y, func=f)
    # Set up the agent with input stream x and output stream z.
    single_item(in_stream=x, out_stream=z, func=h, multiplier=3)

    # Put values into input stream x.
    x.extend([0, 1, 2])
    # Run agents until all streams have been processed.
    run()
    # Functions f and h are called when stream x is extended.
    
    # Print the streams.
    x.print_recent()
    y.print_recent()
    z.print_recent()
    # y[i] = 2*x[i]), and z[i] = multiplier*x[i])

    # Put more values into input stream x.
    x.extend([3, 4])
    run()
    # Functions f and h are called when stream x is extended.
    
    # Print the output streams.
    x.print_recent()
    y.print_recent()
    z.print_recent()
    

def example_join_synch():

    def f(v, out_stream, multiplier):
        out_stream.append(sum(v) * multiplier)
        return

    x, y, z = Stream(name='x'), Stream(name='y'), Stream(name='z')
    join_synch(in_streams=[x, y], out_stream=z, func=f, multiplier=3)

    x.extend([0, 1, 2])
    y.extend([10, 11, 12, 13])
    run()
    x.print_recent()
    y.print_recent()
    z.print_recent()

    x.extend([3, 4, 5, 6])
    y.extend([10, 11, 12, 13, 14])
    run()
    x.print_recent()
    y.print_recent()



def example_join_asynch():
    def f(v, out_stream, multiplier):
        out_stream.append(v * multiplier)
        return

    x, y, z = Stream(name='x'), Stream(name='y'), Stream(name='z')
    join_asynch(in_streams=[x, y], out_stream=z, func=f, multiplier=3)

    x.extend([0, 1])
    y.extend([10])
    run()
    x.print_recent()
    y.print_recent()
    z.print_recent()

    x.extend([2])
    run()
    x.print_recent()
    y.print_recent()
    z.print_recent()

    y.extend([11])
    run()
    x.print_recent()
    y.print_recent()
    z.print_recent()


def example_join_timed():
    def get_time(v):
        return v[0]

    def f(v, out_stream):
        out_stream.append(v)
        return

    x, y, z = Stream(name='x'), Stream(name='y'), Stream(name='z')
    join_timed(in_streams=[x, y], func=f, get_time=get_time, out_stream=z)

    x.extend([(1, 0), (10, 1)])
    y.extend([(2, 'A'), (4, 'B')])
    run()
    x.print_recent()
    y.print_recent()
    z.print_recent()

    y.extend([(12, 'C')])
    run()
    x.print_recent()
    y.print_recent()
    z.print_recent()

    x.extend([(12, 2)])
    run()
    x.print_recent()
    y.print_recent()
    z.print_recent()


def example_sliding_window():
    def g(window, out_stream):
        out_stream.append(sum(window))
        return

    x, y = Stream(name='x'), Stream(name='y')
    sliding_window(in_stream=x, window_size=3, step_size=2, func=g, out_stream=y)

    x.extend(list(range(10)))
    run()
    x.print_recent()
    y.print_recent()



# EXAMPLE OF subtract_mean_from_StreamArray

def append_item_to_StreamArray(v, out_stream):
    out_stream.append(np.stack(v, axis=0))

from stream import StreamArray

def example_subtract_mean_from_StreamArray():
    xx = StreamArray(name='xx', dtype=float, dimension=2)
    yy = StreamArray(name='yy', dtype=float, dimension=2)
    subtract_mean_from_StreamArray(
        in_stream=xx, out_stream=yy, window_size=3, 
        func=append_item_to_StreamArray)
    
    xx.extend([np.array([0., 1.]), np.array([2., 1.]), 
               np.array([1., 1.]), np.array([2., 2.]), 
               np.array([2., 1.])])
    run()
    xx.print_recent()
    yy.print_recent()



# EXAMPLE ILLUSTRATING example_subtract_mean_from_stream

import numpy as np

def append_item_to_stream(v, out_stream): out_stream.append(v)

def example_subtract_mean_from_stream():
    x, y = Stream(name='x'), Stream(name='y')
        
    subtract_mean_from_stream(
        in_stream=x, window_size=3, 
        func=append_item_to_stream, out_stream=y)
    
    x.extend([0, 1, 2, 1, 1, 1, 2, 2, 2, 1])
    run()
    x.print_recent()
    y.print_recent()



def example_detect_anomaly():
    def cloud_func(window, ):
        print ('window ', window)
        return

    x = Stream(name='x')
    detect_anomaly(in_stream=x, window_size=4, anomaly_size=2,
                       anomaly_factor=1.1, cloud_data_size=2,
                       cloud_func=cloud_func)
    x.extend([1, 1, 2, 2, 3, 4, 7, 6, 11, 0, 3, 5, 5, 11, 11, 19, 19, 31])
    run()
    x.print_recent()


def example_detect_anomaly_with_StreamArray():
    def cloud_func(window, ):
        print ('window ', window)
        return

    x = StreamArray(name='x', dtype='float', dimension=2)
    
    detect_anomaly(in_stream=x, window_size=3, anomaly_size=1,
                       anomaly_factor=1.1, cloud_data_size=2,
                       cloud_func=cloud_func)

    x.extend([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0], [7.0, 6.0], [11.0, 6.0], [2.0, 1.0], [18.0, 16.0], [2.0, 4.0]])
    run()

    x.extend([[0.0, 1.0], [8.0, 9.0], [12.0, 15.0], [1.0, 2.0], [21.0,
    31.0], [0.0, 0.0], [0., 0.]])
    run()


if __name__ =='__main__':
    print('example_single_item')
    example_single_item()
    print('')
    print('example_join_synch')
    example_join_synch()
    print('')
    print('example_join_asynch')
    example_join_asynch()
    print('')
    print('example_join_timed')
    example_join_timed()
    print('')
    print('example_sliding_window')
    example_sliding_window()
    print('')
    print('example_subtract_mean_from_stream')
    example_subtract_mean_from_stream()
    print('')
    print('example_subtract_mean_from_StreamArray')
    example_subtract_mean_from_StreamArray()
    print('')
    print('example_detect_anomaly')
    example_detect_anomaly()
    print('')
    print('example_detect_anomaly_with_StreamArray')
    example_detect_anomaly_with_StreamArray()

