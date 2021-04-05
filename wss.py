import websocket
from PyQt5.QtCore import QThread


class ConnectToDigitex(QThread):
    def __init__(self, pc):
        self.pc = pc

    def run(self) -> None:

        def on_message(wsapp, message):
            print(message)
            if message == 'ping':
                wsapp.send('pong')

        wsapp = websocket.WebSocketApp("wss://ws.mapi.digitexfutures.com", on_message=on_message)
        wsapp.run_forever()
