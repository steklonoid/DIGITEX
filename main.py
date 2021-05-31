import random
import sys
import os
import time
import queue
import logging

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSettings, pyqtSlot, Qt
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from mainWindow import UiMainWindow
from loginWindow import LoginWindow, RegisterWindow, ChangeLeverage
from wss import WSThread, Worker, Senderq, InTimer, Analizator
import hashlib
from Crypto.Cipher import AES # pip install pycryptodome
import math
import numpy as np
from threading import Lock

# = order type
AUTO = 0
MANUAL = 1
OUTSIDE = 2
# = order status
OPENING = 0
ACTIVE = 1
CLOSING = 2

MAXORDERDIST = 5
NUMTICKS = 128
# NUMTICKSHISTORY = 108000

ex = {'BTCUSD-PERP':{'TICK_SIZE':5, 'TICK_VALUE':0.1},'ETHUSD-PERP':{'TICK_SIZE':1, 'TICK_VALUE':1}}

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

class MainWindow(QMainWindow, UiMainWindow):
    settings = QSettings("./config.ini", QSettings.IniFormat)   # файл настроек
    lock = Lock()

    user = ''
    psw = ''

    symbol = 'BTCUSD-PERP'

    leverage = 0
    traderBalance = 0
    traderBalance_usd = 0
    contractValue = 0
    dgtxUsdRate = 0
    current_cellprice = 0       #   текущая тик-цена
    last_cellprice = 0          #   прошлая тик-цена
    current_maxbid = 0          #   текущая нижняя граница стакана цен
    last_maxbid = 0             #   прошлая нижняя граница стакана цен
    current_minask = 0          #   текущая верхняя граница стакана цен
    last_minask = 0             #   прошлая верхняя граница стакана цен

    spotPx = 0                  #   текущая spot-цена
    lastSpotPx = 0              #   прошлая spot-цена
    exDist = 0                  #   TICK_SIZE для текущей валюты
    maxBalance = 0

    listOrders = []             #   список активных ордеров
    listContracts = []          #   список открытых контрактов
    listTick = np.zeros((NUMTICKS, 3), dtype=float)          #   массив последних тиков
    tickCounter = 0             #   счетчик тиков
    market_volatility = 0       #   текущая волатильность
    contractmined = 0
    contractcount = 0
    pnl = 0
    fundingcount = 0
    fundingmined = 0

    flConnect = False           #   флаг нормального соединения с сайтом
    flAuth = False              #   флаг авторизации на сайте (введения правильного API KEY)
    flAutoLiq = False           #   флаг разрешенного авторазмещения ордеров (нажатия кнопки СТАРТ)

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
        logging.basicConfig(filename='info.log', level=logging.INFO, format='%(asctime)s %(message)s')
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
        #   читаем настройки
        s = self.settings.value("l_numconts")
        if s:
            self.l_numconts.setText(s)
        s = self.settings.value("l_dist1")
        if s:
            self.l_dist1.setText(s)
        s = self.settings.value("l_dist2")
        if s:
            self.l_dist2.setText(s)
        s = self.settings.value("l_dist3")
        if s:
            self.l_dist3.setText(s)
        s = self.settings.value("l_dist4")
        if s:
            self.l_dist4.setText(s)
        s = self.settings.value("l_dist5")
        if s:
            self.l_dist5.setText(s)
        s = self.settings.value("l_delayaftermined")
        if s:
            self.l_delayaftermined.setText(s)
        s = self.settings.value("l_losslimit_b")
        if s:
            self.l_losslimit_b.setText(s)
        s = self.settings.value("l_midvollimit")
        if s:
            self.l_midvollimit.setText(s)

        self.sendq = queue.Queue()

        self.dxthread = WSThread(self)
        self.dxthread.daemon = True
        self.dxthread.start()

        self.senderq = Senderq(self.sendq, self.dxthread)
        self.senderq.daemon = True
        self.senderq.start()

        self.listf = {'orderbook_1':{'q':queue.Queue(), 'f':self.message_orderbook_1},
                      'index':{'q':queue.Queue(), 'f':self.message_index},
                      'ticker':{'q':queue.Queue(), 'f':self.message_ticker},
                      'tradingStatus': {'q': queue.Queue(), 'f': self.message_tradingStatus},
                      'orderStatus': {'q': queue.Queue(), 'f': self.message_orderStatus},
                      'orderFilled': {'q': queue.Queue(), 'f': self.message_orderFilled},
                      'orderCancelled': {'q': queue.Queue(), 'f': self.message_orderCancelled},
                      'contractClosed': {'q': queue.Queue(), 'f': self.message_contractClosed},
                      'traderStatus': {'q': queue.Queue(), 'f': self.message_traderStatus},
                      'leverage': {'q': queue.Queue(), 'f': self.message_leverage},
                      'funding': {'q': queue.Queue(), 'f': self.message_funding},
                      'position': {'q': queue.Queue(), 'f': self.message_position}}
        self.listp = []
        for ch in self.listf.keys():
            p = Worker(self.listf[ch]['q'], self.listf[ch]['f'])
            self.listp.append(p)
            p.daemon = True
            p.start()

        self.intimer = InTimer(self)
        self.intimer.daemon = True
        self.intimer.start()

        self.analizator = Analizator(self.midvol)
        self.analizator.daemon = True
        self.analizator.start()

    def closeEvent(self, *args, **kwargs):
        #   закрываем соединение с БД
        if self.db.isOpen():
            self.db.close()
        #   сохраняем настройки
        self.settings.setValue("l_numconts", self.l_numconts.text())
        self.settings.setValue("l_dist1", self.l_dist1.text())
        self.settings.setValue("l_dist2", self.l_dist2.text())
        self.settings.setValue("l_dist3", self.l_dist3.text())
        self.settings.setValue("l_dist4", self.l_dist4.text())
        self.settings.setValue("l_dist5", self.l_dist5.text())
        self.settings.setValue("l_delayaftermined", self.l_delayaftermined.text())
        self.settings.setValue("l_losslimit_b", self.l_losslimit_b.text())
        self.settings.setValue("l_midvollimit", self.l_midvollimit.text())
        #   завершение работы потоков
        self.intimer.flClosing = True
        self.senderq.flClosing = True
        self.dxthread.flClosing = True
        self.analizator.flClosing = True
        self.dxthread.wsapp.close()
        while self.intimer.is_alive() or self.dxthread.is_alive() or self.analizator.is_alive():
            pass

    def returnid(self):
        id = str(round(time.time()) * 1000000 + random.randrange(1000000))
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
            if self.flConnect:
                self.dxthread.send_privat('auth', type='token', value=ak)

    def midvol(self):
        if self.tickCounter > NUMTICKS:
            self.lock.acquire()
            ar = np.array(self.listTick)
            self.lock.release()
            self.market_volatility = round(np.mean(ar, axis=0)[2], 2)

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
        lastname = self.symbol
        self.symbol = name
        self.exDist = ex[name]['TICK_SIZE']
        self.tickCounter = 0
        self.market_volatility = 0
        self.dxthread.changeEx(name, lastname)

    @pyqtSlot()
    def startbutton_clicked(self):
        if self.flConnect:
            self.flAutoLiq = not self.flAutoLiq
            self.intimer.flWorking = self.flAutoLiq
            if self.flAutoLiq:
                self.startbutton.setText('СТОП')
                self.last_cellprice = 0
                self.intimer.pnlStartTime = self.intimer.workingStartTime = time.time()
                self.fundingcount = 0
                self.fundingmined = 0
                self.contractmined = 0
                self.contractcount = 0
                logging.info('-------------start session------------')
                logging.info('Баланс: ' + self.l_balance_dgtx.text())
                logging.info('------------------------------------')
            else:
                self.startbutton.setText('СТАРТ')
                self.dxthread.send_privat('cancelAllOrders', symbol=self.symbol)
                logging.info('------------------------------------')
                logging.info('Время работы: '+self.l_worktimer.text())
                logging.info('Добыто: ' + self.l_fundingmined.text())
                logging.info('Доход от контрактов: ' + self.l_contractmined.text())
                logging.info('Баланс: ' + self.l_balance_dgtx.text())
                logging.info('-------------end session------------')


    @pyqtSlot()
    def buttonLeverage_clicked(self):
        if self.flConnect:
            rw = ChangeLeverage()
            rw.setupUi(self.leverage)
            rw.leveragechanged.connect(lambda: self.dxthread.send_privat('changeLeverageAll', symbol=self.symbol, leverage=int(rw.lineedit_leverage.text())))
            rw.exec_()

    def fill_data(self, data):
        self.traderBalance = data['traderBalance']
        self.maxBalance = max(self.maxBalance, self.traderBalance)
        self.traderBalance_usd = data['traderBalance'] * self.dgtxUsdRate
        self.leverage = data['leverage']

    def update_form(self):
        self.l_balance_dgtx.setText(str(self.traderBalance))
        self.l_balance_usd.setText(str(round(self.traderBalance_usd, 2)))
        self.buttonLeverage.setText(str(self.leverage) + ' x')
        self.l_tickcount.setText(str(self.tickCounter))
        self.l_midvol.setText(str(self.market_volatility))
        self.graphicsview.setText(str(self.spotPx))
        self.l_contractmined.setText(str(round(self.contractmined, 2)))
        self.l_contractcount.setText(str(self.contractcount))
        self.l_pnl.setText(str(round(self.pnl, 2)))
        self.l_fundingcount.setText(str(self.fundingcount))
        self.l_fundingmined.setText(str(round(self.fundingmined, 2)))

    def changemarketsituation(self):

        def checkLimits():
            if not self.flAutoLiq:
                return False
            if len(self.listContracts) != 0:
                return False
            if self.cb_delayaftermined.checkState() == Qt.Checked and self.intimer.pnlTime <= int(self.l_delayaftermined.text()):
                return False
            if self.cb_midvollimit.checkState() == Qt.Checked and float(self.l_midvol.text()) >= float(self.l_midvollimit.text()):
                return False
            if self.cb_losslimit.checkState() == Qt.Checked and float(self.l_balance_dgtx.text()) <= float(self.l_losslimit_b.text()):
                return False
            return True


        if self.current_cellprice != 0:
            distlist = {}
            for spotdist in range(-MAXORDERDIST, MAXORDERDIST + 1):
                price = self.current_cellprice + spotdist * self.exDist
                if price < self.current_maxbid:
                    bonddist = (self.current_maxbid - price) // self.exDist
                elif price > self.current_minask:
                    bonddist = (price - self.current_minask) // self.exDist
                else:
                    bonddist = 0
                bonddist = min(bonddist, MAXORDERDIST)
                if bonddist == 0:
                    bondmod = 0
                elif bonddist == 1:
                    bondmod = int(self.l_dist1.text())
                elif bonddist == 2:
                    bondmod = int(self.l_dist2.text())
                elif bonddist == 3:
                    bondmod = int(self.l_dist3.text())
                elif bonddist == 4:
                    bondmod = int(self.l_dist4.text())
                elif bonddist == 5:
                    bondmod = int(self.l_dist5.text())
                if bondmod != 0:
                    distlist[price] = int(self.l_numconts.text()) * bondmod

        # завершаем ордеры, которые находятся не в списке разрешенных дистанций
        for order in self.listOrders:
            if order.status == ACTIVE:
                if order.px not in distlist.keys():
                    self.dxthread.send_privat('cancelOrder', symbol=self.symbol,
                                                            clOrdId=order.clOrdId)
                    order.status = CLOSING
        # автоматически открываем ордеры
        if checkLimits():
            listorders = [x.px for x in self.listOrders]
            for dist in distlist.keys():
                if dist not in listorders:
                    if dist < self.current_maxbid:
                        side = 'BUY'
                    else:
                        side = 'SELL'
                    id = self.returnid()
                    self.dxthread.send_privat('placeOrder',
                                              clOrdId=id,
                                              symbol=self.symbol,
                                              ordType='LIMIT',
                                              timeInForce='GTC',
                                              side=side,
                                              px=dist,
                                              qty=distlist[dist])
                    self.listOrders.append(Order(
                        clOrdId=id,
                        origClOrdId=id,
                        orderSide=side,
                        orderType='LIMIT',
                        px=dist,
                        qty=distlist[dist],
                        leverage=self.leverage,
                        paidPx=0,
                        type=AUTO,
                        status=OPENING))
    # ========== обработчик респонсов ============
    def message_response(self, id, status):
        pass
    # ========== обработчики сообщений ===========
    # ==== публичные сообщения
    def message_orderbook_1(self, data):
        self.lock.acquire()
        self.current_maxbid = data.get('bids')[0][0]
        self.current_minask = data.get('asks')[0][0]
        if ((self.current_maxbid != self.last_maxbid) or (self.current_minask != self.last_minask)) and self.flConnect:
            self.changemarketsituation()
        self.last_maxbid = self.current_maxbid
        self.last_minask = self.current_minask
        self.lock.release()

    def message_kline(self, data):
        pass

    def message_trades(self, data):
        pass

    def message_liquidations(self, data):
        pass

    def message_ticker(self, data):
        self.dgtxUsdRate = data['dgtxUsdRate']
        self.contractValue = data['contractValue']

    def message_fundingInfo(self, data):
        pass

    def message_index(self, data):
        self.lock.acquire()
        self.spotPx = data['spotPx']

        if self.tickCounter < NUMTICKS:
            if self.tickCounter > 1:
                self.listTick[self.tickCounter] = [data['ts'], self.spotPx, np.absolute(self.spotPx - self.listTick[self.tickCounter - 1][1])]
        else:
            res = np.empty_like(self.listTick)
            res[:-1] = self.listTick[1:]
            res[-1] = [data['ts'], self.spotPx, np.absolute(self.spotPx - res[-2][1])]
            self.listTick = res

        self.tickCounter += 1
        if self.flConnect:
            self.current_cellprice = math.floor(self.spotPx / self.exDist) * self.exDist
            if self.current_cellprice != self.last_cellprice:
                self.changemarketsituation()
            self.last_cellprice = self.current_cellprice

            # завершаем открытые контракты
            for cont in self.listContracts:
                if cont.status == ACTIVE:
                    self.dxthread.send_privat('closeContract', symbol=self.symbol,
                                              contractId=cont.contractId, ordType='MARKET')
                    cont.status = CLOSING
        self.lock.release()

    # ==== приватные сообщения
    def message_tradingStatus(self, data):
        status = data.get('available')
        self.buttonLeverage.setEnabled(status)
        self.startbutton.setEnabled(status)
        if status:
            self.buttonAK.setStyleSheet("color:rgb(32, 192, 32);font: bold 11px; border: none;")
            self.buttonAK.setText('верный api key\nнажмите здесь для изменения')
            self.flAuth = True
            self.dxthread.send_privat('getTraderStatus', symbol=self.symbol)
        else:
            self.buttonAK.setStyleSheet("color:rgb(192, 32, 32);font: bold 11px; border: none;")
            self.buttonAK.setText('не верный api key\nнажмите здесь для изменения')

    def message_orderStatus(self, data):
        self.lock.acquire()
        self.fill_data(data)
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
        self.lock.release()

    def message_orderFilled(self, data):
        self.lock.acquire()
        self.contractmined += (data['pnl'] - self.pnl)
        self.pnl = data['pnl']
        # отменяем ордер
        if data['orderStatus'] == 'FILLED':
            orderidtoremove = data['origClOrdId']
            lo = list(self.listOrders)
            for order in lo:
                if order.origClOrdId == orderidtoremove:
                    self.listOrders.remove(order)
        # создаем контракты
        listnewcontids = [x for x in data['contracts'] if x['qty'] != 0]
        self.contractcount += len(listnewcontids)
        listcontidtoclose = [x['origContractId'] for x in data['contracts'] if x['qty'] == 0]
        for cont in listnewcontids:
            self.listContracts.append(Contract(contractId=cont['contractId'],
                                               origContractId=cont['origContractId'],
                                               status=ACTIVE))
        lc = list(self.listContracts)
        for cont in lc:
            if cont.origContractId in listcontidtoclose:
                self.listContracts.remove(cont)
        self.fill_data(data)
        self.lock.release()

    def message_orderCancelled(self, data):
        self.lock.acquire()
        # если статус отмена
        if data['orderStatus'] == 'CANCELLED':
            listtoremove = [x['origClOrdId'] for x in data['orders']]
            lo = list(self.listOrders)
            for order in lo:
                if order.origClOrdId in listtoremove:
                    self.listOrders.remove(order)
        self.lock.release()

    def message_condOrderStatus(self, data):
        pass

    def message_contractClosed(self, data):
        pass

    def message_traderStatus(self, data):
        self.lock.acquire()
        self.fill_data(data)
        self.pnl = data['pnl']
        self.lock.release()

    def message_leverage(self, data):
        self.lock.acquire()
        self.leverage = data['leverage']
        self.lock.release()

    def message_funding(self, data):
        self.lock.acquire()
        self.fundingcount += 1
        self.fundingmined += data['payout']
        self.pnl = data['pnl']

        self.intimer.pnlStartTime = time.time()
        if self.cb_delayaftermined.checkState() == Qt.Checked:
            self.dxthread.send_privat('cancelAllOrders', symbol=self.symbol)
            self.dxthread.send_privat('getTraderStatus', symbol=self.symbol)
        self.lock.release()

    def message_position(self, data):
        pass

app = QApplication([])
win = MainWindow()
sys.exit(app.exec_())
