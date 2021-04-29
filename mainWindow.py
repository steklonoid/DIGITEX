# модуль главного окна
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QGridLayout, QStatusBar, QHBoxLayout, QPushButton, QLabel, QSplitter, QLineEdit, QCheckBox, QSizePolicy, QGroupBox, QTableView, QAbstractItemView
from PyQt5.QtGui import QIcon, QPainter, QPen, QColor, QStandardItemModel, QStandardItem
import time

class DisplayField(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setContentsMargins(0, 0, 0, 0)
        self.checktime = time.time()
        self.alpha = 255
        self.alphadirect = -1
        self.alphavel = 60

    def paintEvent(self, event):
        painter = QPainter(self)
        width = painter.viewport().width()  # текущая ширина окна рисования
        height = painter.viewport().height()  # текущая высота окна рисования
        painter.fillRect(0, 0, width, height, Qt.black)  # очищаем окно (черный цвет)

        self.alpha += (round((time.time() - self.checktime) * self.alphavel)) * self.alphadirect
        self.checktime = time.time()
        if self.alpha <= 0:
            self.alpha = 0
            self.alphadirect = -self.alphadirect
        if self.alpha >= 255:
            self.alpha = 255
            self.alphadirect = -self.alphadirect

        painter.setPen(QPen(QColor(255, 128, 0, self.alpha), 5))
        painter.drawLine(0, height // 2, width, height // 2)

class UiMainWindow(object):
    def __init__(self):
        self.buttonlist = []

    def setupui(self, mainwindow):

        def ex_choose():
            mainwindow.buttonex_clicked(self.sender().objectName())
            for b in self.buttonlist:
                if b == self.sender():
                    b.setIcon(QIcon("./images/buttononlineicon.png"))
                else:
                    b.setIcon(QIcon("./images/buttonofflineicon.png"))

        @pyqtSlot()
        def le_numcont_editingFinished():
            v = self.sender().text()
            if not v.isdigit():
                self.sender().setText('1')
                self.cur_state['symbol'] = 1
            elif int(v) < 1:
                self.sender().setText('1')
                self.cur_state['numconts'] = 1
            elif int(v) > 100:
                self.sender().setText('100')
                self.cur_state['numconts'] = 100
            else:
                self.cur_state['numconts'] = int(v)

        @pyqtSlot()
        def le_orderdist_editingFinished():
            v = self.sender().text()
            if not v.isdigit():
                self.sender().setText('10')
                self.cur_state['orderDist'] = 10
            elif int(v) < 1:
                self.sender().setText('1')
                self.cur_state['orderDist'] = 1
            else:
                self.cur_state['orderDist'] = int(v)

        @pyqtSlot()
        def tw_buy_clicked():
            index = self.tw_buy.selectedIndexes()[0]
            row = index.row()
            column = index.column()
            value = self.tm_buy.item(row, 1).data(Qt.DisplayRole)
            if column == 0:
                value -= 1
                value = max(0, value)
            else:
                value += 1
            self.tm_buy.item(row, 1).setData(value, Qt.DisplayRole)

        @pyqtSlot()
        def tw_sell_clicked():
            index = self.tw_sell.selectedIndexes()[0]
            row = index.row()
            column = index.column()
            value = self.tm_sell.item(row, 1).data(Qt.DisplayRole)
            if column == 0:
                value -= 1
                value = max(0, value)
            else:
                value += 1
            self.tm_sell.item(row, 1).setData(value, Qt.DisplayRole)

        mainwindow.setObjectName("MainWindow")
        mainwindow.resize(1200, 800)
        mainwindow.setWindowTitle("Digitex Trading v1.1.0")
        mainwindow.setWindowIcon(QIcon("./images/main_icon.png"))
        self.centralwidget = QWidget(mainwindow)
        self.centralwidget.setObjectName("centralwidget")
        mainwindow.setCentralWidget(self.centralwidget)

        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(1, 1, 1, 1)
        self.gridLayout.setObjectName("gridLayout")

        #   верхняя полоска инфопанель
        self.hspacerwidgetinfo = QWidget()
        self.hspacerwidgetinfo.setObjectName('hspacerwidgetinfo')
        self.hspacerwidgetinfo.setMaximumHeight(50)
        self.hspacerinfo = QHBoxLayout(self.hspacerwidgetinfo)
        self.hspacerinfo.setContentsMargins(0, 0, 0, 0)
        self.hspacerinfo.setObjectName('hspacermenu')
        self.buttonBTC = QPushButton()
        self.buttonBTC.setObjectName('BTCUSD-PERP')
        self.buttonBTC.setText('BTC')
        self.buttonBTC.setMinimumHeight(50)
        self.buttonBTC.clicked.connect(ex_choose)
        self.buttonlist.append(self.buttonBTC)
        self.hspacerinfo.addWidget(self.buttonBTC)
        self.buttonETH = QPushButton()
        self.buttonETH.setObjectName('ETHUSD-PERP')
        self.buttonETH.setText('ETH')
        self.buttonETH.setMinimumHeight(50)
        self.buttonETH.clicked.connect(ex_choose)
        self.buttonlist.append(self.buttonETH)
        self.hspacerinfo.addWidget(self.buttonETH)
        self.gridLayout.addWidget(self.hspacerwidgetinfo, 0, 0, 1, 1)
        #   верхняя полоска вход не выполнен, аккаунт
        self.hspacerwidgetmenu = QWidget()
        self.hspacerwidgetmenu.setObjectName('hspacerwidgetmenu')
        self.hspacerwidgetmenu.setMaximumHeight(50)
        self.hspacermenu = QHBoxLayout(self.hspacerwidgetmenu)
        self.hspacermenu.setContentsMargins(1, 1, 1, 1)
        self.hspacermenu.setObjectName('hspacermenu')
        self.buttonEnter = QPushButton()
        self.buttonEnter.setObjectName('buttonEnter')
        self.buttonEnter.setIcon(QIcon("./images/siluet.png"))
        self.buttonEnter.setMinimumHeight(50)
        self.buttonEnter.setCursor(Qt.PointingHandCursor)
        self.buttonEnter.setText('вход не выполнен: ' + self.user)
        self.buttonEnter.setStyleSheet("color:rgb(128, 32, 32); font: bold 11px; border: none")
        self.buttonEnter.clicked.connect(self.buttonLogin_clicked)
        self.hspacermenu.addWidget(self.buttonEnter)
        self.buttonAK = QPushButton()
        self.buttonAK.setObjectName('buttonAK')
        self.buttonAK.setIcon(QIcon("./images/key.png"))
        self.buttonAK.setMinimumHeight(50)
        self.buttonAK.setCursor(Qt.PointingHandCursor)
        self.buttonAK.setStyleSheet("color:rgb(128, 32, 32); font: bold 11px; border: none")
        self.buttonAK.clicked.connect(self.buttonAK_clicked)
        self.hspacermenu.addWidget(self.buttonAK)
        self.gridLayout.addWidget(self.hspacerwidgetmenu, 0, 1, 1, 1)

        #   горизонтальный сплиттер, делящий остальное пространство внизу на две части
        self.splitterv = QSplitter(Qt.Vertical)
        self.splitterh = QSplitter(Qt.Horizontal)
        self.graphicsview = DisplayField()
        self.splitterh.addWidget(self.graphicsview)
        self.infogridlayoutwidget = QWidget()
        self.infogridlayout = QGridLayout(self.infogridlayoutwidget)
# ------>
        self.l_balance = QLabel('Баланс:')
        self.l_balance.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.infogridlayout.addWidget(self.l_balance, 0, 0, 1, 1)
        self.l_balance_dgtx = QLabel('0')
        self.l_balance_dgtx.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_balance_dgtx.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_balance_dgtx, 0, 1, 1, 1)
        self.l_dgtx = QLabel('DGTX')
        self.l_dgtx.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_dgtx, 0, 2, 1, 1)
        self.l_balance_usd = QLabel('0')
        self.l_balance_usd.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_balance_usd.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_balance_usd, 0, 3, 1, 1)
        self.l_usd = QLabel('USD')
        self.l_usd.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_usd, 0, 4, 1, 1)
