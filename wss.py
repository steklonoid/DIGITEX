from threading import Thread, Lock
import websocket
import json
import time
import datetime

class WSThread(Thread):
    methods = {'subscribe':1, 'unsubscribe':2, 'subscriptions':3, 'auth':4, 'placeOrder':5, 'cancelOrder':6,
               'cancelAllOrders':7, 'placeCondOrder':8, 'cancelCondOrder':9, 'closeContract':10, 'closePosition':11,
               'getTraderStatus':12, 'changeLeverageAll':13}
    def __init__(self, pc):
        super(WSThread, self).__init__()
        self.pc = pc

    def run(self) -> None:
        def on_open(wsapp):
            self.pc.flConnect = True
            self.pc.statusbar.showMessage('Есть соединение с сервером')
            self.pc.buttonBTC.clicked.emit()
            self.pc.pb_numcont_1.clicked.emit()
            if self.pc.flAuth:
                self.pc.authser()

        def on_close(wsapp):
            self.pc.flConnect = False
            self.pc.statusbar.showMessage('Нет соединения с сервером')

        def on_error(wsapp, error):
            self.pc.statusbar.showMessage(error)

        def on_message(wssapp, message):
            if message == 'ping':
                wssapp.send('pong')
            else:
                self.message = json.loads(message)
                id = self.message.get('id')
                ch = self.message.get('ch')
                if ch:
                    self.pc.listf[ch]['q'].put(self.message.get('data'))
                # elif id:
                #     print(self.message)

        while True:
            try:
                self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_open=on_open,
                                                    on_close=on_close, on_error=on_error, on_message=on_message)
                self.wsapp.run_forever()
                self.pc.statusbar.showMessage('Восстановление соединения с сервером')
            except:
                pass

    def changeEx(self, name, lastname):
        self.send_public('unsubscribe', lastname + '@index', lastname + '@trades', lastname + '@ticker', lastname + '@orderbook_1')
        self.send_public('subscribe', name + '@index', name + '@trades', name + '@ticker', name + '@orderbook_1')

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

class Sender(Thread):
    def __init__(self, q, th):
        super(Sender, self).__init__()
        self.q = q
        self.th = th

    def run(self) -> None:
        while True:
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
        self.workingStartTime = 0
        self.flWorking = False
        self.flClosing = False

    def run(self) -> None:
        while not self.flClosing:
            time.sleep(self.delay)
            if self.flWorking:
                self.pc.l_pnltimer.setText(str(round(time.time() - self.pnlStartTime, 1)))
                self.pc.l_worktimer.setText(str(datetime.timedelta(seconds=round(time.time() - self.workingStartTime))))
            else:
                self.pc.l_pnltimer.setText('0.0')
                self.pc.l_worktimer.setText('0.0')

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
