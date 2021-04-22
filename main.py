import math
import sys
import os

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QIcon
from PyQt5.QtCore import QSettings, pyqtSlot, Qt
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from mainWindow import UiMainWindow
from loginWindow import LoginWindow, RegisterWindow, ChangeLeverage
import hashlib
from Crypto.Cipher import AES # pip install pycryptodome
import websocket
from threading import Thread
import json
import time

ex = {'BTCUSD-PERP':{'TICK_SIZE':5, 'TICK_VALUE':0.1},'ETHUSD-PERP':{'TICK_SIZE':0.25, 'TICK_VALUE':0.25}}

class Order():
    def __init__(self, **kwargs):
        self.clOrdId = kwargs['clOrdId']
        self.orderSide = kwargs['orderSide']
        self.px = kwargs['px']
        self.qty = kwargs['qty']

class WSThread(Thread):
    methods = {'subscribe':1, 'unsubscribe':2, 'subscriptions':3, 'auth':4, 'placeOrder':5, 'cancelOrder':6, 'cancelAllOrders':7, 'placeCondOrder':8, 'cancelCondOrder':9, 'closeContract':10, 'closePosition':11, 'getTraderStatus':12, 'changeLeverageAll':13}
    channels = ['orderbook', 'kline', 'trades', 'liquidations', 'ticker', 'fundingInfo', 'index', 'tradingStatus', 'orderStatus', 'orderFilled', 'orderCancelled', 'condOrderStatus', 'contractClosed', 'traderStatus', 'leverage', 'funding', 'position']

    def __init__(self, pc):
        super(WSThread, self).__init__()
        self.message = dict()
        self.pc = pc

    def run(self) -> None:
        def on_open(wsapp):
            curex = self.pc.current_symbol
            self.pc.current_symbol = ''
            self.pc.button1_clicked(curex)

        def on_close(wsapp):
            print('on_close')

        def on_error(wsapp, error):
            print('error ' + error)

        def on_message(wssapp, message):
            if message == 'ping':
                wssapp.send('pong')
            else:
                try:
                    self.message = json.loads(message)
                except:
                    return
                if self.message.get('id'):
                    id = self.message.get('id')
                    status = self.message.get('status')
                    print(self.message)
                if self.message.get('ch'):
                    channel = self.message.get('ch')
                    data = self.message.get('data')
                    if channel in self.channels:
                        eval('self.pc.message_' + channel + '(data)')

        self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_open=on_open, on_close=on_close, on_error=on_error, on_message=on_message)
        self.wsapp.run_forever()

    def changeEx(self, name, lastname):
        if lastname != '':
            self.send_public('unsubscribe', name + '@index', name + '@trades', name + '@ticker')
        self.send_public('subscribe', name + '@index', name + '@trades', name + '@ticker')
        self.send_privat('getTraderStatus', symbol=name)

    def send_public(self, method, *params):
        pd = {'id':self.methods.get(method), 'method':method}
        if params:
            pd['params'] = list(params)
        strpar = json.dumps(pd)
        self.wsapp.send(strpar)
        time.sleep(0.1)

    def send_privat(self, method, **params):
        pd = {'id':self.methods.get(method), 'method':method, 'params':params}
        strpar = json.dumps(pd)
        self.wsapp.send(strpar)
        time.sleep(0.1)


