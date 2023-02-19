### The code EEL takes input x of dimension Q x 1 and returns output y of dimension Q x 2 where
### Q is the number of samples.

import numpy as np
import pandas as pd

def ANN(x):

    x = np.array(x)

    Tmin = -258 + 273.15
    Tmax = -240 + 273.15
    x = (x - Tmin) / (Tmax - Tmin)

    Q = len(x)

    x_xoffset = 0
    x_gain = 2
    x_ymin = -1

    # Layer 1
    b1 = [[10.35757697677199296], [11.598666688878049413], [-8.7792239655998631775], [-4.6104309070357052391],
          [-1.4955839343447343559], [-1.5628599258166584463], [4.6518542889999086043], [7.8523914793979221471],
          [-10.750394888534451354], [14.186483669451710909]]

    b1 = np.array(b1)

    IW1_1 = [[1.9080022131105405236], [-11.59539807783799148], [13.695943065336411593], [14.286419658458356707],
             [13.73131970853766326], [-13.992309270770107332], [13.990174129028265071], [14.130275287514134419],
             [-13.887306184181612778], [14.299712225324910264]]

    IW1_1 = np.array(IW1_1)

    # Layer 2
    b2 = [[10.072552180115035725], [2.132369754140571505]]
    b2 = np.array(b2)

    LW2_1 = [[-10.139661919862755113, -0.25003994609056784393, 0.22654236029935972963, 0.11461095113540953339,
              0.077230924297407202439, -0.077926631143471661312, 0.070581803644641533113,
              0.065894005912409805981, -0.061196286551330823789, 0.080467234510204266318],
             [-2.938590852955687005, -0.17924800529208079203, 0.011273008994426934187, 0.0016224911541086158365,
              0.00086512057185046935953, -0.00062327169531904507392, 0.00040310270090259552912, 0.000277472166367824318,
              3.5735423991604726871*10**(-5), 0.00065973131547274839123]]

    LW2_1 = np.array(LW2_1)

    # Output 1
    y1_ymin = -1
    y1_gain = [[5.74814438229587*10**(-6)], [1.0045629916181*10**(-6)]]
    y1_xoffset = [[-984039.45244745],[10922.0505419513]]


    xp1 = [(x[i][0]-x_xoffset)*x_gain+x_ymin for i in range(len(x))]

    a1 = np.empty((len(b1),0))
    a2 = np.array([])

    for i in range(len(xp1)):
        b3 = b1 + IW1_1*xp1[i]
        a = 2 / (1 + np.exp(-2*b3)) - 1
        a1 = np.append(a1, a, axis=1)

    a2 = np.repeat(b2, Q, axis=1) + np.matmul(LW2_1, a1)

    a3 = a2 - y1_ymin
    a3 = np.divide(a3, y1_gain)
    a3 = a3 + y1_xoffset

    y1 = np.transpose(a3)

    return y1[:,0]