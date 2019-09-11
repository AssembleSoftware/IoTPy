class Buffer:
    "A circular buffer"
    def __init__(self, max_size, name=None):
        assert max_size > 0
        self.max_size = max_size
        self.buffer_size = self.max_size+1
        self.start = 0
        self.end = 0
        self.count = 0
        self.data = [None]*self.buffer_size
        self.name = name

    def append(self, value):
        if self.count == 0:
            assert self.start == 0 and self.end == 0
            self.data[self.start] = value
            self.end = 1
            self.count = 1
            return
        # self.count > 0
        self.data[self.end] = value
        self.end = (self.end +1 ) % self.buffer_size
        self.count += 1
        if self.count > self.max_size:
            ## print 'self.start', self.start
            ## print 'self.end', self.end
            ## assert self.start == self.end
            ## print 'Buffer called {0} is full'.format(self.name)
            self.start = (self.start + 1) % self.buffer_size
            self.count = self.max_size

    def extend(self, alist):
        list_length = len(alist)
        assert (list_length <= self.max_size), \
          'Extending Buffer called {0} of size {1} with a list of length {2}'.format(
              self.name, self.max_size, list_length)
        if self.count == 0:
            assert self.start == 0 and self.end == 0
            self.data[self.start:self.start+list_length] = alist
            self.end = list_length
            self.count = list_length
            return
        # CASE: self.count > 0
        remaining_linear_space = self.buffer_size - self.end
        if self.count > self.max_size - list_length:
            # CASE: insufficient space to add alist. So delete old
            # values to make space for alist.
            print ('Buffer called {0} is full'.format(self.name))
            number_discard_old_data = self.count - (self.max_size - list_length)
            self.start = (self.start + number_discard_old_data) % self.buffer_size
            self.data[self.end:self.buffer_size] = alist[:remaining_linear_space]
            self.data[:list_length - remaining_linear_space] = alist[remaining_linear_space:]
            self.end = (self.end + list_length) % self.buffer_size
            self.count = self.max_size
            return

        # CASE: self.count > 0 and sufficient space to add alist
        if list_length <= remaining_linear_space:
            # CASE: sufficient linear space to add alist directly
            self.data[self.end:self.end+list_length] = alist
            self.count += list_length
            self.end += list_length
            return

        # CASE: list_length > remaining_linear_space
        # Cannot add alist directly. Break alist into two parts: the part to
        # add directly and the remainder.
        self.data[self.end:self.buffer_size] = alist[:remaining_linear_space]
        self.data[:list_length - remaining_linear_space] = alist[remaining_linear_space:]
        ## print 'self.start is', self.start
        ## print 'self.end is', self.end
        ## print 'remaining_linear_space', remaining_linear_space
        ## print 'alist', alist
        ## print 'self.data[self.end:self.buffer_size]', self.data[self.end:self.buffer_size]
        ## print 'self.data[:list_length - remaining_linear_space]', self.data[:list_length - remaining_linear_space]
        self.end = (self.end + list_length) % self.buffer_size
        self.count += list_length
        return

    def get_earliest(self):
        if self.count == 0:
            return None
        return_value = self.data[self.start]
        self.start = (self.start +1 ) % self.buffer_size
        self.count -= 1
        if self.count == 0:
            self.start = 0
            self.end = 0
        return return_value

    def get_earliest_n(self, n):
        n = min(n, self.count)
        if n == 0:
            return []
        if self.start + n <= self.buffer_size:
            return_value = self.data[self.start:self.start+n]
            self.start += n
            self.count -= n
            if self.count == 0:
                self.start = 0
                self.end = 0
            return return_value
        # CASE: self.start + n > self.buffer_size
        return_value = self.data[self.start:]
        return_value.extend(self.data[:n-self.buffer_size+self.start])
        self.start = n-self.buffer_size+self.start
        self.count -= n
        if self.count == 0:
            self.start = 0
            self.end = 0
        return return_value

    def get_all(self):
        if self.count == 0:
            return []
        if self.start < self.end:
            return_value = self.data[self.start:self.end]
            self.start = 0
            self.end = 0
            self.count = 0
            return return_value
        # CASE: self.end < self.start
        return_value = self.data[self.start:self.buffer_size]
        return_value.extend(self.data[:self.end])
        self.start = 0
        self.end = 0
        self.count = 0
        return return_value

    def get_number_in_buffer(self):
        return self.count

    def delete_earliest(self):
        if self.count == 0:
            return
        self.start = (self.start +1 ) % self.buffer_size
        self.count -= 1
        if self.count == 0:
            self.start = 0
            self.end = 0
        return

    def delete_earliest_n(self, n):
        n = min(n, self.count)
        if n == 0:
            return None
        if self.start + n <= self.buffer_size:
            self.start += n
            self.count -= n
            if self.count == 0:
                self.start = 0
                self.end = 0
            return
        # CASE: self.start + n > self.buffer_size
        self.start = n-self.buffer_size+self.start
        self.count -= n
        if self.count == 0:
            self.start = 0
            self.end = 0
        return

    def delete_all(self):
        self.start = 0
        self.end = 0
        self.count = 0
        return

    def read_earliest(self):
        if self.count == 0:
            return None
        return self.data[self.start]

    def read_earliest_n(self, n):
        n = min(n, self.count)
        if n == 0:
            return None
        if self.start + n <= self.buffer_size:
            return self.data[self.start:self.start+n]
        # CASE: self.start + n > self.buffer_size
        return_value = self.data[self.start:]
        return_value.extend(self.data[:n-self.buffer_size+self.start])
        return return_value

    def read_all(self):
        if self.count == 0:
            return None
        if self.start < self.end:
            return self.data[self.start:self.end]
        # CASE: self.end < self.start
        return_value = self.data[self.start:self.buffer_size]
        return_value.extend(self.data[:self.end])
        return return_value

    def get_up_to_time(self, time):
        return_value = []
        while self.count > 0:
            if self.data[self.start][0] <= time:
                return_value.append(self.data[self.start])
                self.start = (self.start + 1)%self.buffer_size
                self.count -= 1
            else:
                return return_value
        assert self.count == 0
        self.start = 0
        self.end = 0
        return return_value


