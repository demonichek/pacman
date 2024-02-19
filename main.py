import random
import sqlite3
import sys
from enum import Enum

import numpy as np
import pygame
import tcod
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from PyQt5.uic import loadUi
from pygame import mixer


class Access(QDialog):
    def __init__(self):
        super(Access, self).__init__()
        loadUi("vhod.ui", self)
        self.setWindowTitle('Access')
        self.access.clicked.connect(self.login_function)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.log_in.clicked.connect(self.go_to_create)

    def login_function(self):
        email = self.email.text()
        con = sqlite3.connect('logins.db')
        cur = con.cursor()
        all_logins = [i[0] for i in cur.execute("""SELECT  login_name FROM log_in""").fetchall()]
        con.commit()
        con.close()
        if email in all_logins:
            password = self.password.text()
            con = sqlite3.connect('logins.db')
            cur = con.cursor()
            password2 = cur.execute("""SELECT password FROM log_in WHERE login_name == (?)""",
                                    (email,)).fetchone()[0]
            con.commit()
            con.close()
            if password == password2:
                self.close()
                QApplication.quit()

            else:
                message = QMessageBox()
                message.setWindowTitle('password_error')
                message.setText('Неверный пароль')
                message.setIcon(QMessageBox.Critical)
                message.setStandardButtons(QMessageBox.Retry)
                message.buttonClicked.connect(self.remove_password)

                res = message.exec_()
        else:
            message = QMessageBox()
            message.setWindowTitle('login_error')
            message.setText('Несуществующий логин')
            message.setIcon(QMessageBox.Warning)
            message.setStandardButtons(QMessageBox.Ok)
            message.setInformativeText('Нажмите на кнопку "Зарегистрироваться",'
                                       ' чтобы создать аккаунт.')
            message.buttonClicked.connect(self.remove_login)

            res = message.exec_()

    def go_to_create(self):
        create_acc = Login()
        widget.addWidget(create_acc)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def remove_login(self):
        self.email.setText(None)
        self.password.setText(None)

    def remove_password(self):
        self.password.setText(None)


class Login(QDialog):

    def __init__(self):
        super(Login, self).__init__()
        loadUi("register.ui", self)
        self.setWindowTitle('Log in')
        self.create_acc.clicked.connect(self.create_acc_function)
        self.password1.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password2.setEchoMode(QtWidgets.QLineEdit.Password)

    def create_acc_function(self):
        email = self.email.text()
        cor_email = self.incorrect_login(email)
        if not cor_email:
            message = QMessageBox()
            message.setWindowTitle('login_error')
            message.setText('Этот логин некорректен')
            message.setIcon(QMessageBox.Critical)
            message.setStandardButtons(QMessageBox.Retry)
            message.setInformativeText('Логин должен состоять из минимум 6 символов.')
            message.buttonClicked.connect(self.new_login)

            res = message.exec_()
        else:
            con = sqlite3.connect('logins.db')
            cur = con.cursor()
            all_logins = [i[0] for i in cur.execute("""SELECT  login_name FROM log_in""").fetchall()]
            con.commit()
            con.close()
            if email in all_logins:
                message = QMessageBox()
                message.setWindowTitle('login_error')
                message.setText('Этот логин уже использован')
                message.setIcon(QMessageBox.Critical)
                message.setStandardButtons(QMessageBox.Retry)
                message.buttonClicked.connect(self.new_login)

                res = message.exec_()
            else:
                if self.password1.text() == self.password2.text():

                    password = self.password1.text()
                    pas_corr = self.incorrect_password(password)
                    if pas_corr != 'OK':
                        message = QMessageBox()
                        message.setWindowTitle('password_error')
                        message.setText('Этот пароль некорректен')
                        message.setIcon(QMessageBox.Critical)
                        message.setStandardButtons(QMessageBox.Retry)
                        message.buttonClicked.connect(self.diff_passwords)
                        message.setInformativeText(pas_corr)
                        res = message.exec_()
                    else:
                        #  Наконец регистрируемся и заходим.
                        con = sqlite3.connect('logins.db')
                        cur = con.cursor()
                        cur.execute('''INSERT INTO log_in (login_name, password) VALUES (?, ?)''',
                                    (str(email), str(password)))
                        con.commit()
                        con.close()
                        login = Access()
                        widget.addWidget(login)
                        widget.setCurrentIndex(widget.currentIndex() + 1)
                else:
                    message = QMessageBox()
                    message.setWindowTitle('password_error')
                    message.setText('Пароли не совпадают, попробуйте еще раз!')
                    message.setIcon(QMessageBox.Critical)
                    message.setStandardButtons(QMessageBox.Retry)
                    message.buttonClicked.connect(self.diff_passwords)

                    res = message.exec_()

    def diff_passwords(self, event):
        self.password2.setText(None)
        self.password1.setText(None)

    def new_login(self):
        self.email.setText(None)
        self.password2.setText(None)
        self.password1.setText(None)

    def incorrect_password(self, password):
        password = [str(i) for i in password]
        count_letters = [i for i in password if ((97 <= ord(i) <= 122)
                                                 or (65 <= ord(i) <= 90))]
        count_numbers = [i for i in password if
                         48 <= ord(i) <= 57]
        if len(password) < 8:
            return 'В пароле должно быть 8 или более символов.'
        elif len(count_letters) < 5:
            return 'В пароле должно быть 5 или более букв.'
        elif len(count_numbers) < 3:
            return 'В пароле должно быть 3 или более цифр.'
        else:
            return 'OK'

    def incorrect_login(self, email):
        email2 = email
        email2.strip()
        if len(email2) < 6:
            return False
        return True

