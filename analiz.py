from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QPushButton, QFileDialog
import sys

import numpy as np
from matplotlib import pyplot as plt

from keras import models
from keras import layers
from keras import callbacks
from keras.utils.np_utils import to_categorical

from threading import Thread

P_TEST = 80

LOOKBACK = 84
LOOKFORWARD = 1

# def WhiteNoise(n):
#     a = np.zeros((n, 3))
#     random.seed()
#     lastrnd = 0
#     rnd = 0
#     for i in range(n):
#         rnd = random.random()
#         a[i] = [i, max(rnd, lastrnd), min(rnd, lastrnd)]
#         lastrnd = rnd
#     return a
class Worker(Thread):

    def __init__(self, f, arr):
        super(Worker, self).__init__()
        self.f = f
        self.arr = arr

    def run(self) -> None:
        self.f(self.arr)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.resize(800, 600)
        centralwidget = QWidget()
        self.setCentralWidget(centralwidget)
        gridLayout = QGridLayout()
        centralwidget.setLayout(gridLayout)
        button1 = QPushButton()
        button1.setText('Загрузить нейросеть')
        button1.clicked.connect(self.open_neyronet)
        gridLayout.addWidget(button1, 0, 0, 1, 1)
        button2 = QPushButton()
        button2.setText('Загрузить исторические данные')
        button2.clicked.connect(self.loadhistorical)
        gridLayout.addWidget(button2, 1, 0, 1, 1)
        button3 = QPushButton()
        button3.setText('Рассчитать нейросеть')
        button3.clicked.connect(self.calc_neyronet)
        gridLayout.addWidget(button3, 2, 0, 1, 1)
        self.show()
        self.arr = ''
        # self.work()

    def open_neyronet(self):
        filename = QFileDialog.getOpenFileName(parent=self, directory='./files', filter='h5 files (*.h5)')[0]
        if filename:
            models.load_model(filename)

    def loadhistorical(self):
        self.arr = np.loadtxt('./files/USDT_BTC_2h_neyro_fk_4-2048.csv', delimiter=',', skiprows=5)
        print(self.arr.shape[0])

    def calc_neyronet(self):
        if self.arr:
            worker = Worker(self.work, self.arr)
            # worker.setDaemon(True)
            # worker.start()

    def work(self, arr):
        bonds = [0.9, 0.96, 1.04, 1.1]
        x = np.zeros((arr.shape[0] - LOOKBACK - LOOKFORWARD + 1, LOOKBACK * 3))
        y = np.zeros((arr.shape[0] - LOOKBACK - LOOKFORWARD + 1, ))
        yy = np.zeros((arr.shape[0] - LOOKBACK - LOOKFORWARD + 1, ))

        for i in range(arr.shape[0] - LOOKBACK - LOOKFORWARD + 1):
            x[i, :LOOKBACK] = arr[i:i + LOOKBACK, 3]
            x[i, LOOKBACK:LOOKBACK * 2] = arr[i:i + LOOKBACK, 4]
            x[i, LOOKBACK * 2:LOOKBACK * 3] = arr[i:i + LOOKBACK, 5]
            currel = 0
            for j in range(LOOKFORWARD):
                mid1 = (arr[i + LOOKBACK + j, 1] + arr[i + LOOKBACK + j, 2]) / 2
                mid0 = (arr[i + LOOKBACK + j - 1, 1] + arr[i + LOOKBACK + j - 1, 2]) / 2
                rel = mid1 / mid0
                currel = max(currel, rel)
            yy[i] = currel
            ind = len(bonds)
            for k, val in enumerate(bonds):
                if currel < val:
                    ind = k
                    break
            y[i] = ind

        y = to_categorical(y)
        #
        bond = int(x.shape[0] * P_TEST / 100)
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
        model.add(layers.Dense(LOOKBACK * 2,  activation='relu', input_shape=(LOOKBACK * 3,)))
        model.add(layers.Dense(LOOKBACK,  activation='relu'))
        model.add(layers.Dense(y.shape[1], activation='softmax'))

        model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])
        callbacklist = [callbacks.ModelCheckpoint(filepath='fk_abs_84back_3forw.h5', monitor='val_loss', save_best_only=True)]
        history = model.fit(x_test, y_test, epochs=30, batch_size=32, validation_data=(x_val, y_val), callbacks=callbacklist)

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

app = QApplication([])
win = MainWindow()
sys.exit(app.exec_())


