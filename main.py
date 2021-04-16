import math
import sys
import os


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
# import time

NUMROWS = 50
ex = {'BTCUSD-PERP':{'TICK_SIZE':5, 'TICK_VALUE':0.1},'ETHUSD-PERP':{'TICK_SIZE':0.25, 'TICK_VALUE':0.25}}

class Order():
    def __init__(self, clOrdId, timestamp, openTime, orderType, timeInForce, orderSide, px, qty, leverage, paidPx, origClOrdId, origQty):
        self.clOrdId = clOrdId
        self.timestamp = timestamp
        self.openTime = openTime
        self.orderType = orderType
        self.timeInForce = timeInForce
        self.orderSide = orderSide
        self.px = px
        self.qty = qty
        self.leverage = leverage
        self.paidPx = paidPx
        self.origClOrdId = origClOrdId
        self.origQty = origQty

class Contract():
    def __init__(self, timestamp, traderId, positionType, qty, entryPx, paidPx, liquidationPx, bankruptcyPx, exitPx, leverage, contractId, openTime, entryQty, exitQty, exitVolume, fundingPaidPx, fundingQty, fundingVolume, fundingCount, origContractId):
        self.timestamp = timestamp
        self.traderId = traderId
        self.positionType = positionType
        self.qty = qty
        self.entryPx = entryPx
        self.paidPx = paidPx
        self.liquidationPx = liquidationPx
        self.bankruptcyPx = bankruptcyPx
        self.exitPx = exitPx
        self.leverage = leverage
        self.contractId = contractId
        self.openTime = openTime
        self.entryQty = entryQty
        self.exitQty = exitQty
        self.exitVolume = exitVolume
        self.fundingPaidPx = fundingPaidPx
        self.fundingQty = fundingQty
        self.fundingVolume = fundingVolume
        self.fundingCount = fundingCount
        self.origContractId = origContractId


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
                        self.bids = data['bids']
                        self.asks = data['asks']
                        self.pc.message_orderbook()
                    elif channel == 'index':
                        self.pc.message_index(data['spotPx'])
                    elif channel == 'trades':
                        print(self.message)
                    elif channel == 'ticker':
                        print(self.message)
                    elif channel == 'traderStatus':
                        self.pc.message_traderStatus(data)
                    elif channel == 'tradingStatus':
                        self.pc.message_tradingStatus(data['available'])
                    elif channel == 'orderStatus':
                        self.pc.message_orderstatus(data)
                    elif channel == 'orderFilled':
                        print(self.message)
                    elif channel == 'orderCancelled':
                        print(self.message)
                    elif channel == 'leverage':
                        print(self.message)


        self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_open=on_open, on_message=on_message)
        self.wsapp.run_forever()

    def changeEx(self, name, lastname):
        if lastname != '':
            param = '{"id":11, "method":"unsubscribe", "params":["' + lastname + '@orderbook_25"]}'
            self.wsapp.send(param)
            param = '{"id":12, "method":"unsubscribe", "params":["' + lastname + '@index"]}'
            self.wsapp.send(param)
            param = '{"id":13, "method":"unsubscribe", "params":["' + lastname + '@trades"]}'
            self.wsapp.send(param)
            param = '{"id":14, "method":"unsubscribe", "params":["' + lastname + '@ticker"]}'
            self.wsapp.send(param)
        param = '{"id":21, "method":"subscribe", "params":["' + name + '@orderbook_25"]}'
        self.wsapp.send(param)
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
        self.wsapp.send(param)

    def changeLeverage(self, name, leverage):
        param = '{"id":8, "method":"changeLeverageAll", "params":{"symbol":"' + name + '", "leverage":' + str(leverage) + '}}'
        self.wsapp.send(param)

    def cancelOrder(self, param):
        self.wsapp.send(param)

    def cancelAllOrders(self, param):
        self.wsapp.send(param)


