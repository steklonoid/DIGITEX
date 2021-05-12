from threading import Thread, Lock
import websocket
import json
import time
import datetime
import logging


class WSThread(Thread):
    methods = {'subscribe':1, 'unsubscribe':2, 'subscriptions':3, 'auth':4, 'placeOrder':5, 'cancelOrder':6,
               'cancelAllOrders':7, 'placeCondOrder':8, 'cancelCondOrder':9, 'closeContract':10, 'closePosition':11,
               'getTraderStatus':12, 'changeLeverageAll':13}
    def __init__(self, pc):
        super(WSThread, self).__init__()
        self.pc = pc
        self.flClosing = False

    def run(self) -> None:
        def on_open(wsapp):
            logging.info('open')
            self.pc.flConnect = True
            self.pc.statusbar.showMessage('Есть соединение с сервером')
            self.pc.buttonBTC.clicked.emit()
            self.pc.pb_numcont_1.clicked.emit()
            if self.pc.flAuth:
                self.pc.authser()

        def on_close(wsapp):
            logging.info('close')
            self.pc.flConnect = False
            self.pc.statusbar.showMessage('Нет соединения с сервером')

        def on_error(wsapp, error):
            logging.info(error)
            self.pc.statusbar.showMessage(error)

        def on_message(wssapp, message):
            if message == 'ping':
                wssapp.send('pong')
            else:
                self.message = json.loads(message)
                id = self.message.get('id')
                status = self.message.get('status')
                ch = self.message.get('ch')
                if ch:
                    self.pc.listf[ch]['q'].put(self.message.get('data'))
                elif status:
                    if status == 'error':
                        logging.info(self.message)

        while not self.flClosing:
            try:
                self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_open=on_open,
                                                    on_close=on_close, on_error=on_error, on_message=on_message)
                self.wsapp.run_forever()
                self.pc.statusbar.showMessage('Восстановление соединения с сервером')
            except:
                pass

    def changeEx(self, name, lastname):
        self.send_public('unsubscribe', lastname + '@index', lastname + '@ticker', lastname + '@orderbook_1')
        self.send_public('subscribe', name + '@index', name + '@ticker', name + '@orderbook_1')

    def send_public(self, method, *params):
        pd = {'id':self.methods.get(method), 'method':method}
        if params:
            pd['params'] = list(params)
        strpar = json.dumps(pd)
        self.pc.sendq.put(strpar)

    def send_privat(self, method, **params):
        pd = {'id':self.methods.get(method), 'method':method, 'params':params}
        strpar = json.dumps(pd)
        self.pc.sendq.put(strpar)


class Worker(Thread):
    def __init__(self, q, f):
        super(Worker, self).__init__()
        self.q = q
        self.f = f

    def run(self) -> None:
        while True:
            data = self.q.get()
            self.f(data)


class Senderq(Thread):
    def __init__(self, q, th):
        super(Senderq, self).__init__()
        self.q = q
        self.th = th
        self.flClosing = False

    def run(self) -> None:
        while not self.flClosing:
            time.sleep(0.1)
            data = self.q.get()
            try:
                self.th.wsapp.send(data)
            except:
                pass


class TraderStatus(Thread):
    def __init__(self, pc):
        super(TraderStatus, self).__init__()
        self.pc = pc
        self.timer = 1
        self.flClosing = False

    def run(self) -> None:
        while not self.flClosing:
            time.sleep(self.timer)
            if self.pc.flConnect and self.pc.flAuth:
                self.pc.dxthread.send_privat('getTraderStatus', symbol=self.pc.symbol)


class InTimer(Thread):
    def __init__(self, pc):
        super(InTimer, self).__init__()
        self.pc = pc
        self.delay = 0.1
        self.pnlStartTime = 0
        self.pnlTime = 0
        self.workingStartTime = 0
        self.flWorking = False
        self.flClosing = False

    def run(self) -> None:
        while not self.flClosing:
            time.sleep(self.delay)
            if self.flWorking:
                self.pnlTime = time.time() - self.pnlStartTime
                self.pc.l_pnltimer.setText(str(round(self.pnlTime, 1)))
                self.pc.l_worktimer.setText(str(datetime.timedelta(seconds=round(time.time() - self.workingStartTime))))


class Animator(Thread):
    def __init__(self, pc):
        super(Animator, self).__init__()
        self.pc = pc
        self.timer = 1/25
        self.flClosing = False

    def run(self) -> None:
        while not self.flClosing:
            time.sleep(self.timer)
            self.pc.graphicsview.update()
