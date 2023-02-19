import numpy as np
import pandas as pd

def ans(x):
    y1 = np.zeros((len(x), 1))
    for i in range(len(y1)):
        y1[i,0] = 0.92
    return y1

# x1 = [0.95,0.03,0.01,0.01,0,200,115,115]
# X = np.array([x1,x1,x1])
# print(X)
# print(ans(X))