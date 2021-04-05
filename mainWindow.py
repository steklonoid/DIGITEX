# модуль главного окна
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QStatusBar, QHBoxLayout, QPushButton, QLabel, QComboBox, QSplitter, QVBoxLayout, QTableView
from PyQt5.QtGui import QIcon, QPainter

class DisplayField(QWidget):
    def __init__(self):
        QWidget.__init__(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        width = painter.viewport().width()  # текущая ширина окна рисования
        height = painter.viewport().height()  # текущая высота окна рисования
        painter.fillRect(0, 0, width, height, Qt.black)  # очищаем окно (черный цвет)

class UiMainWindow(object):
    def setupui(self, mainwindow):
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

        #   верхняя полоска вход не выполнен, аккаунт
        self.hspacerwidgetmenu = QWidget()
        self.hspacerwidgetmenu.setObjectName('hspacerwidgetmenu')
        self.hspacerwidgetmenu.setMaximumHeight(25)
        self.hspacermenu = QHBoxLayout(self.hspacerwidgetmenu)
        self.hspacermenu.setContentsMargins(1, 1, 1, 1)
        self.hspacermenu.setObjectName('hspacermenu')
        self.buttonEnter = QPushButton()
        self.buttonEnter.setObjectName('buttonEnter')
        self.buttonEnter.setText('вход не выполнен')
        self.buttonEnter.setStyleSheet("color:rgb(255, 96, 96); font: bold 10px;border: none")
        self.buttonEnter.setToolTip("Вход")
        self.buttonEnter.setCursor(Qt.PointingHandCursor)
        self.buttonEnter.clicked.connect(self.buttonLogin_clicked)
        self.labelAccount = QLabel('Аккаунт')
        self.labelAccount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.comboBoxAccount = QComboBox()
        self.comboBoxAccount.currentIndexChanged.connect(self.comboBoxAccount_currentIndexChanged)
        self.hspacermenu.addWidget(self.buttonEnter)
        self.hspacermenu.addWidget(self.labelAccount)
        self.hspacermenu.addWidget(self.comboBoxAccount)
        self.gridLayout.addWidget(self.hspacerwidgetmenu, 0, 0, 1, 1)

        #   горизонтальный сплиттер, делящий остальное пространство внизу на две части
        self.splitter = QSplitter(Qt.Horizontal)
        self.graphicsView = DisplayField()
        self.splitter.addWidget(self.graphicsView)
        self.vspacerwidget0 = QWidget()
        self.vspacerwidget0.setObjectName('vspacerwidget0')
        self.vspacer0 = QVBoxLayout(self.vspacerwidget0)
        self.vspacer0.setContentsMargins(0, 0, 0, 0)
        self.vspacer0.setObjectName('vspacer0')
        self.button1 = QPushButton()
        self.button1.setText('Проверка wss')
        self.button1.clicked.connect(self.button1_clicked)
        self.vspacer0.addWidget(self.button1)
        self.splitter.addWidget(self.vspacerwidget0)

        self.splitterv = QSplitter(Qt.Vertical)
        self.tableView1 = QTableView()
        self.tableView1.setObjectName("tableView1")
        self.splitterv.addWidget(self.tableView1)
        self.tableView2 = QTableView()
        self.tableView2.setObjectName("tableView2")
        self.splitterv.addWidget(self.tableView2)
        self.splitter.addWidget(self.splitterv)
        self.splitter.setSizes([200, 100, 700])

        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 1)

        self.statusbar = QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)

        cssfile = "./mainWindow.css"
        with open(cssfile, "r") as fh:
            self.setStyleSheet(fh.read())

        mainwindow.show()