"""
This code implements the streaming version of scikit learn's IPCA algorithm - 
https://github.com/scikit-learn/scikit-learn/blob/7813f7efb/sklearn/decomposition/incremental_pca.py
"""

import numpy as np
import pickle as p
import sys
import os
from sklearn.utils.extmath import svd_flip
from IPCAutils import _incremental_mean_and_var

from scipy import linalg
sys.path.append(os.path.abspath("../../IoTPy/multiprocessing"))
sys.path.append(os.path.abspath("../../IoTPy/core"))
sys.path.append(os.path.abspath("../../IoTPy/agent_types"))
sys.path.append(os.path.abspath("../../IoTPy/helper_functions"))


from multicore import shared_memory_process, Multiprocess
from stream import Stream
from source import source_list, source_list_to_stream
from sink import sink_window
from recent_values import recent_values


source_list = [[1,5,0.1],[3,1,-0.1],[3,7,0.2],[-4,4,-0.3],[-1,-5,0.1],[2,0,0.2],[3,3,-0.2],[-4,8,0],[-7,-2,0.1],'eof']
#source_list = np.array(source_list)



def source(out_stream):
    return source_list_to_stream(source_list, out_stream)

def make_and_run_process(compute_func):
    proc = shared_memory_process(
        compute_func=compute_func,
        in_stream_names=['in'],
        out_stream_names=[],
        connect_sources=[('in', source)],
        connect_actuators=[],
        name='proc')
    mp = Multiprocess(processes=[proc], connections=[])
    mp.run()



def IPCA(k = 5,batches = 25):





    class IPCAValues:
            
        def __init__(self,k):
                self.n_components_ = k
                self.n_samples_seen_ = 0
                self.components_ = None
                self.mean_ = .0
                self.var_ = .0
                self.singular_values_ = None
                self.explained_variance_ = None
                self.explained_variance_ratio_ = None
                self.singular_values_ = None
                self.noise_variance_ = None
                self.count = 0



    state = IPCAValues(k)
            

    
    def compute_func(in_streams, out_streams):


        def partial_fit(X, state):
            """Incremental fit with X. All of X is processed as a single batch.
            Parameters
            ----------
            X : array-like, shape (n_samples, n_features)
                Training data, where n_samples is the number of samples and
                n_features is the number of features.
            
            Returns
            -------
            self : object
                Returns the instance itself.
            """

            end = False
            print(X[0])
            if X[-1] == 'eof':
                end = True
                X= X[:-1]

            X = np.array(X,dtype = 'float64')
            n_samples, n_features = X.shape
            state.count += n_samples

            
            # Update stats - they are 0 if this is the fisrt step

            
            col_mean, col_var, n_total_samples = \
                _incremental_mean_and_var(
                    X, last_mean=state.mean_, last_variance=state.var_,
                    last_sample_count=np.repeat(state.n_samples_seen_, X.shape[1]))
            n_total_samples = n_total_samples[0]

            # Whitening
            if state.n_samples_seen_ == 0:
                # If it is the first step, simply whiten X
                X -= col_mean
            else:
                col_batch_mean = np.mean(X, axis=0)
                X -= col_batch_mean
                # Build matrix of combined previous basis and new data
                mean_correction = \
                    np.sqrt((state.n_samples_seen_ * n_samples) /
                            n_total_samples) * (state.mean_ - col_batch_mean)
                X = np.vstack((state.singular_values_.reshape((-1, 1)) *
                              state.components_, X, mean_correction))

            U, S, V = linalg.svd(X, full_matrices=False)
            U, V = svd_flip(U, V, u_based_decision=False)
            explained_variance = S ** 2 / (n_total_samples - 1)
            explained_variance_ratio = S ** 2 / np.sum(col_var * n_total_samples)

            state.n_samples_seen_ = n_total_samples
            state.components_ = V[:state.n_components_]
            state.singular_values_ = S[:state.n_components_]
            state.mean_ = col_mean
            state.var_ = col_var
            state.explained_variance_ = explained_variance[:state.n_components_]
            state.explained_variance_ratio_ = \
                explained_variance_ratio[:state.n_components_]
            if state.n_components_ < n_features:
                state.noise_variance_ = \
                    explained_variance[state.n_components_:].mean()
            else:
                state.noise_variance_ = 0.


            if state.count >= 999:
                    state.count = 0
                    print (state.components_)

            if end:
                np.savetxt("IPCA.dat", state.components_)

            return state
        




        

        
        

        
       
        sink_window(func = partial_fit, in_stream = in_streams[0], window_size = batches, step_size=batches, state = state )
    
        

        

        
    make_and_run_process(compute_func)

    

if __name__ == '__main__':
    
    print('Running the reverberation test ... ')
    IPCA(k = 2,batches = 5)
    print('reverb done')







