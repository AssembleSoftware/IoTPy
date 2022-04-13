from stream import Stream, run

class map_stream(object):
    def __init__(self, in_stream, out_stream, func, **kwargs):
        self.in_stream = in_stream
        self.out_stream = out_stream
        self.func = func
        self.in_stream.subscribe(self.callback)
        self.kwargs = kwargs
    def callback(self):
        self.out_stream.extend(
            [self.func(v, **self.kwargs) for v in self.in_stream.recent[
                self.in_stream.start[self.callback] : self.in_stream.stop]])
        self.in_stream.start[self.callback] = self.in_stream.stop

class join_synch(object):
    def __init__(self, in_streams, out_stream, func, **kwargs):
        self.in_streams = in_streams
        self.out_stream = out_stream
        self.func = func
        for in_stream in self.in_streams:
            in_stream.subscribe(self.callback)
        self.kwargs = kwargs
    def callback(self):
        slices = [in_stream.recent[in_stream.start[self.callback] : in_stream.stop]
                  for in_stream in self.in_streams]
        output = [self.func(v, **self.kwargs) for v in zip(*slices)]
        self.out_stream.extend(output)
        L = len(output)
        for in_stream in self.in_streams:
            in_stream.start[self.callback] += L

class join_asynch(object):
    def __init__(self, in_streams, out_stream, func, **kwargs):
        self.in_streams = in_streams
        self.out_stream = out_stream
        self.func = func
        for in_stream in self.in_streams:
            in_stream.subscribe(self.callback)
        self.kwargs = kwargs
    def callback(self):
        for in_stream in self.in_streams:
            self.out_stream.extend(
                [self.func(v, **self.kwargs) for v in in_stream.recent[
                    in_stream.start[self.callback]: in_stream.stop]])
            in_stream.start[self.callback] = in_stream.stop


class join_timed(object):
    def __init__(self, in_streams, out_stream, get_time, func, **kwargs):
        self.in_streams = in_streams
        self.out_stream = out_stream
        self.get_time = get_time
        self.func = func
        for in_stream in self.in_streams:
            in_stream.subscribe(self.callback)
        self.kwargs = kwargs
    def callback(self):
        while all([in_stream.start[self.callback] < in_stream.stop 
                   for in_stream in self.in_streams]):        
            items = [in_stream.recent[in_stream.start[self.callback]] 
                     for in_stream in self.in_streams]
            times = [self.get_time(item) for item in items]
            min_time = min(times)
            output = [None for in_stream in self.in_streams]
            for i, in_stream in enumerate(self.in_streams):
                if times[i] == min_time:
                    output[i] = self.func(items[i])
                    in_stream.start[self.callback] += 1
            self.out_stream.append((min_time, output,))


#------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------

def example_map_stream():
    x, y, z = Stream(name='x'), Stream(name='y'), Stream(name='z')

    # Examples of functions passed to map_stream objects below
    # Function ff has a a single parameter: an item v of a stream.
    def f(v): return 2*v
        
    # Function h has two parameters: the first is an item v of a
    # stream and the second is a keyword argument (see kwargs)
    def h(v, multiplier): return multiplier*v

    # Create map_stream objects
    map_stream(in_stream=x, out_stream=y, func=f)
    map_stream(in_stream=x, out_stream=z, func=h, multiplier=3)

    # Put values into input stream x.
    x.extend([0, 1, 2])
    run()

    # Functions f and h are called when stream x is extended.
    # Print the output streams.
    x.print_recent()
    y.print_recent()
    z.print_recent()
    # y[i] = f(x[i]), and z[i] = h(x[i])

    # Put values into input stream x.
    x.extend([3, 4])
    run()
    x.print_recent()
    y.print_recent()
    z.print_recent()

def example_join_synch():
    def f(v, multiplier): return sum(v) * multiplier
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
    z.print_recent()

def example_join_asynch():
    def f(v, multiplier): return v * multiplier
        
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
    
    def get_time(v): return v[0]
        
    def f(v): return v
        
    x, y, z = Stream(name='x'), Stream(name='y'), Stream(name='z')
    join_timed(in_streams=[x, y], out_stream=z, func=f, get_time=get_time)

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

    

if __name__ =='__main__':
    print('example_map_stream')
    example_map_stream()
    print('')
    print('example_join_synch')
    example_join_synch()
    print('')
    print('example_join_asynch')
    example_join_asynch()
    print('')
    print('example_join_timed')
    example_join_timed()
