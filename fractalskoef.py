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

#   входные данные в формате UTS; MAX; MIN;
name = 'USDT_BTC_2h_neyro'
arr = np.loadtxt('./files/' + name + '.csv', delimiter=';', skiprows=1, usecols=(1, 2, 3))
arrlen = arr.shape[0]
print(arrlen)

intervals = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
interval_log = np.log(intervals)

arr_out = np.zeros((arrlen - intervals[-1] + 1, 6))
for i in range(arrlen - intervals[-1] + 1):
    list_bar =arr[i:i + intervals[-1], [1, 2]]
    vj = [np.sum(np.subtract(np.amax(np.reshape(list_bar[:, 0], (interval, -1)), axis=1),
                             np.amin(np.reshape(list_bar[:, 1], (interval, -1)), axis=1))) for interval in intervals]

    vj_log = np.log(vj)
    (a, b, sigma) = mnk(interval_log, vj_log)

    arr_out[i] = [arr[i + intervals[-1] - 1, 0], arr[i + intervals[-1] - 1, 1], arr[i + intervals[-1] - 1, 2], a, b, sigma]

max_absigma = np.amax(arr_out[:, [3, 4, 5]], axis=0)
min_absigma = np.amin(arr_out[:, [3, 4, 5]], axis=0)
mean_absigma = np.mean(arr_out[:, [3, 4, 5]], axis=0)
std_absigma = np.std(arr_out[:, [3, 4, 5]], axis=0)

strheader = str(intervals) + '\n' + 'max(a, b, sigma)=' + str(max_absigma) + '\n' + 'min(a, b, sigma)=' + str(min_absigma) + '\n' + 'mean(a, b, sigma)=' + str(mean_absigma) + '\n' + 'std(a, b, sigma)=' + str(std_absigma)
np.savetxt('./files/' + name + '_fk_' + str(intervals[0]) + '-' + str(intervals[-1]) + '.csv', arr_out, delimiter=',', header=strheader, fmt=['%d', '%16.8f', '%16.8f', '%16.8f', '%16.8f', '%16.8f'])

fig, axs = plt.subplots(4, 1, sharex=True)
# Remove horizontal space between axes
fig.subplots_adjust(hspace=0.5)
# Plot each graph, and manually set the y tick values
axs[0].plot(arr_out[:, 0], arr_out[:, 3])
axs[0].set_ylabel('a', fontsize=12)
axs[0].set_title('min=' + str(round(min_absigma[0], 4)) + ' max=' + str(round(max_absigma[0], 4)) + ' std=' + str(round(std_absigma[0], 4)))
axs[1].plot(arr_out[:, 0], arr_out[:, 4])
axs[1].set_ylabel('b', fontsize=12)
axs[1].set_title('min=' + str(round(min_absigma[1], 4)) + ' max=' + str(round(max_absigma[1], 4)) + ' std=' + str(round(std_absigma[1], 4)))
axs[2].plot(arr_out[:, 0], arr_out[:, 5])
axs[2].set_ylabel('sigma', fontsize=12)
axs[2].set_title('min=' + str(round(min_absigma[2], 4)) + ' max=' + str(round(max_absigma[2], 4)) + ' std=' + str(round(std_absigma[2], 4)))
axs[3].plot(arr_out[:, 0], arr_out[:, 1])
axs[3].set_ylabel('max', fontsize=12)
plt.show()