# ------>
        self.l_margin = QLabel('Резерв:')
        self.l_margin.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.infogridlayout.addWidget(self.l_margin, 1, 0, 1, 1)
        self.l_margin_order = QLabel('0')
        self.l_margin_order.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_margin_order.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_margin_order, 1, 1, 1, 1)
        self.l_order = QLabel('ордера')
        self.l_order.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_order, 1, 2, 1, 1)
        self.l_margin_contr = QLabel('0')
        self.l_margin_contr.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_margin_contr.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_margin_contr, 1, 3, 1, 1)
        self.l_contr = QLabel('контракты')
        self.l_contr.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_contr, 1, 4, 1, 1)
# ------>
        self.l_available = QLabel('Свободно:')
        self.l_available.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.infogridlayout.addWidget(self.l_available, 2, 0, 1, 1)
        self.l_available_dgtx = QLabel('0')
        self.l_available_dgtx.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_available_dgtx.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_available_dgtx, 2, 1, 1, 1)
        self.l_dgtx_2 = QLabel('DGTX')
        self.l_dgtx_2.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_dgtx_2, 2, 2, 1, 1)
        self.l_available_usd = QLabel('0')
        self.l_available_usd.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_available_usd.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_available_usd, 2, 3, 1, 1)
        self.l_usd_2 = QLabel('USD')
        self.l_usd_2.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_usd_2, 2, 4, 1, 1)
