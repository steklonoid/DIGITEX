import numpy as np
from matplotlib import pyplot as plt


def mnk(xlist, ylist):
    n = np.size(xlist)
    sx = np.sum(xlist)
    sy = np.sum(ylist)
    sxy = np.sum(np.multiply(xlist, ylist))
    sxx = np.sum(np.square(xlist))
    a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    b = (sy - a * sx) / n
    sigma = np.sum(np.square(np.subtract(ylist, a * xlist + b)))
    return (a, b, sigma)

# arr = np.loadtxt('history.csv', delimiter=',')
# arr = np.array([[1, 1], [2, 2], [3, 1], [4, 2], [5, 1], [6, 2], [7, 3], [8, 2], [9, 1], [10, 2], [11, 1], [12, 2], [13, 1], [14, 2], [15, 1], [16, 2], [17, 1]])
arr = np.loadtxt('./files/USDT_ETH_2h_neyro.txt', delimiter=';', skiprows=1, usecols=(1, 2, 3))
# arr_prepared = np.zeros((arr.shape[0] - 1, 3))
arrlen = arr.shape[0]
print(arrlen)
# arrlen = arr_prepared.shape[0]
# for i in range(arr_prepared.shape[0]):
#     arr_prepared[i] = [arr[i + 1, 0], max(arr[i + 1, 1], arr[i, 1]), min(arr[i + 1, 1], arr[i, 1])]

intervals = [10, 500, 10000]
interval_log = np.log(intervals)

arr_out = np.zeros((arrlen - intervals[-1] + 1, 6))
for i in range(arrlen - intervals[-1] + 1):
# i = 0
    list_bar =arr[i:i + intervals[-1], [1, 2]]
    vj = [np.sum(np.subtract(np.amax(np.reshape(list_bar[:, 0], (interval, -1)), axis=1),
                             np.amin(np.reshape(list_bar[:, 1], (interval, -1)), axis=1))) for interval in intervals]

    vj_log = np.log(vj)
    (a, b, sigma) = mnk(interval_log, vj_log)

    arr_out[i] = [arr[i + intervals[-1] - 1, 0], arr[i + intervals[-1] - 1, 1], arr[i + intervals[-1] - 1, 2], a, b, sigma]

np.savetxt('USDT_ETH_2h_neyro_fk_' + str(intervals[0]) + '-' + str(intervals[-1]) + '.csv', arr_out, delimiter=',', header=str(intervals), fmt=['%d', '%16.8f', '%16.8f', '%16.8f', '%16.8f', '%16.8f'])

fig, axs = plt.subplots(4, 1, sharex=True)
# Remove horizontal space between axes
fig.subplots_adjust(hspace=0)

# Plot each graph, and manually set the y tick values
axs[0].plot(arr_out[:, 0], arr_out[:, 3])
axs[0].set_ylabel('a', fontsize=12)
axs[1].plot(arr_out[:, 0], arr_out[:, 4])
axs[1].set_ylabel('b', fontsize=12)
axs[2].plot(arr_out[:, 0], arr_out[:, 5])
axs[2].set_ylabel('sigma', fontsize=12)
axs[3].plot(arr_out[:, 0], arr_out[:, 1])
axs[3].set_ylabel('max', fontsize=12)
plt.show()

