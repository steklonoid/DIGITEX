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
        QLabel.__init__(self, *args, **kwargs)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setStyleSheet("color:rgb(0, 128, 32); font: bold 24px;")
        self.step = 1
        self.lastx = 0
        self.flMove = False
        self.integ = True

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        self.lastx = ev.x()

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        if not self.flMove:
            if ev.button() == Qt.LeftButton:
                if self.integ:
                    val = int(self.text()) + self.step
                else:
                    val = round(float(self.text()) + self.step, 2)
            elif ev.button() == Qt.RightButton:
                if self.integ:
                    val = int(self.text()) - self.step
                else:
                    val = round(float(self.text()) - self.step, 2)
            self.setText(str(val))
        self.flMove = False

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        self.flMove = True
        dx = ev.x() - self.lastx
        if self.integ:
            val = int(self.text()) + self.step * dx
        else:
            val = round(float(self.text()) + self.step * dx, 2)
        self.setText(str(max(val, 0)))
        self.lastx = ev.x()

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

        mainwindow.setObjectName("MainWindow")
        mainwindow.resize(1200, 800)
        mainwindow.setWindowTitle("Digitex Liquidity Miner v1.3.13")
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
        self.gb_marketsituation = QGroupBox()
        self.gb_marketsituation.setTitle('Ситуация на рынке: ')
        self.gl_marketsituation = QGridLayout()
        self.gb_marketsituation.setLayout(self.gl_marketsituation)
        self.ll_tickcount = QLabel('Всего тиков:')
        self.ll_tickcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_marketsituation.addWidget(self.ll_tickcount, 0, 0, 1, 1)
        self.l_tickcount = QLabel('0')
        self.l_tickcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_marketsituation.addWidget(self.l_tickcount, 0, 1, 1, 1)
        self.ll_midvol = QLabel('Волатильность рынка, цена/тик:')
        self.ll_midvol.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_marketsituation.addWidget(self.ll_midvol, 1, 0, 1, 1)
        self.l_midvol = QLabel('0')
        self.l_midvol.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_marketsituation.addWidget(self.l_midvol, 1, 1, 1, 1)
        self.ll_midvar = QLabel('Дисперсия рынка:')
        self.ll_midvar.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_marketsituation.addWidget(self.ll_midvar, 2, 0, 1, 1)
        self.l_midvar = QLabel('0')
        self.l_midvar.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_marketsituation.addWidget(self.l_midvar, 2, 1, 1, 1)

        self.splitterh.addWidget(self.gb_marketsituation)
        self.splitterh.setSizes([300, 300])
        self.splitterv.addWidget(self.splitterh)

        self.bottom_hspacer_widget = QWidget()
        self.bottom_hspacer = QHBoxLayout(self.bottom_hspacer_widget)
        self.gb_mininginfo = QGroupBox()
        self.gb_mininginfo.setTitle('Информация о майнинге')
        self.gl_mininginfo = QGridLayout()
        self.gb_mininginfo.setLayout(self.gl_mininginfo)

        self.ll_balance = QLabel('Баланс:')
        self.ll_balance.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_mininginfo.addWidget(self.ll_balance, 4, 0, 1, 1)
        self.l_balance_dgtx = QLabel('0')
        self.l_balance_dgtx.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_balance_dgtx.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.gl_mininginfo.addWidget(self.l_balance_dgtx, 4, 1, 1, 1)
        self.l_dgtx = QLabel('DGTX')
        self.l_dgtx.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_mininginfo.addWidget(self.l_dgtx, 4, 2, 1, 1)
        self.l_balance_usd = QLabel('0')
        self.l_balance_usd.setStyleSheet("color:rgb(0, 0, 96); font: bold 16px;")
        self.l_balance_usd.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.gl_mininginfo.addWidget(self.l_balance_usd, 4, 3, 1, 1)
        self.l_usd = QLabel('USD')
        self.l_usd.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_mininginfo.addWidget(self.l_usd, 4, 4, 1, 1)
        self.ll_pnl = QLabel('PnL')
        self.ll_pnl.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_mininginfo.addWidget(self.ll_pnl, 5, 0, 1, 1)
        self.l_pnl = QLabel('0')
        self.l_pnl.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px;")
        self.l_pnl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.gl_mininginfo.addWidget(self.l_pnl, 5, 1, 1, 1)

        # таймер
        self.ll_worktimer = QLabel('Время работы:')
        self.ll_worktimer.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_mininginfo.addWidget(self.ll_worktimer, 0, 0, 1, 1)
        self.l_worktimer = QLabel('0')
        self.l_worktimer.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_mininginfo.addWidget(self.l_worktimer, 0, 1, 1, 2)

        self.ll_pnltimer = QLabel('Время c прошлой выплаты:')
        self.ll_pnltimer.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_mininginfo.addWidget(self.ll_pnltimer, 0, 3, 1, 2)
        self.l_pnltimer = QLabel('0')
        self.l_pnltimer.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_mininginfo.addWidget(self.l_pnltimer, 0, 5, 1, 2)
        self.ll_fundingcount = QLabel('Выплат:')
        self.ll_fundingcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_mininginfo.addWidget(self.ll_fundingcount, 1, 2, 1, 1)
        self.l_fundingcount = QLabel('0')
        self.l_fundingcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_mininginfo.addWidget(self.l_fundingcount, 1, 3, 1, 1)
        self.ll_mineddgtx = QLabel('Добыто:')
        self.ll_mineddgtx.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_mininginfo.addWidget(self.ll_mineddgtx, 1, 4, 1, 1)
        self.l_fundingmined = QLabel('0')
        self.l_fundingmined.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_mininginfo.addWidget(self.l_fundingmined, 1, 5, 1, 1)
        self.ll_contractcount = QLabel('Сорвано ордеров:')
        self.ll_contractcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_mininginfo.addWidget(self.ll_contractcount, 2, 2, 1, 1)
        self.l_contractcount = QLabel('0')
        self.l_contractcount.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_mininginfo.addWidget(self.l_contractcount, 2, 3, 1, 1)
        self.ll_contractmined = QLabel('Доход контрактов:')
        self.ll_contractmined.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_mininginfo.addWidget(self.ll_contractmined, 2, 4, 1, 1)
        self.l_contractmined = QLabel('0')
        self.l_contractmined.setStyleSheet("color:rgb(0, 0, 32); font: bold 24px")
        self.gl_mininginfo.addWidget(self.l_contractmined, 2, 5, 1, 1)

        self.bottom_hspacer.addWidget(self.gb_mininginfo)
        self.gb_miningcontrol = QGroupBox()
        self.gb_miningcontrol.setTitle('Управление майнингом')
        self.gl_miningcontrol = QGridLayout()
        self.gb_miningcontrol.setLayout(self.gl_miningcontrol)
        self.bottom_hspacer.addWidget(self.gb_miningcontrol)

        self.l_leverage = QLabel('Плечо:')
        self.l_leverage.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_miningcontrol.addWidget(self.l_leverage, 0, 0, 1, 1)
        self.buttonLeverage = QPushButton()
        self.buttonLeverage.setObjectName('buttonLeverage')
        self.buttonLeverage.setText('0 x')
        self.buttonLeverage.setToolTip('Плечо')
        self.buttonLeverage.setCursor(Qt.PointingHandCursor)
        self.buttonLeverage.clicked.connect(self.buttonLeverage_clicked)
        self.buttonLeverage.setEnabled(False)
        self.gl_miningcontrol.addWidget(self.buttonLeverage, 0, 1, 1, 1)
        self.ll_numconts = QLabel('База ордер:')
        self.ll_numconts.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_miningcontrol.addWidget(self.ll_numconts, 0, 3, 1, 1)
        self.l_numconts = ChangeableLabel('1')
        self.gl_miningcontrol.addWidget(self.l_numconts, 0, 4, 1, 1)
        self.ll_bonddist = QLabel('Коэф. дистанций:')
        self.ll_bonddist.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_miningcontrol.addWidget(self.ll_bonddist, 1, 0, 1, 1)
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
        self.gl_miningcontrol.addWidget(self.bonddistwidget, 1, 1, 1, 5)
        self.ll_delayaftermined = QLabel('Задержка после выплаты, сек:')
        self.ll_delayaftermined.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_miningcontrol.addWidget(self.ll_delayaftermined, 2, 0, 1, 2)
        self.cb_delayaftermined = QCheckBox()
        self.gl_miningcontrol.addWidget(self.cb_delayaftermined, 2, 2, 1, 1)
        self.l_delayaftermined = ChangeableLabel('30')
        self.l_delayaftermined.step = 5
        self.gl_miningcontrol.addWidget(self.l_delayaftermined, 2, 4, 1, 1)

        self.ll_losslimit = QLabel('Ограничение потерь: ')
        self.ll_losslimit.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_miningcontrol.addWidget(self.ll_losslimit, 3, 0, 1, 1)
        self.cb_losslimit = QCheckBox()
        self.gl_miningcontrol.addWidget(self.cb_losslimit, 3, 1, 1, 1)
        self.ll_losslimit_b = QLabel('балансом')
        self.ll_losslimit_b.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        self.gl_miningcontrol.addWidget(self.ll_losslimit_b, 3, 2, 1, 1)
        self.l_losslimit_b = ChangeableLabel('0')
        self.l_losslimit_b.step = 10
        self.gl_miningcontrol.addWidget(self.l_losslimit_b, 3, 3, 1, 1)
        # self.ll_losslimit_s = QLabel('суммой')
        # self.ll_losslimit_s.setStyleSheet("color:rgb(0, 0, 32); font: bold 12px")
        # self.gl_miningcontrol.addWidget(self.ll_losslimit_s, 3, 4, 1, 1)
        # self.l_losslimit_s = ChangeableLabel('100')
        # self.gl_miningcontrol.addWidget(self.l_losslimit_s, 3, 5, 1, 1)

        self.ll_midvollimit = QLabel('Ограничение по волатильности:')
        self.ll_midvollimit.setStyleSheet("color:rgb(0, 0, 32); font: bold 16px")
        self.gl_miningcontrol.addWidget(self.ll_midvollimit, 4, 0, 1, 3)
        self.cb_midvollimit = QCheckBox()
        self.gl_miningcontrol.addWidget(self.cb_midvollimit, 4, 3, 1, 1)
        self.l_midvollimit = ChangeableLabel('0.5')
        self.l_midvollimit.step = 0.01
        self.l_midvollimit.integ = False
        self.gl_miningcontrol.addWidget(self.l_midvollimit, 4, 4, 1, 1)

        # кнопка старт
        self.startbutton = QPushButton()
        self.startbutton.setText('СТАРТ')
        self.startbutton.setEnabled(False)
        self.startbutton.clicked.connect(self.startbutton_clicked)
        self.gl_miningcontrol.addWidget(self.startbutton, 5, 0, 1, 6)


        self.splitterv.addWidget(self.bottom_hspacer_widget)
        self.splitterv.setSizes([200, 100])
        self.gridLayout.addWidget(self.splitterv, 1, 0, 1, 2)

        self.statusbar = QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)

        cssfile = "./mainWindow.css"
        with open(cssfile, "r") as fh:
            self.setStyleSheet(fh.read())
