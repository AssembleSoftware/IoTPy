import numpy as np

class incremental_buffer(object):
    def __init__(self, max_size):
        self.max_size = max_size
        self.value = None
        self.num_features = 0
        self.num_samples = 0
    def extend(self, input):
        assert len(input.shape) == 2
        num_new_entries, num_features = input.shape 
        input_size = len(input)
        assert input_size <= self.max_size
        if self.num_samples == 0:
            self.num_features = num_features
            self.value = np.zeros((self.max_size, self.num_features))
            self.num_samples = input_size
            self.value[:input_size] = input
        elif self.num_samples + input_size <= self.max_size:
            assert self.num_features == num_features
            new_num_samples = self.num_samples + input_size
            self.value[self.num_samples : new_num_samples] = input
            self.num_samples = new_num_samples
        elif self.num_samples < self.max_size:
            gap = self.max_size - self.num_samples
            self.value[self.num_samples : self.max_size] = \
              input[: gap]
            self.value = np.roll(self.value,-(input_size-gap), axis=0)
            self.value[-input_size: ] = input
            self.num_samples = self.max_size
        else:
            self.value = np.roll(self.value,-input_size, axis=0)
            self.value[-input_size: ] = input
        return

#---------------------------------------------------------------------
#          TEST
#---------------------------------------------------------------------
def test_incremental_buffer():
    z = incremental_buffer(5)
    z.extend(np.array([[1, 2, 3], [4, 5, 6]]))
    expected = np.array([[1., 2., 3.], [4., 5., 6.],
                         [0., 0., 0.], [0., 0., 0.],
                         [0., 0., 0.]])
    assert np.array_equal(z.value, expected)
    z.extend(np.array([[7, 8, 9], [10, 11, 12]]))
    expected = np.array([[1., 2., 3.], [4., 5., 6.],
                         [7., 8., 9.], [10., 11., 12.],
                         [0., 0., 0.]])
    assert np.array_equal(z.value, expected)
    z.extend(np.array([[13, 14, 15], [16, 17, 18], [19, 20, 21]]))
    expected = np.array([[7., 8., 9.], [10., 11., 12.],
                         [13., 14., 15.], [16., 17., 18.],
                         [19., 20., 21.]])
    assert np.array_equal(z.value, expected)
    z.extend(np.array([[22, 23, 24], [25, 26, 27]]))
    expected = np.array([[13., 14., 15.], [16., 17., 18.],
                         [19., 20., 21.], [22., 23., 24.],
                         [25., 26., 27.]])
    assert np.array_equal(z.value, expected)
    z.extend(np.array([[28, 29, 30], [31, 32, 33], [34, 35, 36]]))
    expected = np.array([[22., 23., 24.], [25., 26., 27.],
                         [28., 29., 30.], [31., 32, 33],
                         [34., 35., 36.]])
    assert np.array_equal(z.value, expected)

if __name__ == '__main__':
    test_incremental_buffer()
    
    
             
    
