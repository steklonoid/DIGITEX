# модуль главного окна
from PyQt5.QtCore import Qt, pyqtSlot, QRectF
from PyQt5.QtWidgets import QWidget, QGridLayout, QStatusBar, QHBoxLayout, QPushButton, QLabel, QSplitter, QOpenGLWidget, QSizePolicy, QGroupBox, QTableView, QAbstractItemView, QHeaderView, QCheckBox
from PyQt5.QtGui import QIcon, QPainter, QStandardItemModel, QStandardItem, QPen, QColor, QFont, QPainterPath, QMouseEvent
from OpenGL import GL
import time

class DisplayField(QOpenGLWidget):
    def __init__(self, pc):
        QWidget.__init__(self)
        self.pc = pc
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setContentsMargins(0, 0, 0, 0)

        self.downaxe = 20   # размер поля для отображения легенды нижней оси, px
        self.rightaxe = 50  # размер поля для отображения легенды правой оси, px
        self.upaxe = 20     # размер поля для отображения легенды верхней оси, px
        self.fontcurprice = QFont("Helvetica", 14, QFont.Bold)
        self.fontcellprice = QFont("Helvetica", 10, QFont.Bold)

    def initializeGL(self) -> None:
        GL.glClearColor(0, 0, 0, 1)

    def resizeGL(self, w: int, h: int) -> None:
        GL.glLoadIdentity()

    def paintGL(self) -> None:
        painter = QPainter(self)
        width = painter.viewport().width() - self.rightaxe  # текущая ширина окна рисования
        height = painter.viewport().height()  # текущая высота окна рисования
        painter.beginNativePainting()
        # рисуем оси
        painter.setPen(QPen(Qt.white, 1))
        painter.drawLine(0, height - self.downaxe, width, height - self.downaxe)
        painter.drawLine(width, 0, width, height - self.downaxe)
        n = width // (2 * self.pc.hscale)
        for i in range(-n, n + 1):
            painter.setPen(QPen(QColor(0, 96, 0), 1, Qt.DotLine))
            x = width // 2 + self.pc.hscale * i
            painter.drawLine(x, 0, x, height - self.downaxe)
            painter.setPen(QPen(Qt.white, 1))
            painter.drawText(x, height, str(i)+' с')
        # выводим цену
        painter.setPen(QPen(QColor(255, 255, 0), 1))
        painter.setFont(self.fontcurprice)
        painter.drawText(10, 20, str(round(self.pc.spotPx, 1)))
        #   выводим справа ячейки с ценой
        painter.setPen(QPen(Qt.white, 1))
        painter.setFont(self.fontcellprice)
        n = height // self.pc.vscale
        price0 = self.pc.current_cellprice - (n * self.pc.exDist // 2 )
        for i in range(n):
            painter.drawText(width + 5, i * self.pc.vscale, str(price0 + i * self.pc.exDist))
        painter.endNativePainting()

class ChangeableLabel(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self,*args, **kwargs)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setStyleSheet("color:rgb(0, 128\, 32); font: bold 24px;")

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        val = int(self.text())
        if ev.button() == Qt.LeftButton:
            self.setText(str(val + 1))
        elif ev.button() == Qt.RightButton:
            self.setText(str(max(val - 1, 0)))

class UiMainWindow(object):
    def __init__(self):
        self.buttonlist = []
        self.numcontbuttonlist = []

    def setupui(self, mainwindow):

        def ex_choose():
            mainwindow.buttonex_clicked(self.sender().objectName())
            for b in self.buttonlist:
                if b == self.sender():
                    b.setIcon(QIcon("./images/buttononlineicon.png"))
                else:
                    b.setIcon(QIcon("./images/buttonofflineicon.png"))

        @pyqtSlot()
        def numcont_choose():
            b = self.sender().objectName()
            value = int(b.replace('pb_numcont_', ''))
            self.numconts = value
            for b in self.numcontbuttonlist:
                if b == self.sender():
                    b.setIcon(QIcon("./images/buttononlineicon.png"))
                else:
                    b.setIcon(QIcon("./images/buttonofflineicon.png"))

        @pyqtSlot()
        def changedist():
            print(self.sender())

        mainwindow.setObjectName("MainWindow")
        mainwindow.resize(1200, 800)
        mainwindow.setWindowTitle("Digitex Liquidity Miner v1.3.8")
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
        self.graphicsview = DisplayField(mainwindow)
        self.splitterh.addWidget(self.graphicsview)
        self.infogridlayoutwidget = QWidget()
        self.infogridlayout = QGridLayout(self.infogridlayoutwidget)
# ------>
        self.ll_balance = QLabel('Баланс:')
        self.ll_balance.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.infogridlayout.addWidget(self.ll_balance, 0, 0, 1, 1)
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
        self.splitterh.addWidget(self.infogridlayoutwidget)
        self.splitterh.setSizes([300, 300])
        self.splitterv.addWidget(self.splitterh)

        self.bottom_hspacer_widget = QWidget()
        self.bottom_hspacer = QHBoxLayout(self.bottom_hspacer_widget)
        self.gb_manual = QGroupBox()
        self.gb_manual.setTitle('Информация')
        self.gl_manual = QGridLayout()
        self.gb_manual.setLayout(self.gl_manual)
        # таймер
        self.ll_worktimer = QLabel('Время работы:')
        self.ll_worktimer.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_manual.addWidget(self.ll_worktimer, 0, 0, 1, 1)
        self.l_worktimer = QLabel('0')
        self.l_worktimer.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_manual.addWidget(self.l_worktimer, 0, 1, 1, 2)

        self.ll_pnltimer = QLabel('Время c прошлой выплаты:')
        self.ll_pnltimer.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_manual.addWidget(self.ll_pnltimer, 0, 3, 1, 2)
        self.l_pnltimer = QLabel('0')
        self.l_pnltimer.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_manual.addWidget(self.l_pnltimer, 0, 5, 1, 2)
        self.ll_fundingcount = QLabel('Выплат:')
        self.ll_fundingcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_manual.addWidget(self.ll_fundingcount, 1, 2, 1, 1)
        self.l_fundingcount = QLabel('0')
        self.l_fundingcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_manual.addWidget(self.l_fundingcount, 1, 3, 1, 1)
        self.ll_mineddgtx = QLabel('Добыто:')
        self.ll_mineddgtx.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_manual.addWidget(self.ll_mineddgtx, 1, 4, 1, 1)
        self.l_mineddgtx = QLabel('0')
        self.l_mineddgtx.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_manual.addWidget(self.l_mineddgtx, 1, 5, 1, 1)
        self.ll_contractcount = QLabel('Сорвано ордеров:')
        self.ll_contractcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_manual.addWidget(self.ll_contractcount, 2, 2, 1, 1)
        self.l_contractcount = QLabel('0')
        self.l_contractcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_manual.addWidget(self.l_contractcount, 2, 3, 1, 1)
        self.ll_contractmined = QLabel('Доход контрактов:')
        self.ll_contractmined.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_manual.addWidget(self.ll_contractmined, 2, 4, 1, 1)
        self.l_contractmined = QLabel('0')
        self.l_contractmined.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_manual.addWidget(self.l_contractmined, 2, 5, 1, 1)
        self.ll_tickcount = QLabel('Всего тиков:')
        self.ll_tickcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_manual.addWidget(self.ll_tickcount, 3, 0, 1, 1)
        self.l_tickcount = QLabel('0')
        self.l_tickcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_manual.addWidget(self.l_tickcount, 3, 1, 1, 1)


        self.bottom_hspacer.addWidget(self.gb_manual)

        self.gb_auto = QGroupBox()
        self.gb_auto.setTitle('Управление')
        self.gl_auto = QGridLayout()
        self.gb_auto.setLayout(self.gl_auto)
        self.bottom_hspacer.addWidget(self.gb_auto)

        self.l_leverage = QLabel('Плечо:')
        self.l_leverage.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_auto.addWidget(self.l_leverage, 0, 0, 1, 1)
        self.buttonLeverage = QPushButton()
        self.buttonLeverage.setObjectName('buttonLeverage')
        self.buttonLeverage.setText('0 x')
        self.buttonLeverage.setToolTip('Плечо')
        self.buttonLeverage.setCursor(Qt.PointingHandCursor)
        self.buttonLeverage.clicked.connect(self.buttonLeverage_clicked)
        self.buttonLeverage.setEnabled(False)
        self.gl_auto.addWidget(self.buttonLeverage, 0, 1, 1, 1)
        self.ll_numconts = QLabel('База ордер:')
        self.ll_numconts.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_auto.addWidget(self.ll_numconts, 0, 3, 1, 1)
        self.l_numconts = ChangeableLabel('1')
        self.gl_auto.addWidget(self.l_numconts, 0, 4, 1, 1)
        self.ll_bonddist = QLabel('Коэф. дистанций:')
        self.ll_bonddist.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_auto.addWidget(self.ll_bonddist, 1, 0, 1, 1)
        self.bonddistwidget = QWidget()
        self.bonddisthlayout = QHBoxLayout()
        self.bonddistwidget.setLayout(self.bonddisthlayout)
        self.ll_bonddist.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.l_dist1 = ChangeableLabel('0')
        self.bonddisthlayout.addWidget(self.l_dist1)
        self.l_dist2 = ChangeableLabel('0')
        self.bonddisthlayout.addWidget(self.l_dist2)
        self.l_dist3 = ChangeableLabel('0')
        self.bonddisthlayout.addWidget(self.l_dist3)
        self.l_dist4 = ChangeableLabel('0')
        self.bonddisthlayout.addWidget(self.l_dist4)
        self.l_dist5 = ChangeableLabel('0')
        self.bonddisthlayout.addWidget(self.l_dist5)
        self.gl_auto.addWidget(self.bonddistwidget, 1, 1, 1, 5)
        self.ll_delayaftermined = QLabel('Задержка после выплаты, сек:')
        self.ll_delayaftermined.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_auto.addWidget(self.ll_delayaftermined, 2, 0, 1, 2)
        self.cb_delayaftermined = QCheckBox()
        self.gl_auto.addWidget(self.cb_delayaftermined, 2, 2, 1, 1)
        self.l_delayaftermined = ChangeableLabel('30')
        self.gl_auto.addWidget(self.l_delayaftermined, 2, 4, 1, 1)
        # кнопка старт
        self.startbutton = QPushButton()
        self.startbutton.setText('СТАРТ')
        self.startbutton.setEnabled(False)
        self.startbutton.clicked.connect(self.startbutton_clicked)
        self.gl_auto.addWidget(self.startbutton, 3, 0, 1, 6)


        self.splitterv.addWidget(self.bottom_hspacer_widget)
        self.splitterv.setSizes([200, 100])
        self.gridLayout.addWidget(self.splitterv, 1, 0, 1, 2)

        self.statusbar = QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)

        cssfile = "./mainWindow.css"
        with open(cssfile, "r") as fh:
            self.setStyleSheet(fh.read())
