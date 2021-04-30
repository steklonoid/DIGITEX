import sys
import os
import threading
import time

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QIcon
from PyQt5.QtCore import QSettings, pyqtSlot, Qt
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from mainWindow import UiMainWindow
from loginWindow import LoginWindow, RegisterWindow, ChangeLeverage
from wss import WSThread, Worker
import hashlib
from Crypto.Cipher import AES # pip install pycryptodome
import math

# = order type
AUTO = 0
MANUAL = 1
OUTSIDE = 2
# = order status
OPENING = 0
ACTIVE = 1
CLOSING = 2

MAXORDERDIST = 5
MINSAFEDIST = 2

ex = {'BTCUSD-PERP':{'TICK_SIZE':5, 'TICK_VALUE':0.1},'ETHUSD-PERP':{'TICK_SIZE':0.25, 'TICK_VALUE':0.25}}

class Order():
    def __init__(self, **kwargs):
        self.clOrdId = kwargs['clOrdId']
        self.origClOrdId = kwargs['origClOrdId']
        self.orderSide = kwargs['orderSide']
        self.orderType = kwargs['orderType']
        self.px = kwargs['px']
        self.qty = kwargs['qty']
        self.leverage = kwargs['leverage']
        self.paidPx = kwargs['paidPx']
        self.type = kwargs['type']
        self.status = kwargs['status']

class Contract():
    def __init__(self, **kwargs):
        self.contractId = kwargs['contractId']
        self.origContractId = kwargs['origContractId']
        self.status = kwargs['status']

class ChannelData():
    def __init__(self, messages=[], public=True):
        self.messages = messages
        self.public = public

