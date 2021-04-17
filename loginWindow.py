from PyQt5.QtWidgets import QDialog, QSizePolicy, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox, QComboBox, QPushButton
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtGui import QIcon
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
        self.setWindowTitle("Учетные данные")
        self.setWindowIcon(QIcon("./images/siluet.png"))
        self.setSizePolicy(sizePolicy)

        vbox = QVBoxLayout(self)
        self.buttonRegister = QPushButton()
        self.buttonRegister.setObjectName('buttonRegister')
        self.buttonRegister.setText('регистрация')
        self.buttonRegister.setStyleSheet("color:rgb(255, 96, 96); font: bold 10px;border: none")
        self.buttonRegister.setToolTip("Регистрация нового пользователя")
        self.buttonRegister.setCursor(Qt.PointingHandCursor)
        self.buttonRegister.clicked.connect(self.buttonRegister_clicked)
        vbox.addWidget(self.buttonRegister)
        labelUser = QLabel('Login')
        labelUser.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        vbox.addWidget(labelUser)
        self.lineUser = QLineEdit()
        vbox.addWidget(self.lineUser)
        self.lineUser.setFocus()
        labelPassword = QLabel('Password')
        labelPassword.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        vbox.addWidget(labelPassword)
        self.lineP = QLineEdit()
        self.lineP.setEchoMode(QLineEdit.Password)
        vbox.addWidget(self.lineP)
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
    def __init__(self, db):
        QDialog.__init__(self)
        self.db = db
        self.flagUser = False
        self.flagPassword = False

    def setupUi(self):
        self.resize(320, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        vbox = QVBoxLayout(self)
        labelUser = QLabel('User')
        vbox.addWidget(labelUser)
        self.lineUser = QLineEdit()
        self.lineUser.textEdited.connect(self.lineUsertextEdited)
        vbox.addWidget(self.lineUser)
        self.labelUnderUser = QLabel('введите логин')
        vbox.addWidget(self.labelUnderUser)
        labelPassword = QLabel('Password')
        vbox.addWidget(labelPassword)
        self.lineP1 = QLineEdit()
        self.lineP1.setEchoMode(QLineEdit.Password)
        self.lineP1.textEdited.connect(self.linePasswordtextEdited)
        vbox.addWidget(self.lineP1)
        self.lineP2 = QLineEdit()
        self.lineP2.setEchoMode(QLineEdit.Password)
        self.lineP2.textEdited.connect(self.linePasswordtextEdited)
        vbox.addWidget(self.lineP2)
        self.labelUnderPassword = QLabel('введите пароль')
        vbox.addWidget(self.labelUnderPassword)
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.buttonOkClicked)
        buttonBox.rejected.connect(self.buttonCancelClicked)
        vbox.addWidget(buttonBox)

        self.q1 = QSqlQuery(self.db)

    @pyqtSlot()
    def buttonOkClicked(self):
        if self.flagUser and self.flagPassword:
            self.q1.prepare('INSERT OR IGNORE INTO users (login, psw) VALUES (:login, :psw)')
            self.q1.bindValue(":login", self.lineUser.text())
            self.q1.bindValue(":psw", (bcrypt.hashpw(self.lineP1.text().encode('utf-8'), bcrypt.gensalt())).decode('utf-8'))
            res = self.q1.exec_()
            if res:
                mess = QMessageBox()
                mess.setText('Пользователь создан успешно')
                mess.exec()
                self.done(0)

    @pyqtSlot()
    def buttonCancelClicked(self):
        self.done(0)

    @pyqtSlot()
    def lineUsertextEdited(self):
        if len(self.lineUser.text()) == 0:
            self.labelUnderUser.setText('введите логин')
            self.flagUser = False
        elif len(self.lineUser.text()) <= 3:
            self.labelUnderUser.setText('длина логина дожна быть больше 3')
            self.flagUser = False
        elif self.checkLoginInDB():
            self.labelUnderUser.setText('логин уже существует')
            self.flagUser = False
        else:
            self.labelUnderUser.setText('логин свободен')
            self.flagUser = True

    @pyqtSlot()
    def linePasswordtextEdited(self):
        if len(self.lineP1.text()) != len(self.lineP2.text()):
            self.labelUnderPassword.setText('пароли не совпадают')
            self.flagPassword = False
        elif len(self.lineP1.text()) == 0:
            self.labelUnderPassword.setText('введите пароль')
            self.flagPassword = False
        else:
            self.labelUnderPassword.setText('пароль годится')
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

class AddAccount(QDialog):
    def __init__(self, p):
        QDialog.__init__(self)
        self.p = p
        self.db = p.db
        self.user = p.user
        self.psw = p.psw

    def setupUi(self):
        self.resize(320, 200)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        vbox = QVBoxLayout(self)
        self.labelNameAccount = QLabel('Название аккаунта')
        vbox.addWidget(self.labelNameAccount)
        self.lineEditNameAccount = QLineEdit()
        vbox.addWidget(self.lineEditNameAccount)
        self.labelAK = QLabel('API KEY')
        vbox.addWidget(self.labelAK)
        self.lineEditAK = QLineEdit()
        self.lineEditAK.setEchoMode(QLineEdit.Password)
        vbox.addWidget(self.lineEditAK)
        buttonBox = QDialogButtonBox()
        buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.buttonOkClicked)
        buttonBox.rejected.connect(self.buttonCancelClicked)
        vbox.addWidget(buttonBox)

    @pyqtSlot()
    def buttonOkClicked(self):
        IV_SIZE = 16  # 128 bit, fixed for the AES algorithm
        KEY_SIZE = 32  # 256 bit meaning AES-256, can also be 128 or 192 bits
        SALT_SIZE = 16  # This size is arbitrary
        psw = self.psw.encode('utf-8')

        ak = self.lineEditAK.text().encode('utf-8')
        salt = os.urandom(SALT_SIZE)
        derived = hashlib.pbkdf2_hmac('sha256', psw, salt, 100000,
                                      dklen=IV_SIZE + KEY_SIZE)
        iv = derived[0:IV_SIZE]
        key = derived[IV_SIZE:]
        ak_encrypted = salt + AES.new(key, AES.MODE_CFB, iv).encrypt(ak)
        int_ak_encrypted = int.from_bytes(ak_encrypted, sys.byteorder)
        q1 = QSqlQuery(self.db)

        q1.prepare('INSERT OR IGNORE INTO accounts (userlogin, accname, apikey) VALUES (:userlogin, :accname, :apikey)')
        q1.bindValue(":userlogin", self.user)
        q1.bindValue(":accname", self.lineEditNameAccount.text())
        q1.bindValue(":apikey", str(int_ak_encrypted))
        q1.exec_()
        self.accountadded.emit()
        self.done(0)

    @pyqtSlot()
    def buttonCancelClicked(self):
        self.done(0)

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
