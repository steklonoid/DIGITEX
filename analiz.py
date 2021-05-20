import numpy as np
from matplotlib import pyplot as plt

from keras import models
from keras import layers
from keras import callbacks
from keras.utils.np_utils import to_categorical

P_TEST = 80

LOOKBACK = 1024
LOOKFORWARD = 50



arr = np.loadtxt('history.csv', delimiter=',')
# arr = np.array([[1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8], [9, 9], [10, 10]])
arrlen = arr.shape[0]

x = np.zeros((arrlen - LOOKBACK - LOOKFORWARD + 1, LOOKBACK))
y = np.zeros((arrlen - LOOKBACK - LOOKFORWARD + 1, ))

for i in range(arrlen - LOOKBACK - LOOKFORWARD + 1):
    x[i] = arr[i:i + LOOKBACK, 1]
    # y[i] = arr[i + LOOKBACK, 1]
    maxd = 0
    for j in range(LOOKFORWARD):
        maxd = max(maxd, np.abs(arr[i + LOOKBACK - 1, 1] - arr[i + LOOKBACK + j, 1]))
    if maxd < 5:
        y[i] = 0
    elif maxd < 10:
        y[i] = 1
    elif maxd < 15:
        y[i] = 2
    elif maxd < 20:
        y[i] = 3
    elif maxd < 25:
        y[i] = 4
    else:
        y[i] = 5

y = to_categorical(y)

bond = int(arrlen * P_TEST / 100)
x_test = x[:bond]
y_test = y[:bond]
x_val = x[bond:]
y_val = y[bond:]

mean = x_test.mean(axis=0)
x_test -= mean
std = x_test.std(axis=0)
x_test /= std
x_val -= mean
x_val /= std

model = models.Sequential()
model.add(layers.Dense(LOOKBACK // 4,  activation='relu', input_shape=(LOOKBACK,)))
model.add(layers.Dense(LOOKBACK // 8,  activation='relu'))
model.add(layers.Dense(6, activation='softmax'))

model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])


callbacklist = [callbacks.ModelCheckpoint(filepath='my_model_1024_50.h5', monitor='val_loss', save_best_only=True)]

history = model.fit(x_test, y_test, epochs=50, batch_size=32, validation_data=(x_val, y_val), callbacks=callbacklist)

loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, loss, 'bo', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()