class MainWindow(QMainWindow, UiMainWindow):
    settings = QSettings("./config.ini", QSettings.IniFormat)   # файл настроек

    user = ''
    psw = ''

    cur_innerstate = {
            'symbol':'BTCUSD-PERP',
            'numconts':1,
            'orderdist':10,
            'tradingFlag':False,
            'authFlag':False
                    }

    cur_outerstate = {
        'leverage': 0,
        'traderBalance': 0,
        'orderMargin': 0,
        'contractValue': 0,
        'spotPx': 0,
        'markPx': 0
                    }

    current_cell_price = 0      #   текущая тик-цена
    last_cell_price = 0         #   прошлая тик-цена
    current_dist = 0

    listOrders = []
    listContracts = []

    def __init__(self):

        def createdb(fname):
            self.db.setDatabaseName(fname)
            self.db.open()
            q1 = QSqlQuery(self.db)
            q1.prepare("CREATE TABLE users (login TEXT UNIQUE PRIMARY KEY, psw TEXT NOT NULL, apikey TEXT NOT NULL)")
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


        # self.modelorders.setHorizontalHeaderLabels(['clOrdId', 'timestamp', 'openTime', 'orderType', 'timeInForce', 'orderSide', 'px', 'qty', 'leverage', 'paidPx', 'origClOrdId', 'origQty'])

        self.dxthread = WSThread(self)
        self.dxthread.daemon = True
        self.dxthread.start()

        self.show()

    def closeEvent(self, *args, **kwargs):
        if self.db.isOpen():
            self.db.close()

    def authuser(self):
        IV_SIZE = 16  # 128 bit, fixed for the AES algorithm
        KEY_SIZE = 32  # 256 bit meaning AES-256, can also be 128 or 192 bits
        SALT_SIZE = 16  # This size is arbitrary
        q1 = QSqlQuery(self.db)
        q1.prepare("SELECT apikey FROM users WHERE login=:userlogin")
        q1.bindValue(":userlogin", self.user)
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
            self.dxthread.send_privat('auth', type='token', value=ak)

    @pyqtSlot()
    def buttonLogin_clicked(self):
        if not self.user:
            rw = LoginWindow(self.db)
            rw.userlogined.connect(lambda: self.userlogined(rw.user, rw.psw))
            rw.setupUi()
            rw.exec_()

    @pyqtSlot()
    def buttonAK_clicked(self):
        if self.user:
            rw = RegisterWindow(self.db, True, self.user, self.psw)
            rw.akChanged.connect(self.authuser)
            rw.setupUi()
            rw.exec_()
        else:
            mess = QMessageBox()
            mess.setText('Выполните вход')
            mess.setWindowTitle("Ошибка")
            mess.setStyleSheet("color:rgb(128, 64, 32);font: bold 14px;")
            mess.setWindowIcon(QIcon("./images/wowsign.png"))
            mess.exec()

    def userlogined(self, user, psw):
        self.user = user
        self.psw = psw
        self.buttonEnter.setText('вход выполнен: '+self.user)
        self.buttonEnter.setStyleSheet("color:rgb(32, 128, 32); font: bold 11px; border: none;")
        self.authuser()

    @pyqtSlot()
    def button1_clicked(self, name):
        if name != self.current_symbol:
            self.dxthread.changeEx(name, self.current_symbol)
            self.cur_innerstate['symbol'] = name
            self.current_dist = ex[name]['TICK_SIZE']

    @pyqtSlot()
    def startbutton_clicked(self):
        self.mainprocessflag = not self.mainprocessflag
        if self.mainprocessflag:
            self.startbutton.setText('СТОП')
        else:
            self.startbutton.setText('СТАРТ')

    @pyqtSlot()
    def button_closeall_clicked(self):
        self.dxthread.send_privat('cancelAllOrders', symbol=self.current_symbol)

    @pyqtSlot()
    def buttonLeverage_clicked(self):
        rw = ChangeLeverage()
        rw.setupUi(self.current_leverage)
        rw.leveragechanged.connect(lambda: self.dxthread.send_privat('changeLeverage', symbol=self.current_symbol, leverage=int(rw.lineedit_leverage.text())))
        rw.exec_()

    # ========== обработчики сообщений ===========
    # ==== публичные сообщения
    def message_orderbook(self, data):
        a = data

    def message_kline(self, data):
        a = data

    def message_trades(self, data):
        a = data

    def message_liquidations(self, data):
        a = data

    def message_ticker(self, data):
        self.current_contractValue = data['contractValue']

    def message_fundingInfo(self, data):
        a = data

    def message_index(self, data):

        def current_cell_price_changed():
            # завершаем ордеры, которые находятся не на расстоянии дистанции или количество не равно количеству открываемых контрактов
            priceDistBuy = self.current_cell_price - self.cur_innerstate['orderDist'] * self.current_dist
            priceDistSell = self.current_cell_price + self.cur_innerstate['orderDist'] * self.current_dist
            for i in range(0, self.modelorders.rowCount()):
                side = self.modelorders.item(i, 5).data(Qt.DisplayRole)
                px = self.modelorders.item(i, 6).data(Qt.DisplayRole)
                qty = self.modelorders.item(i, 7).data(Qt.DisplayRole)
                clOrdId = self.modelorders.item(i, 0).data(3)
                if (px != priceDistBuy and side == 'BUY') or (px != priceDistSell and side == 'SELL') or (
                        qty != self.current_numconts):
                    self.dxthread.send_privat('cancelOrder', symbol=self.current_symbol, clOrdId=clOrdId)

        self.cur_outerstate['spotPx'] = data['spotPx']
        self.cur_outerstate['markPx'] = data['markPx']
        self.current_cell_price = math.floor(self.cur_outerstate['spotPx'] / self.current_dist) * self.current_dist
        if self.current_cell_price != self.last_cell_price:
            self.last_cell_price = self.current_cell_price
            current_cell_price_changed()



        # открываем ордеры
        if self.mainprocessflag:
            pricetoBuy = self.current_cell_price - self.current_orderdist * self.current_dist
            pricetoSell = self.current_cell_price + self.current_orderdist * self.current_dist

            avbalance = self.current_traderBalance - self.current_orderMargin
            req_margin = self.current_contractValue * self.current_numconts / self.current_leverage
            if req_margin < avbalance:
                if self.chb_buy.checkState() == Qt.Checked:
                    self.dxthread.send_privat('placeOrder', symbol=self.current_symbol, ordType='LIMIT', timeInForce='GTC', side='BUY', px=pricetoBuy, qty=self.current_numconts)
                if self.chb_sell.checkState() == Qt.Checked:
                    self.dxthread.send_privat('placeOrder', symbol=self.current_symbol, ordType='LIMIT', timeInForce='GTC', side='SELL', px=pricetoSell, qty=self.current_numconts)
    # ==== приватные сообщения

    def message_tradingStatus(self, data):
        status = data.get('available')
        self.buttonLeverage.setEnabled(status)
        self.startbutton.setEnabled(status)
        if status:
            self.statusbar.showMessage('Торговля разрешена')
            self.buttonAK.setStyleSheet("color:rgb(32, 192, 32);font: bold 11px; border: none;")
            self.buttonAK.setText('верный api key')
            self.dxthread.send_privat('getTraderStatus', symbol=self.current_symbol)
        else:
            self.statusbar.showMessage('Торговля запрещена')
            self.buttonAK.setStyleSheet("color:rgb(192, 32, 32);font: bold 11px; border: none;")
            self.buttonAK.setText('не верный api key\nнажмите здесь для изменения')

    def message_orderstatus(self, data):
        self.cur_outerstate['leverage'] = data['leverage']
        self.buttonLeverage.setText(str(data['leverage']) + ' x')
        self.cur_outerstate['orderMargin'] = data['orderMargin']
        if data['orderStatus'] == 'ACCEPTED':
            self.listOrders.append(Order(clOrdId=data['clOrdId'], orderSide=data['orderSide'], px=data['px'], qty=data['qty']))

    def message_orderFilled(self, data):
        self.cur_outerstate['traderBalance'] = data['traderBalance']
        self.cur_outerstate['leverage'] = data['leverage']
        self.buttonLeverage.setText(str(data['leverage']) + ' x')
        self.cur_outerstate['orderMargin'] = data['orderMargin']

        ordid = data['origClOrdId']
        listindex = self.modelorders.match(self.modelorders.index(0, 10), 3, ordid)
        for ind in listindex:
            self.modelorders.removeRow(ind.row())

    def message_orderCancelled(self, data):
        self.cur_outerstate['orderMargin'] = data['orderMargin']

    def message_condOrderStatus(self, data):
        a = data

    def message_contractClosed(self, data):
        a = data

    def message_traderStatus(self, data):
        self.cur_outerstate['traderBalance'] = data['traderBalance']
        self.cur_outerstate['leverage'] = data['leverage']
        self.buttonLeverage.setText(str(data['leverage']) + ' x')

    def message_leverage(self, data):
        self.cur_outerstate['leverage'] = data['leverage']
        self.buttonLeverage.setText(str(data['leverage']) + ' x')

    def message_funding(self, data):
        a = data

    def message_position(self, data):
        a = data

app = QApplication([])
win = MainWindow()
sys.exit(app.exec_())