def test_buffer():
    b = Buffer(2, 'a')
    b.append(10)
    print (b.get_earliest())
    print ('b.start is', b.start)
    print ('b.end is', b.end)

    b.append(20)
    b.append(30)
    print (b.get_earliest())
    print (b.get_earliest())
    print ('b.start is', b.start)
    print ('b.end is', b.end)

    b.append(40)
    b.append(50)
    b.append(60)
    print (b.get_earliest())
    print (b.get_earliest())
    print ('b.start is', b.start)
    print ('b.end is', b.end)

    b.extend([70, 80])
    print (b.get_earliest())
    print (b.get_earliest())
    print ('b.start is', b.start)
    print ('b.end is', b.end)

    b.extend([90, 100])
    print (b.get_earliest())
    print (b.get_earliest())
    print ('b.start is', b.start)
    print ('b.end is', b.end)

    b.append(110)
    b.append(120)
    print ('b.get_earliest_n(2)',b.get_earliest_n(2))
    #print b.get_earliest()

    b.append(130)
    print (b.get_earliest())
    print ('b.start is', b.start)
    print ('b.end is', b.end)

    b.append(140)
    print (b.get_earliest())
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())

    b.append(150)
    print ('b.get_earliest_n(2)',b.get_earliest_n(2))
    print ('b.get_earliest()', b.get_earliest())
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)

    b.append(160)
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())

    b.append(170)
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.get_earliest() should be 160:', b.get_earliest())
    print ('b.get_earliest() should be 170:', b.get_earliest())
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())

    b.extend([180, 190])
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print ('b.get_earliest() should be 180:', b.get_earliest())
    print ('b.get_earliest() should be 190:', b.get_earliest())
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())

    b.append(200)
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())

    b.extend([210])
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print ('b.read_earliest_n(1)', b.read_earliest_n(1))
    print ('b.read_earliest_n(2)', b.read_earliest_n(2))

    b.extend([220, 230])
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print ('b.read_earliest_n(1)', b.read_earliest_n(1))
    print ('b.read_earliest_n(2)', b.read_earliest_n(2))

    b.append(240)
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print ('b.read_earliest_n(1)', b.read_earliest_n(1))
    print ('b.read_earliest_n(2)', b.read_earliest_n(2))

    b.extend([250, 260])
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print ('b.read_earliest_n(1)', b.read_earliest_n(1))
    print ('b.read_earliest_n(2)', b.read_earliest_n(2))
    print (b.get_all())
    print ('b.get_earliest() is', b.get_earliest())

    b.append(270)
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('number in buffer is ', b.get_number_in_buffer())
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print ('b.read_earliest_n(1)', b.read_earliest_n(1))
    print ('b.read_earliest_n(2)', b.read_earliest_n(2))
    print (b.get_all())

    b.append(280)
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('number in buffer is ', b.get_number_in_buffer())
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print (b.get_all())

    b.extend([290, 300])
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('number in buffer is ', b.get_number_in_buffer())
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print (b.get_all())
    print ('b.get_earliest() is', b.get_earliest())

    b.extend([310])
    b.delete_all()
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print (b.get_all())

    b.append(320)
    b.delete_earliest()
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())
    print (b.get_all())

    b.extend([330, 340])
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())

    b.delete_earliest_n(2)
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())

    b.extend([350])
    b.delete_earliest_n(2)
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())

    b.extend([360, 370])
    b.delete_earliest_n(1)
    print ('b.start is', b.start)
    print ('b.end is', b.end)
    print ('b.count is ', b.count)
    print ('b.data', b.data)
    print ('b.read_earliest()', b.read_earliest())
    print ('b.read_all()', b.read_all())

    c = Buffer(10, 'c')
    c.append([10, 0])
    c.append([11, 1])
    print ('c.get_up_to_time(8)', c.get_up_to_time(8))
    print ('c.get_up_to_time(12)', c.get_up_to_time(12))
    print ('c.get_up_to_time(12) second time', c.get_up_to_time(12))

    c.extend([[14, 2], [16, 3]])
    c.extend([[18, 4]])
    c.append([20, 5])
    print ('c.get_up_to_time(18)', c.get_up_to_time(18))
    print ('c.get_up_to_time(24)', c.get_up_to_time(24))
    print ('c.get_up_to_time(10)', c.get_up_to_time(10))

if __name__ == '__main__':
    test_buffer()
            
    
