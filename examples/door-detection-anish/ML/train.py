import numpy as np
import os
import pickle
from sktime.classification.distance_based import KNeighborsTimeSeriesClassifier
from sklearn.utils import shuffle
from sktime.classification.compose import ColumnEnsembleClassifier
from joblib import dump

anish = []
directory = './data_live/data/anish'
for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(f):
        anish.append(np.load(f))

kevin = []
directory = './data_live/data/kevin'
for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    # checking if it is a file
    if os.path.isfile(f):
        kevin.append(np.load(f))

# First 21 is anish, next 14 are kevin
X = np.concatenate((np.array(anish), np.array(kevin)))
y = np.array([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
X, y = shuffle(X, y)
print(X.shape)
print(y.shape)

# Save model
estimators = [(f"knn_{i}", KNeighborsTimeSeriesClassifier(distance="dtw", n_neighbors=2), i) for i in range(12)]
col_ens = ColumnEnsembleClassifier(estimators=estimators)

# Sanity check, predict on entire set
col_ens.fit(X, y)
y_pred = col_ens.predict(X)
print(y_pred.shape)
print(sum(y_pred == y)/35)

dump(col_ens, 'model.joblib')