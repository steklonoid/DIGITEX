import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import QSettings, pyqtSlot
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from mainWindow import UiMainWindow
from loginWindow import LoginWindow, AddAccount
import hashlib
from Crypto.Cipher import AES # pip install pycryptodome
# from wss import ConnectToDigitex
import websocket
from threading import Thread

class WSThread(Thread):
    def __init__(self):
        super(WSThread, self).__init__()
        self.message = ''

    def run(self) -> None:

        def on_open(wssapp):
            print('open')

        def on_message(wssapp, message):
            if message == 'ping':
                wssapp.send('pong')
            self.message = message
            self.job()

        self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_open=on_open, on_message=on_message)
        self.wsapp.run_forever()

    def job(self):
        print(self.message)

    def send(self, param):
        self.wsapp.send(param)

class MainWindow(QMainWindow, UiMainWindow):
    settings = QSettings("./config.ini", QSettings.IniFormat)   # файл настроек
    user = ''
    psw = ''
    ak = ''

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
        self.modelStair.setColumnCount(3)
        self.tableViewStair.setModel(self.modelStair)
        for i in range(0, 100):
            self.modelStair.appendRow([QStandardItem(), QStandardItem(), QStandardItem()])

        self.dxthread = WSThread()
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
            self.ak = AES.new(key, AES.MODE_CFB, iv).decrypt(en_ak_byte[SALT_SIZE:]).decode('utf-8')
            en_pk_int = int(q1.value(1))
            en_pk_byte = en_pk_int.to_bytes((en_pk_int.bit_length() + 7) // 8, sys.byteorder)
            salt = en_pk_byte[0:SALT_SIZE]
            derived = hashlib.pbkdf2_hmac('sha256', self.psw.encode('utf-8'), salt, 100000,
                                          dklen=IV_SIZE + KEY_SIZE)
            iv = derived[0:IV_SIZE]
            key = derived[IV_SIZE:]
            self.pk = AES.new(key, AES.MODE_CFB, iv).decrypt(en_pk_byte[SALT_SIZE:])
        else:
            print('account not found')

    @pyqtSlot()
    def button1_clicked(self, name):
        param = '{"id":1, "method":"subscribe", "params":["'+name+'@orderbook_5"]}'
        self.dxthread.send(param)

app = QApplication([])
win = MainWindow()
sys.exit(app.exec_())