# ------>
        self.l_profit = QLabel('Профит:')
        self.l_profit.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.infogridlayout.addWidget(self.l_profit, 3, 0, 1, 1)
        self.l_upnl = QLabel('0')
        self.l_upnl.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px;")
        self.l_upnl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_upnl, 3, 1, 1, 1)
        self.l_upnl_l = QLabel('UnPnL')
        self.l_upnl_l.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_upnl_l, 3, 2, 1, 1)
        self.l_pnl = QLabel('0')
        self.l_pnl.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px;")
        self.l_pnl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_pnl, 3, 3, 1, 1)
        self.l_pnl_l = QLabel('PnL')
        self.l_pnl_l.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_pnl_l, 3, 4, 1, 1)
# ------>
        self.l_leverage = QLabel('Плечо:')
        self.l_leverage.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.infogridlayout.addWidget(self.l_leverage, 4, 0, 1, 1)
        self.buttonLeverage = QPushButton()
        self.buttonLeverage.setObjectName('buttonLeverage')
        self.buttonLeverage.setText('0 x')
        self.buttonLeverage.setToolTip('Плечо')
        self.buttonLeverage.setCursor(Qt.PointingHandCursor)
        self.buttonLeverage.clicked.connect(self.buttonLeverage_clicked)
        self.buttonLeverage.setEnabled(False)
        self.infogridlayout.addWidget(self.buttonLeverage, 4, 1, 1, 4)
# ------>
        self.l_price = QLabel('Цены:')
        self.l_price.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.infogridlayout.addWidget(self.l_price, 5, 0, 1, 1)
        self.l_price_spot = QLabel('Spot')
        self.l_price_spot.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_price_spot, 5, 1, 1, 1)
        self.l_spot = QLabel('0')
        self.l_spot.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_spot, 5, 2, 1, 1)
# ------>
        self.l_price_mark = QLabel('Mark')
        self.l_price_mark.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_price_mark, 6, 1, 1, 1)
        self.l_mark = QLabel('0')
        self.l_mark.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_mark, 6, 2, 1, 1)
