from threading import Thread
import websocket
import json
import time

class WSThread(Thread):
    methods = {'subscribe':1, 'unsubscribe':2, 'subscriptions':3, 'auth':4, 'placeOrder':5, 'cancelOrder':6, 'cancelAllOrders':7, 'placeCondOrder':8, 'cancelCondOrder':9, 'closeContract':10, 'closePosition':11, 'getTraderStatus':12, 'changeLeverageAll':13}
    channels = ['orderbook', 'kline', 'trades', 'liquidations', 'ticker', 'fundingInfo', 'index', 'tradingStatus', 'orderStatus', 'orderFilled', 'orderCancelled', 'condOrderStatus', 'contractClosed', 'traderStatus', 'leverage', 'funding', 'position']

    def __init__(self, pc):
        super(WSThread, self).__init__()
        self.message = dict()
        self.pc = pc

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
                try:
                    self.message = json.loads(message)
                except:
                    return
                if self.message.get('id'):
                    id = self.message.get('id')
                    status = self.message.get('status')
                    self.pc.message_response(id, status)
                if self.message.get('ch'):
                    channel = self.message.get('ch')
                    data = self.message.get('data')
                    if channel in self.channels:
                        eval('self.pc.message_' + channel + '(data)')

        self.wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_open=on_open, on_close=on_close, on_error=on_error, on_message=on_message)
        self.wsapp.run_forever()

    def changeEx(self, name, lastname):
        if lastname != '':
            self.send_public('unsubscribe', lastname + '@index', lastname + '@trades', lastname + '@ticker')
        self.send_public('subscribe', name + '@index', name + '@trades', name + '@ticker')

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
        try:
            self.wsapp.send(strpar)
        except:
            print('Ошибка')
        time.sleep(0.1)