class MainWindow(QMainWindow, UiMainWindow):
    settings = QSettings("./config.ini", QSettings.IniFormat)   # файл настроек
    user = ''
    psw = ''

    curstate = {'symbol':'',                               #   текущая валюта
                'traderBalance':0,
                'leverage':0,
                'orderMargin':0,
                'positionMargin':0,
                'upnl':0,
                'pnl':0,
                'positionType':'',
                'positionContracts':0,
                'positionVolume':0,
                'positionLiquidationVolume':0,
                'positionBankruptcyVolume':0,
                'fundingRate':0,
                'contractValue':0}

    current_symbol = ''
    current_leverage = 0

    current_spot_price = 0      #   текущая спот-цена
    current_cell_price = 0      #   текущая тик-цена
    last_cell_price = 0         #   прошлая тик-цена
    current_central_cell = 0    #   текущая текущая центральнаая ячейка
    current_numconts = 1        #   текущий квадрат
    current_opendist = 10       #   текущее расстояние открытия
    current_closedist = 5       #   текущее расстояние закрытия
    mainprocessflag = False     #   флаг автоторговли

    unmatched_orders = []

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

        self.modelorders = QStandardItemModel()
        self.modelorders.setColumnCount(12)
        self.tableViewOrders.setModel(self.modelorders)
        self.tableViewOrders.hideColumn(0)
        self.tableViewOrders.hideColumn(10)
        self.modelorders.setHorizontalHeaderLabels(['clOrdId', 'timestamp', 'openTime', 'orderType', 'timeInForce', 'orderSide', 'px', 'qty', 'leverage', 'paidPx', 'origClOrdId', 'origQty'])

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
        if name != self.current_symbol:
            self.dxthread.changeEx(name, self.current_symbol)
            self.current_symbol = name
            self.current_dist = ex[self.current_symbol]['TICK_SIZE']

    @pyqtSlot()
    def tableViewStairClicked(self):
        indexCell = self.tableViewStair.selectedIndexes()[0].siblingAtColumn(3)
        self.modelStair.setData(indexCell, 5, Qt.DisplayRole)

    @pyqtSlot()
    def slider_leverage_valueChanged(self):
        self.slider_leverage_value.setText(str(self.sender().value()))

    @pyqtSlot()
    def slider_leverage_value_editingFinished(self):
        def outofrange(val):
            self.slider_leverage_value.setText(str(val))
            self.slider_leverage.setValue(val)
            self.currentLeverage = val

        v = self.sender().text()
        if not v.isdigit():
            outofrange(5)
        elif int(v) < 5:
            outofrange(5)
        elif int(v) > 100:
            outofrange(100)
        else:
            outofrange(int(v))

    @pyqtSlot()
    def slider_numconts_valueChanged(self):
        self.slider_numconts_value.setText(str(self.sender().value()))
        self.current_numconts = self.sender().value()

    @pyqtSlot()
    def slider_numconts_value_editingFinished(self):
        def outofrange(val):
            self.slider_numconts_value.setText(str(val))
            self.slider_numconts.setValue(val)
            self.current_numconts = val

        v = self.sender().text()
        if not v.isdigit():
            outofrange(5)
        elif int(v) < 5:
            outofrange(5)
        elif int(v) > 100:
            outofrange(100)
        else:
            outofrange(int(v))

    @pyqtSlot()
    def lineeditopendist_editingFinished(self):
        v = self.sender().text()
        if not v.isdigit():
            self.lineeditopendist.setText('10')
            self.current_opendist = 10
        elif int(v) < 1:
            self.lineeditopendist.setText('1')
            self.current_opendist = 1
        else:
            self.current_opendist = int(v)

    @pyqtSlot()
    def lineeditclosedist_editingFinished(self):
        v = self.sender().text()
        if not v.isdigit():
            self.lineeditclosedist.setText('5')
            self.current_closedist = 5
        elif int(v) < 1:
            self.lineeditclosedist.setText('1')
            self.current_closedist = 1
        else:
            self.current_closedist = int(v)

    @pyqtSlot()
    def startbutton_clicked(self):
        self.mainprocessflag = not self.mainprocessflag
        if self.mainprocessflag:
            self.startbutton.setText('СТОП')
        else:
            self.startbutton.setText('СТАРТ')

    @pyqtSlot()
    def button_closeall_clicked(self):
        print('close all')

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

    def current_cell_price_changed(self):
        if self.mainprocessflag:
            pricetoBuy = self.current_cell_price - 15 * self.current_dist
            self.dxthread.placeOrder(self.current_symbol, 'BUY', pricetoBuy, 1)

    def message_index(self, spotPx):
        self.current_spot_price = spotPx
        self.labelprice.setText(str(self.current_spot_price))
        #self.graphicsView.repaint()
        self.current_cell_price = math.floor(self.current_spot_price / self.current_dist)*self.current_dist
        if self.current_cell_price != self.last_cell_price:
            self.last_cell_price = self.current_cell_price
            self.current_cell_price_changed()

        if math.fabs(self.current_cell_price - self.current_central_cell) >= 7 * self.current_dist:
            self.current_central_cell = self.current_cell_price
            self.change_internal_bounds()

        shift = int((self.current_cell_price - self.current_central_cell) / self.current_dist)
        for i in range(0, NUMROWS * 2 + 1):
            if i == NUMROWS - shift:
               self.modelStair.item(i, 1).setBackground(QColor(24, 24, 68))
            else:
                self.modelStair.item(i, 1).setBackground(QColor(0, 21, 25))

    def message_tradingStatus(self, status):
        if status:
            self.statusbar.showMessage('Торговля разрешена')
            self.dxthread.getTraderStatus(self.current_symbol)
        else:
            self.statusbar.showMessage('Торговля запрещена')

    def message_traderStatus(self, data):
        self.labelbalance.setText(str(data['traderBalance'])+' DGTX')

        # self.curstate['traderBalance'] = data['traderBalance']
        # self.curstate['orderMargin'] = data['orderMargin']
        # self.curstate['positionMargin'] = data['positionMargin']
        self.current_leverage = data['leverage']

        self.modelorders.removeRows(0, self.modelorders.rowCount())
        for ord in data['activeOrders']:
            self.modelorders.appendRow([QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(),
                                       QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem()])
            rownum = self.modelorders.rowCount() - 1
            self.modelorders.item(rownum, 0).setData(ord['clOrdId'], Qt.DisplayRole)
            self.modelorders.item(rownum, 1).setData(ord['timestamp'], Qt.DisplayRole)
            self.modelorders.item(rownum, 2).setData(ord['openTime'], Qt.DisplayRole)
            self.modelorders.item(rownum, 3).setData(ord['orderType'], Qt.DisplayRole)
            self.modelorders.item(rownum, 4).setData(ord['timeInForce'], Qt.DisplayRole)
            self.modelorders.item(rownum, 5).setData(ord['orderSide'], Qt.DisplayRole)
            self.modelorders.item(rownum, 6).setData(ord['px'], Qt.DisplayRole)
            self.modelorders.item(rownum, 7).setData(ord['qty'], Qt.DisplayRole)
            self.modelorders.item(rownum, 8).setData(ord['leverage'], Qt.DisplayRole)
            self.modelorders.item(rownum, 9).setData(ord['paidPx'], Qt.DisplayRole)
            self.modelorders.item(rownum, 10).setData(ord['origClOrdId'], Qt.DisplayRole)
            self.modelorders.item(rownum, 11).setData(ord['origQty'], Qt.DisplayRole)

    def message_orderstatus(self, data):
        self.unmatched_orders.append('')

app = QApplication([])
win = MainWindow()
sys.exit(app.exec_())
