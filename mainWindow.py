# модуль главного окна
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QGridLayout, QStatusBar, QHBoxLayout, QPushButton, QLabel, QComboBox, QSplitter, QTableView, QLineEdit, QCheckBox
from PyQt5.QtGui import QIcon, QFont

class UiMainWindow(object):
    def __init__(self):
        self.buttonlist = []

    def setupui(self, mainwindow):

        def ex_choose():
            mainwindow.button1_clicked(self.sender().objectName())
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
                self.current_numconts = 1
            elif int(v) < 1:
                self.sender().setText('1')
                self.current_numconts = 1
            elif int(v) > 100:
                self.sender().setText('100')
                self.current_numconts = 100
            else:
                self.current_numconts = int(v)

        @pyqtSlot()
        def le_orderdist_editingFinished():
            v = self.sender().text()
            if not v.isdigit():
                self.sender().setText('10')
                self.current_orderdist = 10
            elif int(v) < 1:
                self.sender().setText('1')
                self.current_orderdist = 1
            else:
                self.current_orderdist = int(v)

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
        self.buttonBTC.clicked.emit()
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
        self.tableViewOrders = QTableView()
        self.splitterv.addWidget(self.tableViewOrders)
        self.control_gridLayout_widget = QWidget()
        self.control_gridLayout = QGridLayout(self.control_gridLayout_widget)

        self.buttonLeverage = QPushButton()
        self.buttonLeverage.setObjectName('buttonLeverage')
        self.buttonLeverage.setText('0 x')
        self.buttonLeverage.setToolTip('Плечо')
        self.buttonLeverage.setCursor(Qt.PointingHandCursor)
        self.buttonLeverage.clicked.connect(self.buttonLeverage_clicked)
        self.buttonLeverage.setEnabled(False)
        self.control_gridLayout.addWidget(self.buttonLeverage, 0, 0, 1, 1)

        # расстояния открытия / закрытия
        self.openclosedistspacerwidget = QWidget()
        self.openclosedistspacer = QHBoxLayout(self.openclosedistspacerwidget)
        self.le_numcont = QLineEdit()
        self.le_numcont.setText('1')
        self.le_numcont.editingFinished.connect(le_numcont_editingFinished)
        self.openclosedistspacer.addWidget(QLabel('К-во контр.'))
        self.openclosedistspacer.addWidget(self.le_numcont)

        self.le_orderdist = QLineEdit()
        self.le_orderdist.setText('10')
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
        self.gridLayout.addWidget(self.splitterv, 1, 0, 1, 2)

        self.statusbar = QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)

        cssfile = "./mainWindow.css"
        with open(cssfile, "r") as fh:
            self.setStyleSheet(fh.read())
