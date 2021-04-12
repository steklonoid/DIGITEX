import math
import sys
import os
import time

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QColor, QFont
from PyQt5.QtCore import QSettings, pyqtSlot, Qt
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from mainWindow import UiMainWindow
from loginWindow import LoginWindow, AddAccount
import hashlib
from Crypto.Cipher import AES # pip install pycryptodome
import websocket
from threading import Thread
import json

NUMROWS = 50
ex = {'BTCUSD-PERP':{'dist':5},'ETHUSD-PERP':{'dist':0.25}}
ids = {'subscribe':1, 'unsubscribe':2, 'auth':3, 'getTraderStatus':4, 'placeOrder':5, 'cancelOrder':6, 'cancelAllOrders':7}
chanels = {'orderbook_25', 'index', 'traderStatus', 'tradingStatus', 'orderStatus', 'orderFilled', 'orderCancelled'}

class CellTable(QStandardItem):
    def __init__(self):
        QStandardItem.__init__(self)
        self.setBackground(QColor(0, 21, 25))
        self.setForeground(QColor(255, 255, 255))

class CellTableClick(QStandardItem):
    def __init__(self):
        QStandardItem.__init__(self)
        self.setBackground(QColor(90, 0, 157))
        self.setForeground(QColor(255, 128, 0))
        self.setFont(QFont("Helvetica", 14, QFont.Bold))

class WSThread(Thread):
    def __init__(self, pc):
        super(WSThread, self).__init__()
        self.message = dict()
        self.pc = pc
        self.bids = []
        self.asks = []
        self.spotPx = 0

    def run(self) -> None:

        def on_message(wssapp, message):
            if message == 'ping':
                wssapp.send('pong')
            self.message = json.loads(message)
            # print(self.message)
            if self.message.get('id'):
                id = self.message.get('id')
                status = self.message.get('status')
                print(id, status)
            if self.message.get('ch'):
                chanel = self.message.get('ch')
                data = self.message['data']
                if chanel == 'orderbook_25':
                    self.bids = data['bids']
                    self.asks = data['asks']
                    self.pc.message_orderbook()
                elif chanel == 'index':
                    self.spotPx = data['spotPx']
                    self.pc.message_index()

        self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_message=on_message)
        self.wsapp.run_forever()

    def traderstatusrequest(self):
        param = '{"id": 4, "method": "getTraderStatus", "params": {"symbol": "BTCUSD-PERP"}}'
        self.wsapp.send(param)

    def changeEx(self, name, lastname):
        if lastname != '':
            param = '{"id":2, "method":"unsubscribe", "params":["' + lastname + '@orderbook_25"]}'
            self.wsapp.send(param)
            param = '{"id":2, "method":"unsubscribe", "params":["' + lastname + '@index"]}'
            self.wsapp.send(param)
        param = '{"id":1, "method":"subscribe", "params":["' + name + '@orderbook_25"]}'
        self.wsapp.send(param)
        param = '{"id":1, "method":"subscribe", "params":["' + name + '@index"]}'
        self.wsapp.send(param)

    def auth(self, ak):
        param = '{"id":3, "method":"auth", "params":{"type":"token", "value":"' + ak + '"}}'
        self.wsapp.send(param)
        # time.sleep(1)
        # param = '{"id": 4, "method": "getTraderStatus", "params": {"symbol": "BTCUSD-PERP"}}'
        # self.wsapp.send(param)

