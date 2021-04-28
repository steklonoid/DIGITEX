# модуль главного окна
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QGridLayout, QStatusBar, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSplitter, QLineEdit, QCheckBox, QSizePolicy
from PyQt5.QtGui import QIcon, QPainter, QPen, QColor
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
        self.l_balance_dgtx = QLabel()
        self.l_balance_dgtx.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_balance_dgtx.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_balance_dgtx, 0, 1, 1, 1)
        self.l_dgtx = QLabel('DGTX')
        self.l_dgtx.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_dgtx, 0, 2, 1, 1)
        self.l_balance_usd = QLabel()
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
        self.l_margin_order = QLabel()
        self.l_margin_order.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_margin_order.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_margin_order, 1, 1, 1, 1)
        self.l_order = QLabel('ордера')
        self.l_order.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_order, 1, 2, 1, 1)
        self.l_margin_contr = QLabel()
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
        self.l_available_dgtx = QLabel()
        self.l_available_dgtx.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_available_dgtx.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.infogridlayout.addWidget(self.l_available_dgtx, 2, 1, 1, 1)
        self.l_dgtx_2 = QLabel('DGTX')
        self.l_dgtx_2.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_dgtx_2, 2, 2, 1, 1)
        self.l_available_usd = QLabel()
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
        self.l_upnl = QLabel()
        self.l_upnl.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px;")
        self.infogridlayout.addWidget(self.l_upnl, 3, 1, 1, 1)
        self.l_upnl_l = QLabel('UnPnL')
        self.l_upnl_l.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_upnl_l, 3, 2, 1, 1)
        self.l_pnl = QLabel()
        self.l_pnl.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px;")
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
        self.l_spot = QLabel()
        self.l_spot.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_spot, 5, 2, 1, 1)
# ------>
        self.l_price_mark = QLabel('Mark')
        self.l_price_mark.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_price_mark, 6, 1, 1, 1)
        self.l_mark = QLabel()
        self.l_mark.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_mark, 6, 2, 1, 1)
# ------>
        self.l_price_fair = QLabel('Fair')
        self.l_price_fair.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_price_fair, 7, 1, 1, 1)
        self.l_fair = QLabel()
        self.l_fair.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.infogridlayout.addWidget(self.l_fair, 7, 2, 1, 1)


        self.splitterh.addWidget(self.infogridlayoutwidget)
        self.splitterh.setSizes([300, 300])
        self.splitterv.addWidget(self.splitterh)

        self.control_gridLayout_widget = QWidget()
        self.control_gridLayout = QGridLayout(self.control_gridLayout_widget)

        # расстояния открытия / закрытия
        self.openclosedistspacerwidget = QWidget()
        self.openclosedistspacer = QHBoxLayout(self.openclosedistspacerwidget)
        self.le_numcont = QLineEdit()
        self.le_numcont.setText(str(mainwindow.cur_state['numconts']))
        self.le_numcont.editingFinished.connect(le_numcont_editingFinished)
        self.openclosedistspacer.addWidget(QLabel('К-во контр.'))
        self.openclosedistspacer.addWidget(self.le_numcont)
        self.le_orderdist = QLineEdit()
        self.le_orderdist.setText(str(mainwindow.cur_state['orderDist']))
        self.le_orderdist.editingFinished.connect(le_orderdist_editingFinished)
        self.openclosedistspacer.addWidget(QLabel('Дистанция ордера'))
        self.openclosedistspacer.addWidget(self.le_orderdist)
        self.control_gridLayout.addWidget(self.openclosedistspacerwidget, 1, 0, 1, 1)

        #    флажки покупки продажи
        self.chb_sell = QCheckBox()
        self.chb_sell.setText('SELL')
        self.chb_sell.setCheckState(Qt.Checked)
        self.control_gridLayout.addWidget(self.chb_sell, 2, 0, 1, 1)
        self.chb_buy = QCheckBox()
        self.chb_buy.setText('BUY')
        self.chb_buy.setCheckState(Qt.Checked)
        self.control_gridLayout.addWidget(self.chb_buy, 3, 0, 1, 1)
        # кнопка старт
        self.startbutton = QPushButton()
        self.startbutton.setText('СТАРТ')
        self.startbutton.setEnabled(False)
        self.startbutton.clicked.connect(self.startbutton_clicked)
        self.control_gridLayout.addWidget(self.startbutton, 4, 0, 1, 1)
        # кнопка закрыть все ордера
        self.button_closeall = QPushButton()
        self.button_closeall.setText('закрыть все ордера')
        self.button_closeall.clicked.connect(self.button_closeall_clicked)
        self.control_gridLayout.addWidget(self.button_closeall, 4, 1, 1, 1)

        self.splitterv.addWidget(self.control_gridLayout_widget)
        self.splitterv.setSizes([200, 100])
        self.gridLayout.addWidget(self.splitterv, 1, 0, 1, 2)

        self.statusbar = QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)

        cssfile = "./mainWindow.css"
        with open(cssfile, "r") as fh:
            self.setStyleSheet(fh.read())
