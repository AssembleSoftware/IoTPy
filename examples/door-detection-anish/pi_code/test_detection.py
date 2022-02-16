import numpy as np
from anom_detect import anom_detect
from pathlib import Path

def pred_moving_avg(X):
    '''
    Predicts if this sample corresponds to a door opening or not
    If it does, determines left and right checkpoints
    '''
    # For each timstep, convert measurements to avg of 4 sensor magnitudes
    num_timesteps = X.shape[0]
    X_mag = np.zeros((num_timesteps, 1))
    for timestep in range(num_timesteps):
        magnitude_avg = 0
        for i in range(4):
            magnitude_avg += np.linalg.norm(X[timestep, i])
        magnitude_avg /= 4
        X_mag[timestep] = magnitude_avg
    
    # Get rolling average
    an = anom_detect(window=5)
    an.evaluate(X_mag, anom_detect=False)
    mv_avgs = an.rolling_mean
    
    # left and right marker denote begining and start of signal
    left_marker = np.argwhere(mv_avgs > 0.1)
    right_marker = np.argwhere(np.flip(mv_avgs) > 0.1)
    if len(left_marker) == 0:
        print("Negative")
        return 0
    
    left_marker = left_marker[0]
    right_marker = mv_avgs.shape[0] - right_marker[0]
    
    # Add a little bit of data at the bounds of the signal
    left_marker -= 10
    right_marker += 10
    
    # Trim to avoid out of bounds
    left_marker = max(left_marker, 0)
    right_marker = min(right_marker, X_mag.shape[0])
    an.plot(left_marker, right_marker)
    return 1
    
def validate(method):
    '''
    Apply method on all data points and score it
    '''
    pos_directory = Path('./samples/positive/')
    neg_directory = Path('./samples/negative/')
    
    for f in pos_directory.glob('*'):
        # X = np.load('./samples/positive/23:15:53_1.npy')
        X = np.load(f)
        y = 1
        pred = method(X)
    
    for f in neg_directory.glob('*'):
        X = np.load(f)
        y = 0
        pred = method(X)

validate(pred_moving_avg)