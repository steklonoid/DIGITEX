# модуль главного окна
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QStatusBar, QHBoxLayout, QPushButton, QLabel, QComboBox, QSplitter, QTableView, QAbstractItemView
from PyQt5.QtGui import QIcon, QPainter, QColor, QFont, QPen

class DisplayField(QWidget):
    def __init__(self, pc):
        QWidget.__init__(self)
        self.pc = pc
        self.fontcurprice = QFont("Helvetica", 10, QFont.Bold)

    def paintEvent(self, event):
        painter = QPainter(self)
        width = painter.viewport().width()  # текущая ширина окна рисования
        height = painter.viewport().height()  # текущая высота окна рисования
        painter.fillRect(0, 0, width, height, Qt.black)  # очищаем окно (черный цвет)

        # painter.setPen(QPen(Qt.white, 1))
        # painter.setFont(self.fontcurprice)
        # if self.pc.current_spot_price:
        #     painter.drawText(10, 15, str(self.pc.current_spot_price))

class UiMainWindow(object):
    def __init__(self):
        self.buttonlist = []

    def setupui(self, mainwindow):

        def eq_choose():
            mainwindow.button1_clicked(self.sender().objectName())
            for b in self.buttonlist:
                if b == self.sender():
                    b.setIcon(QIcon("./images/buttononlineicon.png"))
                else:
                    b.setIcon(QIcon("./images/buttonofflineicon.png"))

        mainwindow.setObjectName("MainWindow")
        mainwindow.resize(1200, 800)
        mainwindow.setWindowTitle("Digitex Trading")
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
        self.buttonBTC.clicked.connect(eq_choose)
        self.buttonBTC.setIcon(QIcon("./images/buttonofflineicon.png"))
        self.buttonlist.append(self.buttonBTC)
        self.hspacerinfo.addWidget(self.buttonBTC)
        self.buttonETH = QPushButton()
        self.buttonETH.setObjectName('ETHUSD-PERP')
        self.buttonETH.setText('ETH')
        self.buttonETH.setMinimumHeight(50)
        self.buttonETH.clicked.connect(eq_choose)
        self.buttonETH.setIcon(QIcon("./images/buttonofflineicon.png"))
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
        self.buttonEnter.setToolTip("вход не выполнен")
        self.buttonEnter.setMinimumHeight(50)
        self.buttonEnter.setCursor(Qt.PointingHandCursor)
        self.buttonEnter.clicked.connect(self.buttonLogin_clicked)
        self.labelAccount = QLabel('Аккаунт')
        self.labelAccount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comboBoxAccount = QComboBox()
        self.comboBoxAccount.currentIndexChanged.connect(self.comboBoxAccount_currentIndexChanged)
        self.labelbalance = QLabel()
        self.labelbalance.setFont(QFont("Helvetica", 14, QFont.Bold))
        self.hspacermenu.addWidget(self.buttonEnter)
        self.hspacermenu.addWidget(self.labelAccount)
        self.hspacermenu.addWidget(self.comboBoxAccount)
        self.gridLayout.addWidget(self.hspacerwidgetmenu, 0, 1, 1, 1)

        #   горизонтальный сплиттер, делящий остальное пространство внизу на две части
        self.splitter = QSplitter(Qt.Horizontal)
        # self.graphicsView = DisplayField(self)
        # self.splitter.addWidget(self.graphicsView)
        self.labelprice = QLabel()
        self.splitter.addWidget(self.labelprice)
        self.tableViewStair = QTableView()
        self.tableViewStair.setObjectName("tableViewStair")
        self.tableViewStair.resizeColumnsToContents()
        self.tableViewStair.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableViewStair.setSortingEnabled(True)
        self.tableViewStair.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableViewStair.setCursor(Qt.PointingHandCursor)
        self.tableViewStair.clicked.connect(self.tableViewStairClicked)
        self.splitter.addWidget(self.tableViewStair)

        self.splitterv = QSplitter(Qt.Vertical)
        self.tableView1 = QTableView()
        self.tableView1.setObjectName("tableView1")
        self.splitterv.addWidget(self.tableView1)
        self.tableView2 = QTableView()
        self.tableView2.setObjectName("tableView2")
        self.splitterv.addWidget(self.tableView2)
        self.splitter.addWidget(self.splitterv)
        self.splitter.setSizes([100, 400, 500])

        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 2)

        self.statusbar = QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)

        cssfile = "./mainWindow.css"
        with open(cssfile, "r") as fh:
            self.setStyleSheet(fh.read())

        mainwindow.show()
