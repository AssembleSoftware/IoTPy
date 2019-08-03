def normalize_int_16(a, max_value):
        """
        Parameters
        ----------
        a: np.darray
           A 1-D array, i.e. vector
        max_value: int
           The expected maximum value of the array.

        Returns
        -------
        result: np.ndarray
           A 1-D array
           The input array is normalizd by max_value.

        """
        
        result = ((2**12) * a/max(a.max(), max_value)
        return result.astype('int16') 
