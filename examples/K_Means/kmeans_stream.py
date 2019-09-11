import sys
import os
import numpy as np
from sklearn.cluster import KMeans
sys.path.append(os.path.abspath("../../IoTPy/helper_functions/"))
sys.path.append(os.path.abspath("../../IoTPy/core/"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
from helper_control import _no_value
from run import run
from recent_values import recent_values
from basics import map_e
from stream import Stream
from op import map_element

class kmeans_stream(object):
    def __init__(self, n_clusters=8):
        self.n_clusters = n_clusters
        self.data = []
        self.kmeans = None
        self.cluster_centers = None
        self.predictions = None

    def process_element(self, v):
        if v == 'cluster':
            return self.cluster()
        elif v == 'show':
            return self.show()
        elif len(v) != 2:
            raise ValueError("element is not cluster or show")
        else:
            command, value = v
            if command == 'add':
                return self.add(value)
            elif command == 'add_update':
                return self.add_update(value)
            elif command == 'delete':
                return self.delete(value)
            elif command == 'delete_update':
                return self.delete_update(value)
            else:
                raise ValueError(
                    "command is {0}. Must be 'add' or 'delete.' ".format(
                        command))

    def compute_kmeans(self, init, n_init=10):
        if len(self.data) < self.n_clusters:
            raise ValueError(
                'Number of clusters, {0}, cannot exceed data length: {1}.'. format(
                    self.n_clusters, len(self.data)))
        self.kmeans = KMeans(
            algorithm='auto', copy_x=True, init=init,
            max_iter=300, n_clusters=self.n_clusters, n_init=n_init,
            n_jobs=None, precompute_distances='auto',
            random_state=None, tol=0.0001, verbose=0)
        self.predictions = self.kmeans.fit(np.array(self.data))
        self.cluster_centers = self.predictions.cluster_centers_
        self.labels = self.predictions.labels_

    def cluster(self):
        self.compute_kmeans(init='random')
        return _no_value

    def show(self):
        if self.predictions == None:
            raise ValueError(' Must first run cluster() at least once.')
        output = []
        for j in range(len(self.data)):
            output.append((self.data[j], self.labels[j]))
        return output

    def add(self, v):
        self.data.append(v)
        return _no_value

    def add_update(self, v):
        self.data.append(v)
        self.compute_kmeans(init=self.cluster_centers, n_init=1)
        return _no_value

    def extend(self, v):
        self.data.extend(v)
        return _no_value

    def delete(self, v):
        try:
            self.data.remove(v)
        except:
            ValueError('Cannot delete {0} which is not in {1}'.format(
                v, self.data))
        return _no_value

    def delete(self, v):
        try:
            self.data.remove(v)
        except:
            ValueError('Cannot delete {0} which is not in {1}'.format(
                v, self.data))
        return _no_value

    def delete_list(self, lst):
        for v in lst:
            try:
                self.data.remove(v)
            except:
                ValueError('Cannot delete {0} which is not in {1}'.format(
                    v, self.data))
        self.compute_kmeans(init=self.cluster_centers)
        return _no_value

def test_kmeans():
    # Used only without map_e decorator
    a = kmeans_stream(n_clusters=2)
    a.add([1, 2])
    a.add([1, 4])
    a.add([1, 0])
    a.add([10, 4])
    a.add([10, 0])
    a.add([10, 2])
    a.cluster()
    print(a.show())
    a.add([1, 2])
    a.cluster()
    print(a.show())

    a.delete([1, 2])
    a.add_update([1, 4])
    a.add_update([1, 10])
    print(a.show())

def test_kmeans_streams():
    s = Stream()
    t = Stream()
    km = kmeans_stream(n_clusters=2)

    @map_e
    def g(v):
        return km.process_element(v)

    g(in_stream=s, out_stream=t)
    s.append(('add', [1, 2]))
    s.append(('add', [1, 4]))
    s.append(('add', [1, 0]))
    s.append(('add', [10, 4]))
    s.append(('add', [10, 0]))
    s.append(('add', [10, 2]))
    s.append('cluster')
    s.append('show')
    
    ## s.extend([('add', [1, 2]), ('add', [1, 4]), ('add', [1, 0]),
    ##           ('add', [10, 4]), ('add', [10, 0]), ('add', [10, 2])])
    run()
    print (recent_values(t))
    

if __name__ == '__main__':
    test_kmeans_streams()
    
            
            
        
        
            
