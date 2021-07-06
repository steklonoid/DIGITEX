from PyQt5.QtWidgets import QDialog, QSizePolicy, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox, QPushButton
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtGui import QIcon, QFont
import bcrypt   #pip install bcrypt

import hashlib
import sys
import os
from Crypto.Cipher import AES


class LoginWindow(QDialog):
    userlogined = pyqtSignal()

    def __init__(self, db):
        QDialog.__init__(self)
        self.db = db

    def setupUi(self):
        self.resize(320, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setWindowTitle("Логин пароль")
        self.setWindowIcon(QIcon("./images/siluet.png"))
        self.setSizePolicy(sizePolicy)

        vbox = QVBoxLayout(self)
        labelUser = QLabel('Логин')
        labelUser.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        labelUser.setFont(QFont("Helvetica", 16))
        vbox.addWidget(labelUser)
        self.lineUser = QLineEdit()
        vbox.addWidget(self.lineUser)
        self.lineUser.setFocus()
        labelPassword = QLabel('Пароль')
        labelPassword.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        labelPassword.setFont(QFont("Helvetica", 16))
        vbox.addWidget(labelPassword)
        self.lineP = QLineEdit()
        self.lineP.setEchoMode(QLineEdit.Password)
        vbox.addWidget(self.lineP)
        self.buttonRegister = QPushButton()
        self.buttonRegister.setObjectName('buttonRegister')
        self.buttonRegister.setText('новый пользователь')
        self.buttonRegister.setStyleSheet("color:rgb(96, 96, 255); font: bold 14px;border: none")
        self.buttonRegister.setToolTip("Регистрация нового пользователя")
        self.buttonRegister.setCursor(Qt.PointingHandCursor)
        self.buttonRegister.clicked.connect(self.buttonRegister_clicked)
        vbox.addWidget(self.buttonRegister)
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.buttonOkClicked)
        buttonBox.rejected.connect(self.buttonCancelClicked)
        vbox.addWidget(buttonBox)

        self.q1 = QSqlQuery(self.db)
    @pyqtSlot()

    def buttonRegister_clicked(self):
        rw = RegisterWindow(self.db)
        rw.setupUi()
        rw.exec_()
        self.done(0)


    @pyqtSlot()
    def buttonOkClicked(self):
        flag = True
        if not self.lineUser.text():
            flag = False
        if not self.lineP.text():
            flag = False
        if flag:
            self.q1.prepare('SELECT * FROM users WHERE login=:login')
        self.q1.bindValue(":login", self.lineUser.text())
        self.q1.exec_()
        if self.q1.next():
            if bcrypt.checkpw(self.lineP.text().encode('utf-8'), self.q1.value(1).encode('utf-8')):
                flag = True
            else:
                flag = False
        else:
            flag = False
        if not flag:
            mess = QMessageBox()
            mess.setText('Неверная пара логин/пароль')
            mess.setWindowTitle("Ошибка")
            mess.setWindowIcon(QIcon("./images/wowsign.png"))
            mess.exec()
        else:
            self.user = self.lineUser.text()
            self.psw = self.lineP.text()
            self.userlogined.emit()
            self.done(0)

    @pyqtSlot()
    def buttonCancelClicked(self):
        self.done(0)