class MainWindow(QMainWindow, UiMainWindow):
    settings = QSettings("./config.ini", QSettings.IniFormat)   # файл настроек
    user = ''
    psw = ''
    currentEx = ''
    current_spot_price = 0
    current_cell_price = 0
    last_cell_price = 0
    current_central_cell = 0
    current_dist = 0

    def __init__(self):

        def createdb(fname):
            self.db.setDatabaseName(fname)
            self.db.open()
            q1 = QSqlQuery(self.db)
            q1.prepare("CREATE TABLE users (login TEXT UNIQUE PRIMARY KEY, psw TEXT)")
            q1.exec_()
            q1.prepare("CREATE TABLE accounts (userlogin TEXT NOT NULL, accname TEXT NOT NULL, apikey TEXT NOT NULL)")
            q1.exec_()

        def opendb():
            fname = "./conf.db"
            if not os.path.exists(fname):
                createdb(fname)

            self.db.setDatabaseName(fname)
            self.db.open()
            if self.db.isOpen():
                return True
            else:
                return False


        super().__init__()

        #  подключаем базу SQLite
        self.db = QSqlDatabase.addDatabase("QSQLITE", 'maindb')
        if not opendb():
            msg_box = QMessageBox()
            msg_box.setText("Ошибка открытия файла базы данных")
            msg_box.exec()
            sys.exit()

        # отображение окна
        self.setupui(self)

        self.modelStair = QStandardItemModel()
        self.modelStair.setColumnCount(4)
        self.tableViewStair.setModel(self.modelStair)
        for i in range(0, NUMROWS * 2 + 1):
            self.modelStair.appendRow([CellTable(), CellTable(), CellTable(), CellTableClick()])
        self.tableViewStair.verticalHeader().close()
        self.tableViewStair.horizontalHeader().close()
        self.qi1 = self.modelStair.createIndex(0, 0)
        self.qi2 = self.modelStair.createIndex(NUMROWS * 2, 2)
        self.qcenter = self.modelStair.createIndex(NUMROWS, 1)
        self.tableViewStair.scrollTo(self.qcenter)

        self.dxthread = WSThread(self)
        self.dxthread.daemon = True
        self.dxthread.start()

    def closeEvent(self, *args, **kwargs):
        if self.db.isOpen():
            self.db.close()

    @pyqtSlot()
    def buttonLogin_clicked(self):
        if not self.user:
            rw = LoginWindow(self.db)
            rw.userlogined.connect(lambda: self.userlogined(rw.user, rw.psw))
            rw.setupUi()
            rw.exec_()

    def userlogined(self, user, psw):
        self.user = user
        self.psw = psw
        self.buttonEnter.setText('вход выполнен: '+self.user)
        self.buttonEnter.setStyleSheet("color:rgb(32, 128, 32); font: bold 11px; border: none")

        q1 = QSqlQuery(self.db)
        q1.prepare("SELECT accname FROM accounts WHERE userlogin=:userlogin ORDER BY accname ASC")
        q1.bindValue(":userlogin", self.user)
        q1.exec_()
        while q1.next():
            it = QStandardItem()
            it.setData(q1.value(0), 3)
            self.comboBoxAccount.addItem(q1.value(0), q1.value(0))
        self.comboBoxAccount.addItem("...добавить новый")

    @pyqtSlot()
    def comboBoxAccount_currentIndexChanged(self):
        if self.comboBoxAccount.currentText() == "...добавить новый":
            rw = AddAccount(self)
            rw.setupUi()
            rw.exec_()
            self.comboBoxAccount.setCurrentIndex(0)
            return

        IV_SIZE = 16  # 128 bit, fixed for the AES algorithm
        KEY_SIZE = 32  # 256 bit meaning AES-256, can also be 128 or 192 bits
        SALT_SIZE = 16  # This size is arbitrary

        q1 = QSqlQuery(self.db)
        q1.prepare("SELECT apikey FROM accounts WHERE userlogin=:userlogin AND accname=:accname")
        q1.bindValue(":userlogin", self.user)
        q1.bindValue(":accname", self.comboBoxAccount.currentData())
        q1.exec_()
        if q1.next():
            en_ak_int = int(q1.value(0))
            en_ak_byte = en_ak_int.to_bytes((en_ak_int.bit_length() + 7) // 8, sys.byteorder)
            salt = en_ak_byte[0:SALT_SIZE]
            derived = hashlib.pbkdf2_hmac('sha256', self.psw.encode('utf-8'), salt, 100000,
                                          dklen=IV_SIZE + KEY_SIZE)
            iv = derived[0:IV_SIZE]
            key = derived[IV_SIZE:]
            ak = AES.new(key, AES.MODE_CFB, iv).decrypt(en_ak_byte[SALT_SIZE:]).decode('utf-8')
            self.dxthread.auth(ak)
        else:
            print('account not found')

    @pyqtSlot()
    def button1_clicked(self, name):
        if name != self.currentEx:
            self.dxthread.changeEx(name, self.currentEx)
            self.currentEx = name
            self.current_dist = ex[self.currentEx]['dist']

    @pyqtSlot()
    def tableViewStairClicked(self):
        indexCell = self.tableViewStair.selectedIndexes()[0].siblingAtColumn(3)
        self.modelStair.setData(indexCell, 5, Qt.DisplayRole)


    def change_internal_bounds(self):
        self.modelStair.item(NUMROWS, 1).setData(self.current_central_cell, Qt.DisplayRole)
        for i in range(1, NUMROWS + 1):
            self.modelStair.item(NUMROWS - i, 1).setData(self.current_central_cell + i * self.current_dist, Qt.DisplayRole)
            self.modelStair.item(NUMROWS + i, 1).setData(self.current_central_cell - i * self.current_dist, Qt.DisplayRole)

    def message_orderbook(self):
        for i in range(0, NUMROWS * 2 + 1):
            self.modelStair.item(i, 0).setData('', Qt.DisplayRole)
            self.modelStair.item(i, 0).setBackground(QColor(28, 34, 34))
            self.modelStair.item(i, 2).setData('', Qt.DisplayRole)
            self.modelStair.item(i, 2).setBackground(QColor(28, 34, 34))
        for i in range(0, 25):
            ind = int((self.dxthread.asks[i][0] - self.current_central_cell) / self.current_dist)
            if ind <= NUMROWS:
                self.modelStair.item(NUMROWS - ind, 2).setData(self.dxthread.asks[i][1], Qt.DisplayRole)
                self.modelStair.item(NUMROWS - ind, 2).setBackground(QColor(68, 24, 24))
            ind = int((self.current_central_cell - self.dxthread.bids[i][0]) / self.current_dist)
            if ind <= NUMROWS:
                self.modelStair.item(NUMROWS + ind, 0).setData(self.dxthread.bids[i][1], Qt.DisplayRole)
                self.modelStair.item(NUMROWS + ind, 0).setBackground(QColor(24, 68, 24))
        self.tableViewStair.dataChanged(self.qi1, self.qi2)

    def message_index(self):
         self.current_spot_price = self.dxthread.spotPx
         self.labelprice.setText(str(self.current_spot_price))
         #self.graphicsView.repaint()
         self.current_cell_price = math.floor(self.current_spot_price / self.current_dist)*self.current_dist

         if math.fabs(self.current_cell_price - self.current_central_cell) >= 10 * self.current_dist:
             self.current_central_cell = self.current_cell_price
             self.change_internal_bounds()

         shift = int((self.current_cell_price - self.current_central_cell) / self.current_dist)
         for i in range(0, NUMROWS * 2 + 1):
             if i == NUMROWS - shift - 1:
                self.modelStair.item(i, 1).setBackground(QColor(24, 24, 68))
             else:
                 self.modelStair.item(i, 1).setBackground(QColor(0, 21, 25))


app = QApplication([])
win = MainWindow()
sys.exit(app.exec_())
