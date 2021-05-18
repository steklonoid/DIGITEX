import numpy as np
from matplotlib import pyplot as plt

from keras import models
from keras import layers

NUM = 1000
LOOKBACK = 16

arr = np.loadtxt('history.csv', delimiter=',')
arrlen = arr.shape[0]

arrsin = np.zeros((NUM, 2))
for i in range(NUM):
    arrsin[i] = [i, (np.sin(20 * i / NUM) + 1) / 2]

x = np.zeros((NUM - LOOKBACK - 1, LOOKBACK))
y = np.zeros((NUM - LOOKBACK - 1, ))

for i in range(NUM - LOOKBACK - 1):
    x[i] = arrsin[i:i + LOOKBACK, 1]
    y[i] = arrsin[i + LOOKBACK + 1, 1]

x_test = x[:700]
x_val = x[700:]
y_test = y[:700]
y_val = y[700:]

model = models.Sequential()
model.add(layers.Dense(LOOKBACK // 2,  activation='relu', input_shape=(LOOKBACK,)))
model.add(layers.Dense(LOOKBACK // 4,  activation='relu'))
model.add(layers.Dense(1, activation='sigmoid'))

model.compile(optimizer='rmsprop',
 loss='binary_crossentropy',
 metrics=['accuracy'])

history = model.fit(x_test, y_test, epochs=20, batch_size=32, validation_data=(x_val, y_val))

predictions = model.predict(x)
print(predictions)

# plt.plot(arrsin[:, 0], arrsin[:, 1])
plt.plot(predictions)
plt.show()