class RegisterWindow(QDialog):
    akChanged = pyqtSignal()
    def __init__(self, db, changeak=False, login='', psw=''):
        QDialog.__init__(self)
        self.db = db
        self.flagUser = changeak
        self.flagPassword = changeak
        self.changeak = changeak
        self.login = login
        self.psw = psw

    def setupUi(self):
        self.resize(320, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        if self.changeak:
            self.setWindowTitle("Изменение API KEY")
        else:
            self.setWindowTitle("Регистрация нового пользователя")
        self.setWindowIcon(QIcon("./images/siluet.png"))

        vbox = QVBoxLayout(self)
        labelUser = QLabel('Логин')
        labelUser.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        labelUser.setFont(QFont("Helvetica", 16))
        vbox.addWidget(labelUser)
        #   поле для ввода логина
        self.lineUser = QLineEdit()
        self.lineUser.textEdited.connect(self.lineUsertextEdited)
        self.lineUser.setEnabled(not self.changeak)
        if self.changeak:
            self.lineUser.setText(self.login)
        vbox.addWidget(self.lineUser)
        self.labelUnderUser = QLabel()
        vbox.addWidget(self.labelUnderUser)
        labelPassword = QLabel('Пароль')
        labelPassword.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        labelPassword.setFont(QFont("Helvetica", 16))
        vbox.addWidget(labelPassword)
        #   поле для первого ввода пароля
        self.lineP1 = QLineEdit()
        self.lineP1.setEchoMode(QLineEdit.Password)
        self.lineP1.textEdited.connect(self.linePasswordtextEdited)
        self.lineP1.setEnabled(not self.changeak)
        if self.changeak:
            self.lineP1.setText(self.psw)
        vbox.addWidget(self.lineP1)
        #   поле для второго ввода пароля
        self.lineP2 = QLineEdit()
        self.lineP2.setEchoMode(QLineEdit.Password)
        self.lineP2.textEdited.connect(self.linePasswordtextEdited)
        self.lineP2.setEnabled(not self.changeak)
        vbox.addWidget(self.lineP2)
        self.labelUnderPassword = QLabel()
        vbox.addWidget(self.labelUnderPassword)
        labelAK = QLabel('API Key')
        labelAK.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        labelAK.setFont(QFont("Helvetica", 16))
        vbox.addWidget(labelAK)
        #   поле для ввода APIKEY
        self.lineAK = QLineEdit()
        self.lineAK.setEchoMode(QLineEdit.Password)
        vbox.addWidget(self.lineAK)

        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.buttonOkClicked)
        buttonBox.rejected.connect(self.buttonCancelClicked)
        vbox.addWidget(buttonBox)

        self.q1 = QSqlQuery(self.db)

    @pyqtSlot()
    def buttonOkClicked(self):
        def makeak():
            IV_SIZE = 16  # 128 bit, fixed for the AES algorithm
            KEY_SIZE = 32  # 256 bit meaning AES-256, can also be 128 or 192 bits
            SALT_SIZE = 16  # This size is arbitrary
            psw = self.lineP1.text().encode('utf-8')
            ak = self.lineAK.text().encode('utf-8')
            salt = os.urandom(SALT_SIZE)
            derived = hashlib.pbkdf2_hmac('sha256', psw, salt, 100000,
                                          dklen=IV_SIZE + KEY_SIZE)
            iv = derived[0:IV_SIZE]
            key = derived[IV_SIZE:]
            ak_encrypted = salt + AES.new(key, AES.MODE_CFB, iv).encrypt(ak)
            int_ak_encrypted = int.from_bytes(ak_encrypted, sys.byteorder)
            return int_ak_encrypted

        if self.flagUser and self.flagPassword and len(self.lineAK.text()) != 0:
            if self.changeak:
                self.q1.prepare('UPDATE users SET apikey = :ak WHERE login = :login')
                self.q1.bindValue(":login", self.lineUser.text())
                self.q1.bindValue(":ak", str(makeak()))
                res = self.q1.exec_()
                if res:
                    self.akChanged.emit()
                    self.done(0)
            else:
                self.q1.prepare('INSERT OR IGNORE INTO users (login, psw, apikey) VALUES (:login, :psw, :ak)')
                self.q1.bindValue(":login", self.lineUser.text())
                self.q1.bindValue(":psw", (bcrypt.hashpw(self.lineP1.text().encode('utf-8'), bcrypt.gensalt())).decode('utf-8'))
                self.q1.bindValue(":ak", str(makeak()))
                res = self.q1.exec_()
                if res:
                    mess = QMessageBox()
                    mess.setWindowTitle('* * *')
                    mess.setText('Пользователь зарегистрирован.\nВойдите, используя логин и пароль.')
                    mess.setStyleSheet("color:rgb(0, 96, 128);font: bold 14px;")
                    mess.exec()
                    self.done(0)

    @pyqtSlot()
    def buttonCancelClicked(self):
        self.done(0)

    @pyqtSlot()
    def lineUsertextEdited(self):
        if len(self.lineUser.text()) <= 3:
            self.labelUnderUser.setText('длина логина дожна быть больше 3')
            self.labelUnderUser.setStyleSheet("color:rgb(255, 128, 0);")
            self.flagUser = False
        elif self.checkLoginInDB():
            self.labelUnderUser.setText('логин уже существует')
            self.labelUnderUser.setStyleSheet("color:rgb(128, 0, 0);")
            self.flagUser = False
        else:
            self.labelUnderUser.setText('логин свободен')
            self.labelUnderUser.setStyleSheet("color:rgb(0, 128, 0);")
            self.flagUser = True

    @pyqtSlot()
    def linePasswordtextEdited(self):
        if self.lineP1.text() != self.lineP2.text():
            self.labelUnderPassword.setText('пароли не совпадают')
            self.labelUnderPassword.setStyleSheet("color:rgb(128, 0, 0);")
            self.flagPassword = False
        elif len(self.lineP1.text()) == 0:
            self.labelUnderPassword.setText('введите пароль')
            self.labelUnderPassword.setStyleSheet("color:rgb(255, 128, 0);")
            self.flagPassword = False
        else:
            self.labelUnderPassword.setText('пароль годится')
            self.labelUnderPassword.setStyleSheet("color:rgb(0, 128, 0);")
            self.flagPassword = True

    def checkLoginInDB(self):
        login = self.lineUser.text()
        self.q1.prepare("SELECT * FROM users WHERE login = :login")
        self.q1.bindValue(":login", login)
        self.q1.exec_()
        if self.q1.next():
            return True
        else:
            return False

class ChangeLeverage(QDialog):
    leveragechanged = pyqtSignal()

    def __init__(self):
        QDialog.__init__(self)

    def setupUi(self, leverage):
        self.resize(320, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setWindowTitle("Изменение плеча")
        self.setWindowIcon(QIcon("./images/siluet.png"))
        self.setSizePolicy(sizePolicy)

        vbox = QVBoxLayout(self)
        self.lineedit_leverage = QLineEdit()
        self.lineedit_leverage.setText(str(leverage))
        self.lineedit_leverage.editingFinished.connect(self.lineedit_leverage_editingFinished)
        vbox.addWidget(self.lineedit_leverage)
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.buttonOkClicked)
        buttonBox.rejected.connect(self.buttonCancelClicked)
        vbox.addWidget(buttonBox)

    @pyqtSlot()
    def lineedit_leverage_editingFinished(self):
        v = self.sender().text()
        if not v.isdigit():
            self.lineedit_leverage.setText('5')
        elif int(v) < 1:
            self.lineedit_leverage.setText('1')
        elif int(v) > 100:
            self.lineedit_leverage.setText('100')

    @pyqtSlot()
    def buttonOkClicked(self):
        self.leveragechanged.emit()
        self.done(0)

    @pyqtSlot()
    def buttonCancelClicked(self):
        self.done(0)
