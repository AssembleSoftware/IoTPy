import numpy as np
"""
This module defines an incremental buffer that is used in Incremental PCA.

"""
class incremental_buffer(object):
    """
    Parameters
    ----------
    size: int
      positive int which is the maximum number of rows of the buffer.
      The buffer is a 2D numpy array.

    Attributes
    ----------
    value: np.ndarray
      This is the 2D numpy array in which data is stored.
      It is a circular buffer.
    num_features: int
       positive integer which is the number of columns of the buffer array.
       It is also the number of features in the PCA algorithm.
    num_samples: int
       positive integer which is the number of samples used in PCA. It is
       the number of samples that have been retained in the buffer.

    """
    def __init__(self, size):
        self.size = size
        self.SLACK_NUM = 2
        self.buf_size = self.size*self.SLACK_NUM
        self.value = None
        # value is created on the first call to extend().
        self.num_features = 0
        # The number of features (i.e. columns of the array) is set on the
        # first call to extend().
        self.num_samples = 0
    def extend(self, input):
        """
        Parameters
        ----------
        input: A two-dimensional array. A matrix (not necessarily square).

        """
        # Verify that input is a 2-D array.
        assert len(input.shape) == 2

        num_new_entries, num_features = input.shape
        # num_new_entries is the number of rows of the input
        # num_features is the number of columns. This must remain unchanged
        # for all input.
        #input_size = len(input)

        # The number of new entries must not exceed size.
        assert num_new_entries <= self.size

        if self.num_samples == 0:
            # This case deals with the initial call to extend.
            self.num_features = num_features
            # num_features will remain unchanged from now on.
            # value is an array where the number of rows is self.buf_size and
            # the number of columns is self.num_features
            self.value = np.zeros((self.buf_size, self.num_features))
            # Put the input into the buffer, i.e., into value.
            self.num_samples = num_new_entries
            # self.num_samples is the total number of samples in self.value.
            self.value[:num_new_entries] = input
            # self.value[0:self.num_samples] contains data and
            # self.value[self.num_samples:] is arbitrary.
        elif self.num_samples + num_new_entries < self.buf_size:
            # This is a second or later call to extend.
            # So, self.num_features has been determined by the initial call.
            assert self.num_features == num_features
            # The total number of samples in the buffer, after inserting the
            # new input, is less than self.buf_size; so, put the input data
            # directly into the buffer without wrapping around the end of
            # the circular buffer.
            new_num_samples = self.num_samples + num_new_entries
            # self.value[:self.num_samples] has data and
            # self.value[self.num_samples: ] is arbitrary. So, put
            # the input into the empty slots.
            self.value[self.num_samples : new_num_samples] = input
            self.num_samples = new_num_samples
            # self.num_samples is the number of elements in the buffer
            # after the input has been inserted.
        else:
            # The buffer is never completely full because we compact
            # the buffer before that happens.
            assert self.num_samples < self.buf_size
            # This is a second or later call to extend, and so
            # self.num_features is fixed.
            gap = self.size - num_new_entries
            assert gap >= 0
            self.value[:gap] = self.value[self.num_samples-gap:self.num_samples]
            self.value[gap : gap+num_new_entries] = input
            new_num_samples = gap + num_new_entries
            # Put the input into the freed-up slots at the bottom of buffer.
            self.value[gap:new_num_samples ] = input
            self.num_samples = new_num_samples
        return
        ## elif self.num_samples < self.buf_size:
        ##     # This is a second or later call to extend, and so
        ##     # self.num_features is fixed.
        ##     # The size of the input (num_samples) is  strictly less 
        ##     # than the buffer size; so, the buffer has at least one
        ##     # empty slot.
        ##     gap = self.buf_size - self.num_samples
        ##     # gap is the number of free slots remaining in the buffer.
        ##     # Now move the elements in circular buffer up by just enough
        ##     # slots to make space for the remaining elements of the input.
        ##     self.value = np.roll(self.value,-(num_new_entries-gap), axis=0)
        ##     # Put the input into the freed-up slots at the bottom of buffer.
        ##     self.value[-num_new_entries: ] = input
        ##     self.num_samples = self.buf_size
        ##     # The buffer is now completely full. So, number of samples is
        ##     # the buffer size
        ## else:
        ##     # self.num_samples == self.buf_size
        ##     # The buffer is completely full.
        ##     # Move the buffer up by the number of new entries to make
        ##     # space for the input.
        ##     self.value = np.roll(self.value,-num_new_entries, axis=0)
        ##     self.value[-num_new_entries: ] = input
        ## return


#---------------------------------------------------------------------
#          TEST
#---------------------------------------------------------------------
def test_incremental_buffer():
    z = incremental_buffer(3)
    z.extend(np.array([[1, 2, 3], [4, 5, 6]]))
    expected = np.array([[1., 2., 3.], [4., 5., 6.]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[7, 8, 9], [10, 11, 12]]))
    expected = np.array([[1., 2., 3.], [4., 5., 6.],
                         [7., 8., 9.], [10., 11., 12.]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[13, 14, 15], [16, 17, 18], [19, 20, 21]]))
    expected = np.array([[13., 14., 15.], [16., 17., 18.], [19., 20., 21.]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[22, 23, 24], [25, 26, 27]]))
    expected = np.array([[13., 14., 15.], [16., 17., 18.],
                         [19., 20., 21.], [22., 23., 24.],
                         [25., 26., 27.]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[28, 29, 30], [31, 32, 33], [34, 35, 36]]))
    expected = np.array([[28, 29, 30], [31, 32, 33], [34, 35, 36]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[37, 38, 39]]))
    expected = np.array([[28, 29, 30], [31, 32, 33], [34, 35, 36], [37, 38, 39]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[40, 41, 42]]))
    expected = np.array([[28, 29, 30], [31, 32, 33], [34, 35, 36], [37, 38, 39],
                         [40, 41, 42]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[43, 44, 45]]))
    expected = np.array([[37, 38, 39], [40, 41, 42], [43, 44, 45]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[46, 47, 48]]))
    expected = np.array([[37, 38, 39], [40, 41, 42], [43, 44, 45], [46, 47, 48]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[49, 50, 51]]))
    expected = np.array([[37, 38, 39], [40, 41, 42], [43, 44, 45], [46, 47, 48],
                         [49, 50, 51]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[52, 53, 54]]))
    expected = np.array([[46, 47, 48], [49, 50, 51], [52, 53, 54]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    z.extend(np.array([[54, 55, 56], [57, 58, 59], [60, 61, 62]]))
    expected = np.array([[54, 55, 56], [57, 58, 59], [60, 61, 62]])
    assert np.array_equal(z.value[:z.num_samples], expected)

    print ('Test is successful')

if __name__ == '__main__':
    test_incremental_buffer()
    
    
             
    