class MainWindow(QMainWindow, UiMainWindow):
    settings = QSettings("./config.ini", QSettings.IniFormat)   # файл настроек

    user = ''
    psw = ''

    cur_state = {
        'symbol': '',
        'numconts': 1,
        'orderDist': 5,
        'tradingFlag': False,
        'connectFlag': False,
        'leverage': 0,
        'traderBalance': 0,
        'orderMargin': 0,
        'positionMargin':0,
        'contractValue': 0,
        'spotPx': 0,
        'markPx': 0,
        'fairPx':0,
        'dgtxUsdRate':0,
        'pnl':0,
        'upnl':0
                    }
    channels = {'orderbook_1': {'mes':[], 'public':True}, 'kline': {'mes':[], 'public':True}, 'trades': {'mes':[], 'public':True}, 'liquidations': {'mes':[], 'public':True}, 'ticker': {'mes':[], 'public':True}, 'fundingInfo': {'mes':[], 'public':True},
                'index': {'mes':[], 'public':True}, 'tradingStatus': {'mes':[], 'public':False}, 'orderStatus': {'mes':[], 'public':False}, 'orderFilled': {'mes':[], 'public':False}, 'orderCancelled': {'mes':[], 'public':False},
                'condOrderStatus': {'mes':[], 'public':False}, 'contractClosed': {'mes':[], 'public':False}, 'traderStatus': {'mes':[], 'public':False}, 'leverage': {'mes':[], 'public':False}, 'funding': {'mes':[], 'public':False},
                'position': {'mes':[], 'public':False}}

    current_cellprice = 0      #   текущая тик-цена
    last_cellprice = 0         #   прошлая тик-цена
    current_maxbid = 0
    last_maxbid = 0
    current_minask = 0
    last_minask = 0

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

        # создание визуальной формы
        self.setupui(self)
        self.show()

        # создание потока, в котором происходит подключение к вебсокету, обработка приходящих сообщений и запись их
        # в переменную channels
        self.dxthread = WSThread(self)
        self.dxthread.daemon = True
        self.dxthread.start()
        # создание потока, который читает данные из переменной channels и обрабатывает их
        self.worker = Worker(self)
        self.worker.daemon = True
        self.worker.start()


    def closeEvent(self, *args, **kwargs):
        if self.db.isOpen():
            self.db.close()

    def returnid(self):
        id = str(round(time.time() * 1000000))
        return id

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
    def buttonex_clicked(self, name):
        if name != self.cur_state['symbol']:
            lastname = self.cur_state['symbol']
            self.cur_state['symbol'] = name
            self.dxthread.changeEx(name, lastname)


    @pyqtSlot()
    def startbutton_clicked(self):
        self.cur_state['tradingFlag'] = not self.cur_state['tradingFlag']
        if self.cur_state['tradingFlag']:
            self.startbutton.setText('СТОП')
            self.last_cellprice = 0
        else:
            self.startbutton.setText('СТАРТ')
            self.dxthread.send_privat('cancelAllOrders', symbol=self.cur_state['symbol'])

    @pyqtSlot()
    def buttonLeverage_clicked(self):
        rw = ChangeLeverage()
        rw.setupUi(self.cur_state['leverage'])
        rw.leveragechanged.connect(lambda: self.dxthread.send_privat('changeLeverageAll', symbol=self.cur_state['symbol'], leverage=int(rw.lineedit_leverage.text())))
        rw.exec_()

    @pyqtSlot()
    def pb_buy_clicked(self):
        for i in range(self.tm_buy.rowCount()):
            current_dist = self.tm_buy.item(i, 0).data(Qt.DisplayRole)
            value = self.tm_buy.item(i, 1).data(Qt.DisplayRole)
            if value != 0:
                id = self.returnid()
                pricetoBuy = min(self.current_cellprice,
                                 self.cur_state['minAsk'] - self.cur_state['orderDist'] * current_dist)
                self.dxthread.send_privat('placeOrder',
                                          clOrdId=id,
                                          symbol=self.cur_state['symbol'],
                                          ordType='LIMIT',
                                          timeInForce='GTC',
                                          side='BUY',
                                          px=pricetoBuy,
                                          qty=self.cur_state['numconts'])
                self.listOrders.append(Order(
                    clOrdId=id,
                    origClOrdId=id,
                    orderSide='BUY',
                    orderType='LIMIT',
                    px=pricetoBuy,
                    qty=self.cur_state['numconts'],
                    leverage=self.cur_state['leverage'],
                    paidPx=0,
                    type=MANUAL,
                    status=OPENING))

    @pyqtSlot()
    def pb_sell_clicked(self):
        for i in range(self.tm_sell.rowCount()):
            current_dist = self.tm_sell.item(i, 0).data(Qt.DisplayRole)
            value = self.tm_sell.item(i, 1).data(Qt.DisplayRole)
            if value != 0:
                id = self.returnid()
                pricetoSell = max(self.current_cellprice,
                                  self.cur_state['maxBid'] + self.cur_state['orderDist'] * current_dist)
                self.dxthread.send_privat('placeOrder',
                                          clOrdId=id,
                                          symbol=self.cur_state['symbol'],
                                          ordType='LIMIT',
                                          timeInForce='GTC',
                                          side='SELL',
                                          px=pricetoSell,
                                          qty=self.cur_state['numconts'])
                self.listOrders.append(Order(
                    clOrdId=id,
                    origClOrdId=id,
                    orderSide='SELL',
                    orderType='LIMIT',
                    px=pricetoSell,
                    qty=self.cur_state['numconts'],
                    leverage=self.cur_state['leverage'],
                    paidPx=0,
                    type=MANUAL,
                    status=OPENING))

    def update_cur_state(self, data):
        self.cur_state['traderBalance'] = data['traderBalance']
        self.l_balance_dgtx.setText(str(data['traderBalance']))
        self.l_balance_usd.setText(str(round(data['traderBalance'] * self.cur_state['dgtxUsdRate'], 2)))

        self.cur_state['leverage'] = data['leverage']
        self.buttonLeverage.setText(str(data['leverage']) + ' x')

        self.cur_state['orderMargin'] = data['orderMargin']
        self.l_margin_order.setText(str(data['orderMargin']))
        self.cur_state['positionMargin'] = data['positionMargin']
        self.l_margin_contr.setText(str(data['positionMargin']))
        available = round(data['traderBalance'] - data['orderMargin'] - data['positionMargin'], 4)
        self.l_available_dgtx.setText(str(available))
        self.l_available_usd.setText(str(round(available * self.cur_state['dgtxUsdRate'], 2)))
        self.cur_state['pnl'] = data['pnl']
        self.l_pnl.setText(str(data['pnl']))
        self.cur_state['upnl'] = data['upnl']
        self.l_upnl.setText(str(data['upnl']))

    def changemarketsituation(self):
        if self.current_cellprice != 0:
            current_dist = ex[self.cur_state['symbol']]['TICK_SIZE']
            distlist = []
            for dist in range(self.current_cellprice - current_dist * MAXORDERDIST, self.current_cellprice + current_dist * (MAXORDERDIST + 1), current_dist):
                if (dist <= self.current_maxbid - current_dist * MINSAFEDIST) or (dist >= self.current_minask + current_dist * MINSAFEDIST):
                    distlist.append(dist)
        # завершаем ордеры, которые находятся не в списке разрешенных дистанций
        for order in self.listOrders:
            if order.status == ACTIVE:
                if order.px not in distlist:
                    self.dxthread.send_privat('cancelOrder', symbol=self.cur_state['symbol'],
                                                            clOrdId=order.clOrdId)
                    order.status = CLOSING
        # автоматически открываем ордеры
        if self.cur_state['tradingFlag']:
            available = self.cur_state['traderBalance'] - self.cur_state['orderMargin'] - self.cur_state[
                'positionMargin']
            req_margin = self.cur_state['contractValue'] * self.cur_state['numconts'] / self.cur_state[
                'leverage']
            if req_margin < available:
                listorderdist = [x.px for x in self.listOrders]
                for dist in distlist:
                    if dist not in listorderdist:
                        if dist < self.current_maxbid:
                            side = 'BUY'
                        else:
                            side = 'SELL'
                        id = self.returnid()
                        self.dxthread.send_privat('placeOrder',
                                                  clOrdId=id,
                                                  symbol=self.cur_state['symbol'],
                                                  ordType='LIMIT',
                                                  timeInForce='GTC',
                                                  side=side,
                                                  px=dist,
                                                  qty=self.cur_state['numconts'])
                        self.listOrders.append(Order(
                            clOrdId=id,
                            origClOrdId=id,
                            orderSide=side,
                            orderType='LIMIT',
                            px=dist,
                            qty=self.cur_state['numconts'],
                            leverage=self.cur_state['leverage'],
                            paidPx=0,
                            type=AUTO,
                            status=OPENING))
    # ========== обработчик респонсов ============
    def message_response(self, id, status):
        a = id
    # ========== обработчики сообщений ===========
    # ==== публичные сообщения
    def message_orderbook_1(self, data):
        self.current_maxbid = data.get('bids')[0][0]
        self.current_minask = data.get('asks')[0][0]
        if (self.current_maxbid != self.last_maxbid) or (self.current_minask != self.last_minask):
            self.changemarketsituation()
        self.last_maxbid = self.current_maxbid
        self.last_minask = self.current_minask

    def message_kline(self, data):
        a = data

    def message_trades(self, data):
        a = data

    def message_liquidations(self, data):
        a = data

    def message_ticker(self, data):
        self.cur_state['dgtxUsdRate'] = data['dgtxUsdRate']
        self.cur_state['contractValue'] = data['contractValue']

    def message_fundingInfo(self, data):
        a = data

    def message_index(self, data):
        self.cur_state['spotPx'] = data['spotPx']
        self.l_spot.setText(str(data['spotPx']))
        self.cur_state['markPx'] = data['markPx']
        self.l_mark.setText(str(data['markPx']))
        self.cur_state['fairPx'] = data['fairPx']
        self.l_fair.setText(str(data['fairPx']))

        current_dist = ex[self.cur_state['symbol']]['TICK_SIZE']
        self.current_cellprice = math.floor(self.cur_state['spotPx'] / current_dist) * current_dist
        if self.current_cellprice != self.last_cellprice:
            self.changemarketsituation()
        self.last_cellprice = self.current_cellprice

        # завершаем открытые контракты
        for cont in self.listContracts:
            if cont.status == ACTIVE:
                self.dxthread.send_privat('closeContract', symbol=self.cur_state['symbol'],
                                          contractId=cont.contractId, ordType='MARKET')
                cont.status = CLOSING


    # ==== приватные сообщения
    def message_tradingStatus(self, data):
        status = data.get('available')
        self.buttonLeverage.setEnabled(status)
        self.startbutton.setEnabled(status)
        if status:
            self.statusbar.showMessage('Торговля разрешена')
            self.buttonAK.setStyleSheet("color:rgb(32, 192, 32);font: bold 11px; border: none;")
            self.buttonAK.setText('верный api key')
            self.dxthread.send_privat('getTraderStatus', symbol=self.cur_state['symbol'])
        else:
            self.statusbar.showMessage('Торговля запрещена')
            self.buttonAK.setStyleSheet("color:rgb(192, 32, 32);font: bold 11px; border: none;")
            self.buttonAK.setText('не верный api key\nнажмите здесь для изменения')

    def message_orderStatus(self, data):
        self.update_cur_state(data)
        # если приходит сообщение о подтвержденном ордере
        if data['orderStatus'] == 'ACCEPTED':
            foundOrder = False
            origClOrdId = data['origClOrdId']
            for order in self.listOrders:
                if order.origClOrdId == origClOrdId and order.status == OPENING:
                    order.status = ACTIVE
                    order.paidPx = data['paidPx']
                    foundOrder = True
            if not foundOrder:
                self.listOrders.append(Order(clOrdId=data['clOrdId'],
                                             origClOrdId=data['origClOrdId'],
                                             orderSide=data['orderSide'],
                                             orderType=data['orderType'],
                                             px=data['px'],
                                             qty=data['qty'],
                                             leverage=data['leverage'],
                                             paidPx = data['paidPx'],
                                             type = OUTSIDE,
                                             status=ACTIVE))

    def message_orderFilled(self, data):
        self.update_cur_state(data)
        # отменяем ордер
        if data['orderStatus'] == 'FILLED':
            orderidtoremove = data['origClOrdId']
            lo = list(self.listOrders)
            for order in lo:
                if order.origClOrdId == orderidtoremove:
                    self.listOrders.remove(order)
        # создаем контракты
        listnewcontids = [x for x in data['contracts'] if x['qty'] != 0]
        listcontidtoclose = [x['origContractId'] for x in data['contracts'] if x['qty'] == 0]
        for cont in listnewcontids:
            self.listContracts.append(Contract(contractId=cont['contractId'],
                                               origContractId=cont['origContractId'],
                                               status=ACTIVE))
        lc = list(self.listContracts)
        for cont in lc:
            if cont.origContractId in listcontidtoclose:
                self.listContracts.remove(cont)

    def message_orderCancelled(self, data):
        self.cur_state['orderMargin'] = data['orderMargin']
        # если статус отмена
        if data['orderStatus'] == 'CANCELLED':
            listtoremove = [x['origClOrdId'] for x in data['orders']]
            lo = list(self.listOrders)
            for order in lo:
                if order.origClOrdId in listtoremove:
                    self.listOrders.remove(order)

    def message_condOrderStatus(self, data):
        a = data

    def message_contractClosed(self, data):
        a = data

    def message_traderStatus(self, data):
        self.update_cur_state(data)

    def message_leverage(self, data):
        self.cur_state['leverage'] = data['leverage']
        self.buttonLeverage.setText(str(data['leverage']) + ' x')

    def message_funding(self, data):
        a = data

    def message_position(self, data):
        a = data

app = QApplication([])
win = MainWindow()
sys.exit(app.exec_())