# ------>
        self.l_price_fair = QLabel('Fair')
        self.l_price_fair.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_price_fair, 7, 1, 1, 1)
        self.l_fair = QLabel('0')
        self.l_fair.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_fair, 7, 2, 1, 1)


        self.splitterh.addWidget(self.infogridlayoutwidget)
        self.splitterh.setSizes([300, 300])
        self.splitterv.addWidget(self.splitterh)

        self.bottom_hspacer_widget = QWidget()
        self.bottom_hspacer = QHBoxLayout(self.bottom_hspacer_widget)
        self.gb_manual = QGroupBox()
        self.gb_manual.setTitle('Ручное управление')
        self.gl_manual = QGridLayout()
        self.gb_manual.setLayout(self.gl_manual)
        self.tm_buy = QStandardItemModel()
        self.tm_buy.setColumnCount(2)
        self.tm_buy.setHorizontalHeaderLabels(['Тики', 'К-во'])
        for i in range(5):
            it1 = QStandardItem()
            it1.setData(i + 1, Qt.DisplayRole)
            it1.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            it2 = QStandardItem()
            it2.setData(0, Qt.DisplayRole)
            it2.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.tm_buy.appendRow([it1, it2])
        self.tw_buy = QTableView()
        self.tw_buy.setObjectName('tw_buy')
        self.tw_buy.setModel(self.tm_buy)
        self.tw_buy.verticalHeader().close()
        self.tw_buy.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tw_buy.clicked.connect(tw_buy_clicked)
        self.gl_manual.addWidget(self.tw_buy, 0, 0, 1, 1)
        self.tm_sell = QStandardItemModel()
        self.tm_sell.setColumnCount(2)
        self.tm_sell.setHorizontalHeaderLabels(['Тики', 'К-во'])
        for i in range(5):
            it1 = QStandardItem()
            it1.setData(i + 1, Qt.DisplayRole)
            it1.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            it2 = QStandardItem()
            it2.setData(0, Qt.DisplayRole)
            it2.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.tm_sell.appendRow([it1, it2])
        self.tw_sell = QTableView()
        self.tw_sell.setObjectName('tw_sell')
        self.tw_sell.setModel(self.tm_sell)
        self.tw_sell.verticalHeader().close()
        self.tw_sell.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tw_sell.clicked.connect(tw_sell_clicked)
        self.gl_manual.addWidget(self.tw_sell, 0, 1, 1, 1)
        self.pb_buy = QPushButton()
        self.pb_buy.setText('BUY')
        self.gl_manual.addWidget(self.pb_buy, 1, 0, 1, 1)
        self.pb_sell = QPushButton()
        self.pb_sell.setText('SELL')
        self.gl_manual.addWidget(self.pb_sell, 1, 1, 1, 1)
        self.bottom_hspacer.addWidget(self.gb_manual)

        self.gb_auto = QGroupBox()
        self.gb_auto.setTitle('Автомат')
        self.gl_auto = QGridLayout()
        self.gb_auto.setLayout(self.gl_auto)
        self.gl_auto.addWidget(QLabel('К-во контр.'), 0, 0, 1, 1)
        self.le_numcont = QLineEdit()
        self.le_numcont.setText(str(mainwindow.cur_state['numconts']))
        self.le_numcont.editingFinished.connect(le_numcont_editingFinished)
        self.gl_auto.addWidget(self.le_numcont, 0, 1, 1, 1)
        self.gl_auto.addWidget(QLabel('Дистанция ордера'), 1, 0, 1, 1)
        self.le_orderdist = QLineEdit()
        self.le_orderdist.setText(str(mainwindow.cur_state['orderDist']))
        self.le_orderdist.editingFinished.connect(le_orderdist_editingFinished)
        self.gl_auto.addWidget(self.le_orderdist, 1, 1, 1, 1)
        #    флажки покупки продажи
        self.chb_sell = QCheckBox()
        self.chb_sell.setText('SELL')
        self.chb_sell.setCheckState(Qt.Checked)
        self.gl_auto.addWidget(self.chb_sell, 2, 0, 1, 1)
        self.chb_buy = QCheckBox()
        self.chb_buy.setText('BUY')
        self.chb_buy.setCheckState(Qt.Checked)
        self.gl_auto.addWidget(self.chb_buy, 2, 1, 1, 1)
        # кнопка старт
        self.startbutton = QPushButton()
        self.startbutton.setText('СТАРТ')
        self.startbutton.setEnabled(False)
        self.startbutton.clicked.connect(self.startbutton_clicked)
        self.gl_auto.addWidget(self.startbutton, 3, 0, 1, 1)
        # кнопка закрыть все ордера
        self.button_closeall = QPushButton()
        self.button_closeall.setText('закрыть все ордера')
        self.button_closeall.clicked.connect(self.button_closeall_clicked)
        self.gl_auto.addWidget(self.button_closeall, 3, 1, 1, 1)
        self.bottom_hspacer.addWidget(self.gb_auto)

        self.splitterv.addWidget(self.bottom_hspacer_widget)
        self.splitterv.setSizes([200, 100])
        self.gridLayout.addWidget(self.splitterv, 1, 0, 1, 2)

        self.statusbar = QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)

        cssfile = "./mainWindow.css"
        with open(cssfile, "r") as fh:
            self.setStyleSheet(fh.read())
