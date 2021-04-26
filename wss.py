from threading import Thread, Lock
import websocket
import json
import time

class WSThread(Thread):

    methods = {'subscribe':1, 'unsubscribe':2, 'subscriptions':3, 'auth':4, 'placeOrder':5, 'cancelOrder':6, 'cancelAllOrders':7, 'placeCondOrder':8, 'cancelCondOrder':9, 'closeContract':10, 'closePosition':11, 'getTraderStatus':12, 'changeLeverageAll':13}


    def __init__(self, pc):
        super(WSThread, self).__init__()
        self.message = dict()
        self.pc = pc
        self.lock = Lock()

    def run(self) -> None:
        def on_open(wsapp):
            self.pc.buttonBTC.clicked.emit()

        def on_close(wsapp):
            print('on_close')

        def on_error(wsapp, error):
            print('error ' + error)

        def on_message(wssapp, message):
            if message == 'ping':
                wssapp.send('pong')
            else:
                self.message = json.loads(message)
                if self.message.get('id'):
                    id = self.message.get('id')
                    status = self.message.get('status')
                    self.pc.message_response(id, status)
                if self.message.get('ch'):
                    channel = self.message.get('ch')
                    data = self.message.get('data')
                    self.lock.acquire()
                    self.pc.channels[channel].append(data)
                    self.lock.release()


        self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_open=on_open, on_close=on_close, on_error=on_error, on_message=on_message)
        self.wsapp.run_forever()

    def changeEx(self, name, lastname):
        if lastname != '':
            self.send_public('unsubscribe', lastname + '@index', lastname + '@trades', lastname + '@ticker', lastname + '@orderbook_1')
        self.send_public('subscribe', name + '@index', name + '@trades', name + '@ticker', name + '@orderbook_1')

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

class SuperViser(Thread):
    def __init__(self, pc):
        super(SuperViser, self).__init__()
        self.pc = pc
        self.timer = 0.2
        self.lock = Lock()

    def run(self) -> None:
        oldtime = time.time()
        while True:
            for channel in self.pc.channels.keys():
                self.lock.acquire()
                listmes = self.pc.channels[channel]
                self.lock.release()
                if listmes:
                    data = listmes[-1]
                    eval('self.pc.message_' + channel + '(data)')
                    print(len(listmes))
                    self.lock.acquire()
                    listmes.clear()
                    self.lock.release()
