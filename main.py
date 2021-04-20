import math
import sys
import os

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import QSettings, pyqtSlot, Qt
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from mainWindow import UiMainWindow
from loginWindow import LoginWindow, AddAccount, ChangeLeverage
import hashlib
from Crypto.Cipher import AES # pip install pycryptodome
import websocket
from threading import Thread
import json
import time

NUMROWS = 50
ex = {'BTCUSD-PERP':{'TICK_SIZE':5, 'TICK_VALUE':0.1},'ETHUSD-PERP':{'TICK_SIZE':0.25, 'TICK_VALUE':0.25}}

class WSThread(Thread):
    def __init__(self, pc):
        super(WSThread, self).__init__()
        self.message = dict()
        self.pc = pc
        self.bids = []
        self.asks = []

    def run(self) -> None:
        def on_open(wsapp):
            curex = self.pc.current_symbol
            self.pc.current_symbol = ''
            self.pc.button1_clicked(curex)

        def on_message(wssapp, message):
            if message == 'ping':
                wssapp.send('pong')
            else:
                self.message = json.loads(message)
                # print(self.message)
                if self.message.get('id'):
                    id = self.message.get('id')
                    status = self.message.get('status')
                    # if status == 'ok':
                    #     self.getTraderStatus(self.pc.current_symbol)
                if self.message.get('ch'):
                    channel = self.message.get('ch')
                    data = self.message['data']
                    if channel == 'orderbook_25':
                        self.pc.message_orderbook(data)
                    elif channel == 'index':
                        self.pc.message_index(data)
                    elif channel == 'trades':
                        self.pc.message_trades(data)
                    elif channel == 'ticker':
                        self.pc.message_ticker(data)
                    elif channel == 'traderStatus':
                        self.pc.message_traderStatus(data)
                    elif channel == 'tradingStatus':
                        self.pc.message_tradingStatus(data['available'])
                    elif channel == 'orderStatus':
                        self.pc.message_orderstatus(data)
                    elif channel == 'orderFilled':
                        self.pc.message_orderFilled(data)
                    elif channel == 'orderCancelled':
                        self.pc.message_orderCancelled(data)
                    elif channel == 'leverage':
                        self.pc.message_leverage(data)


        self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_open=on_open, on_message=on_message)
        self.wsapp.run_forever()

    def changeEx(self, name, lastname):
        if lastname != '':
            # param = '{"id":11, "method":"unsubscribe", "params":["' + lastname + '@orderbook_25"]}'
            # self.wsapp.send(param)
            param = '{"id":12, "method":"unsubscribe", "params":["' + lastname + '@index"]}'
            self.wsapp.send(param)
            param = '{"id":13, "method":"unsubscribe", "params":["' + lastname + '@trades"]}'
            self.wsapp.send(param)
            param = '{"id":14, "method":"unsubscribe", "params":["' + lastname + '@ticker"]}'
            self.wsapp.send(param)
        # param = '{"id":21, "method":"subscribe", "params":["' + name + '@orderbook_25"]}'
        # self.wsapp.send(param)
        param = '{"id":22, "method":"subscribe", "params":["' + name + '@index"]}'
        self.wsapp.send(param)
        param = '{"id":23, "method":"subscribe", "params":["' + name + '@trades"]}'
        self.wsapp.send(param)
        param = '{"id":24, "method":"subscribe", "params":["' + name + '@ticker"]}'
        self.wsapp.send(param)

        self.getTraderStatus(name)

    def auth(self, ak):
        param = '{"id":3, "method":"auth", "params":{"type":"token", "value":"' + ak + '"}}'
        self.wsapp.send(param)

    def getTraderStatus(self, name):
        param = '{"id": 4, "method": "getTraderStatus", "params": {"symbol": "' + name + '"}}'
        self.wsapp.send(param)

    def placeOrder(self, name, side, price, qty):
        param = '{"id": 5, "method": "placeOrder", "params": {"symbol": "' + name + '", "ordType": "LIMIT", "timeInForce": "GTC", "side": "' + side + '", "px": ' + str(price) + ', "qty": ' + str(qty) + '}}'
        time.sleep(0.1)
        self.wsapp.send(param)

    def changeLeverage(self, name, leverage):
        param = '{"id":8, "method":"changeLeverageAll", "params":{"symbol":"' + name + '", "leverage":' + str(leverage) + '}}'
        self.wsapp.send(param)

    def cancelOrder(self, name, clOrdId):
        param = '{"id":9, "method":"cancelOrder", "params":{"symbol":"' + name + '", "clOrdId":"' + clOrdId + '"}}'
        time.sleep(0.1)
        self.wsapp.send(param)

    def cancelAllOrders(self, name):
        param = '{"id":10, "method":"cancelAllOrders", "params":{"symbol":"' + name + '"}}'
        self.wsapp.send(param)


