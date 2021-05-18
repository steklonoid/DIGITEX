import numpy as np
from matplotlib import pyplot as plt

TRAIN = 60000
VAL = 30000
TEST = 18000

NUM = 512

arr = np.loadtxt('history.csv', delimiter=',')
arrlen = arr.shape[0]

# plt.plot(arr[:, 0], arr[:, 1])
# plt.show()

arr1 = np.zeros((10, 5, 2))
print(arr1)
