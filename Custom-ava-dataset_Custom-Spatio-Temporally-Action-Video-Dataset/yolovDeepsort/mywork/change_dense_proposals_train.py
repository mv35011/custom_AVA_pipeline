import pickle
import numpy as np

input_path = '../../Dataset/annotations/dense_proposals_train.pkl'
with open(input_path, 'rb') as f:
    info = pickle.load(f, encoding='iso-8859-1')

dense_proposals_train = {}

for i in info:
    tempArr = np.array(info[i])
    dicts = []
    for temp in tempArr:
        temp = temp.astype(np.float64)
        temp[temp < 0] = 0.0
        temp[temp > 1] = 1.0
        dicts.append(temp)
    dense_proposals_train[i] = np.array(dicts)
with open(input_path, "wb") as pklfile:
    pickle.dump(dense_proposals_train, pklfile)

print(f"[✓] Cleaned dense_proposals_train.pkl saved to: {input_path}")
