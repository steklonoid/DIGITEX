from threading import Thread, Lock
import websocket
import json
import time

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
                ch = self.message.get('ch')
                if ch:
                    self.pc.publicf[ch]['q'].put(self.message.get('data'))

        while True:
            try:
                self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_open=on_open,
                                                    on_close=on_close, on_error=on_error, on_message=on_message)
                self.wsapp.run_forever()
                self.pc.statusbar.showMessage('Восстановление соединения с сервером')
            except:
                pass

    def changeEx(self, name, lastname):
        if lastname != '':
            self.send_public('unsubscribe', lastname + '@index', lastname + '@trades', lastname + '@ticker', lastname + '@orderbook_1')
        self.send_public('subscribe', name + '@index', name + '@trades', name + '@ticker', name + '@orderbook_1')
        self.send_privat('getTraderStatus', symbol=name)

    def send_public(self, method, *params):
        pd = {'id':self.methods.get(method), 'method':method}
        if params:
            pd['params'] = list(params)
        strpar = json.dumps(pd)
        try:
            self.wsapp.send(strpar)
        except:
            pass
        time.sleep(0.1)

    def send_privat(self, method, **params):
        pd = {'id':self.methods.get(method), 'method':method, 'params':params}
        strpar = json.dumps(pd)
        try:
            self.wsapp.send(strpar)
        except:
            pass
        time.sleep(0.1)

class Worker(Thread):
    def __init__(self, q, f):
        super(Worker, self).__init__()
        self.q = q
        self.f = f

    def run(self) -> None:
        while True:
            data = self.q.get()
            self.f(data)

class TraderStatus(Thread):
    def __init__(self, pc):
        super(TraderStatus, self).__init__()
        self.pc = pc
        self.timer = 1

    def run(self) -> None:
        while not self.pc.flClosing:
            time.sleep(self.timer)
            if self.pc.flConnect:
                self.pc.dxthread.send_privat('getTraderStatus', symbol=self.pc.cur_state['symbol'])

class InTimer(Thread):
    def __init__(self, pc):
        super(InTimer, self).__init__()
        self.pc = pc
        self.timer = 0.1

    def run(self) -> None:
        while not self.pc.flClosing:
            time.sleep(self.timer)
            self.pc.l_intimer.setText(str(round(time.time() - self.pc.pnltimer, 1)))

class Animator(Thread):
    def __init__(self, pc):
        super(Animator, self).__init__()
        self.pc = pc
        self.timer = 1/25

    def run(self) -> None:
        while not self.pc.flClosing:
            time.sleep(self.timer)
            self.pc.graphicsview.update()