class MainWindow(QMainWindow, UiMainWindow):
    settings = QSettings("./config.ini", QSettings.IniFormat)   # файл настроек
    user = ''
    psw = ''

    current_symbol = ''
    current_leverage = 0
    current_numconts = 1
    current_traderBalance = 0
    current_orderMargin = 0
    current_contractValue = 0
    current_spot_price = 0      #   текущая спот-цена
    current_markprice = 0
    current_cell_price = 0      #   текущая тик-цена
    last_cell_price = 0         #   прошлая тик-цена
    current_central_cell = 0    #   текущая текущая центральнаая ячейка
    current_orderdist = 10       #   текущее расстояние ордера
    mainprocessflag = False     #   флаг автоторговли



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

        self.current_symbol = 'BTCUSD-PERP'
        # создание визуальной формы
        self.setupui(self)

        self.modelorders = QStandardItemModel()
        self.modelorders.setColumnCount(12)
        self.tableViewOrders.setModel(self.modelorders)
        self.tableViewOrders.hideColumn(0)
        self.tableViewOrders.hideColumn(10)
        self.modelorders.setHorizontalHeaderLabels(['clOrdId', 'timestamp', 'openTime', 'orderType', 'timeInForce', 'orderSide', 'px', 'qty', 'leverage', 'paidPx', 'origClOrdId', 'origQty'])

        self.dxthread = WSThread(self)
        self.dxthread.daemon = True
        self.dxthread.start()

        self.show()

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
        if name != self.current_symbol:
            self.dxthread.changeEx(name, self.current_symbol)
            self.current_symbol = name
            self.current_dist = ex[self.current_symbol]['TICK_SIZE']

    @pyqtSlot()
    def startbutton_clicked(self):
        self.mainprocessflag = not self.mainprocessflag
        if self.mainprocessflag:
            self.startbutton.setText('СТОП')
        else:
            self.startbutton.setText('СТАРТ')

    @pyqtSlot()
    def button_closeall_clicked(self):
        self.dxthread.cancelAllOrders(self.current_symbol)

    @pyqtSlot()
    def buttonLeverage_clicked(self):
        rw = ChangeLeverage()
        rw.setupUi(self.current_leverage)
        rw.leveragechanged.connect(lambda: self.dxthread.changeLeverage(self.current_symbol, rw.lineedit_leverage.text()))
        rw.exec_()

    def message_trades(self, data):
        a = 1

    def message_ticker(self, data):
        self.current_contractValue = data['contractValue']

    def current_cell_price_changed(self):
        # завершаем ордеры, которые находятся не на расстоянии дистанции или количество не равно количеству открываемых контрактов
        priceDistBuy = self.current_cell_price - self.current_orderdist * self.current_dist
        priceDistSell = self.current_cell_price + self.current_orderdist * self.current_dist
        for i in range(0, self.modelorders.rowCount()):
            side = self.modelorders.item(i, 5).data(Qt.DisplayRole)
            px = self.modelorders.item(i, 6).data(Qt.DisplayRole)
            qty = self.modelorders.item(i, 7).data(Qt.DisplayRole)
            clOrdId = self.modelorders.item(i, 0).data(3)
            if (px != priceDistBuy and side == 'BUY') or (px != priceDistSell and side == 'SELL') or (qty != self.current_numconts):
                self.dxthread.cancelOrder(self.current_symbol, clOrdId)

        # открываем ордеры
        if self.mainprocessflag:
            pricetoBuy = self.current_cell_price - self.current_orderdist * self.current_dist
            pricetoSell = self.current_cell_price + self.current_orderdist * self.current_dist

            avbalance = self.current_traderBalance - self.current_orderMargin
            req_margin = self.current_contractValue * self.current_numconts / self.current_leverage
            if req_margin < avbalance:
                if self.chb_buy.checkState() == Qt.Checked:
                    self.dxthread.placeOrder(self.current_symbol, 'BUY', pricetoBuy, self.current_numconts)
                if self.chb_sell.checkState() == Qt.Checked:
                    self.dxthread.placeOrder(self.current_symbol, 'SELL', pricetoSell, self.current_numconts)

    def message_index(self, data):
        self.current_spot_price = data['spotPx']
        self.labelprice.setText(str(self.current_spot_price))
        self.current_markprice = data['markPx']
        self.current_cell_price = math.floor(self.current_markprice / self.current_dist) * self.current_dist
        if self.current_cell_price != self.last_cell_price:
            self.last_cell_price = self.current_cell_price
            self.current_cell_price_changed()

    def message_tradingStatus(self, status):
        self.buttonLeverage.setEnabled(status)
        self.startbutton.setEnabled(status)
        if status:
            self.statusbar.showMessage('Торговля разрешена')
            self.dxthread.getTraderStatus(self.current_symbol)
        else:
            self.statusbar.showMessage('Торговля запрещена')

    def message_traderStatus(self, data):
        self.current_traderBalance = data['traderBalance']
        self.labelbalance.setText(str(data['traderBalance'])+' DGTX')
        self.current_leverage = data['leverage']
        self.buttonLeverage.setText(str(data['leverage']) + ' x')

        self.modelorders.removeRows(0, self.modelorders.rowCount())
        for ord in data['activeOrders']:
            self.modelorders.appendRow([QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(),
                                       QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem()])
            rownum = self.modelorders.rowCount() - 1
            self.modelorders.item(rownum, 0).setData(ord['clOrdId'], 3)
            self.modelorders.item(rownum, 1).setData(ord['timestamp'], Qt.DisplayRole)
            self.modelorders.item(rownum, 2).setData(ord['openTime'], Qt.DisplayRole)
            self.modelorders.item(rownum, 3).setData(ord['orderType'], Qt.DisplayRole)
            self.modelorders.item(rownum, 4).setData(ord['timeInForce'], Qt.DisplayRole)
            self.modelorders.item(rownum, 5).setData(ord['orderSide'], Qt.DisplayRole)
            self.modelorders.item(rownum, 6).setData(ord['px'], Qt.DisplayRole)
            self.modelorders.item(rownum, 7).setData(ord['qty'], Qt.DisplayRole)
            self.modelorders.item(rownum, 8).setData(ord['leverage'], Qt.DisplayRole)
            self.modelorders.item(rownum, 9).setData(ord['paidPx'], Qt.DisplayRole)
            self.modelorders.item(rownum, 10).setData(ord['origClOrdId'], 3)
            self.modelorders.item(rownum, 11).setData(ord['origQty'], Qt.DisplayRole)

    def message_orderstatus(self, data):
        self.current_leverage = data['leverage']
        self.buttonLeverage.setText(str(data['leverage']) + ' x')
        self.current_orderMargin = data['orderMargin']

        if data['orderStatus'] == 'ACCEPTED':
            self.modelorders.appendRow(
                [QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(),
                 QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem()])
            rownum = self.modelorders.rowCount() - 1
            self.modelorders.item(rownum, 0).setData(data['clOrdId'], 3)
            self.modelorders.item(rownum, 1).setData(data['timestamp'], Qt.DisplayRole)
            self.modelorders.item(rownum, 2).setData(data['openTime'], Qt.DisplayRole)
            self.modelorders.item(rownum, 3).setData(data['orderType'], Qt.DisplayRole)
            self.modelorders.item(rownum, 4).setData(data['timeInForce'], Qt.DisplayRole)
            self.modelorders.item(rownum, 5).setData(data['orderSide'], Qt.DisplayRole)
            self.modelorders.item(rownum, 6).setData(data['px'], Qt.DisplayRole)
            self.modelorders.item(rownum, 7).setData(data['qty'], Qt.DisplayRole)
            self.modelorders.item(rownum, 8).setData(data['leverage'], Qt.DisplayRole)
            self.modelorders.item(rownum, 9).setData(data['paidPx'], Qt.DisplayRole)
            self.modelorders.item(rownum, 10).setData(data['origClOrdId'], 3)
            self.modelorders.item(rownum, 11).setData(data['origQty'], Qt.DisplayRole)

    def message_orderFilled(self, data):
        self.current_traderBalance = data['traderBalance']
        self.labelbalance.setText(str(data['traderBalance']) + ' DGTX')
        self.current_leverage = data['leverage']
        self.buttonLeverage.setText(str(data['leverage']) + ' x')
        self.current_orderMargin = data['orderMargin']

        ordid = data['origClOrdId']
        listindex = self.modelorders.match(self.modelorders.index(0, 10), 3, ordid)
        for ind in listindex:
            self.modelorders.removeRow(ind.row())

    def message_orderCancelled(self, data):
        self.current_orderMargin = data['orderMargin']

        for ordid in [x['origClOrdId'] for x in data['orders']]:
            listindex = self.modelorders.match(self.modelorders.index(0, 10), 3, ordid)
            for ind in listindex:
                self.modelorders.removeRow(ind.row())

    def message_leverage(self, data):
        self.message_orderstatus(data)

app = QApplication([])
win = MainWindow()
sys.exit(app.exec_())
