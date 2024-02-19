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


class Moving_const(Enum):
    UP = 90
    DOWN = -90
    LEFT = 180
    RIGHT = 0
    AGAIN_POS = 360


class Const(Enum):
    MONSTERS = 400
    BONUSES = 10
    POWER = 50


class Monsters_moving_const(Enum):
    FIND = 1
    MONSTER_POS = 2


def screen_into_maze(coords, size=32):
    return int(coords[0] / size), int(coords[1] / size)


def maze_into_screen(coords, size=32):
    return coords[0] * size, coords[1] * size


class Object_in_game:
    def __init__(self, area, x, y,
                 size: int, color=(255, 0, 0),
                 circle: bool = False):
        self._size = size
        self._renderer: Game_Change = area
        self.area = area.screen
        self.y = y
        self.x = x
        self._color = color
        self._circle = circle
        self._shape = pygame.Rect(self.x, self.y, size, size)

    def draw(self):
        if self._circle:
            pygame.draw.circle(self.area,
                               self._color,
                               (self.x, self.y),
                               self._size)
        else:
            rect = pygame.Rect(self.x, self.y, self._size, self._size)
            pygame.draw.rect(self.area,
                             self._color,
                             rect,
                             2)

    def tick(self):
        pass

    def shape(self):
        return pygame.Rect(self.x, self.y, self._size, self._size)

    def new_position(self, x, y):
        self.x = x
        self.y = y

    def get_new_position(self):
        return (self.x, self.y)


class Wall(Object_in_game):
    def __init__(self, area, x, y, size: int, color=(0, 0, 255)):
        super().__init__(area, x * size, y * size, size, color)


class Game_Change:
    def __init__(self, width: int, height: int):
        pygame.init()
        pygame.display.set_caption('Pacman')
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.done = False
        self.won = False
        self.object = []
        self.walls = []
        self.coins = []
        self.bonuses = []
        self.monsters = []
        self.pacman: Packman = None
        self.lives = 3
        self.score = 0
        self.score_coins = 10
        self.score_monster = 400
        self.score_bonuses = 50
        self.pacman_active = False
        self.settings_in_time = Monsters_moving_const.MONSTER_POS
        self.switch_settings = pygame.USEREVENT + 1
        self.pacman_end_event = pygame.USEREVENT + 2
        self.pacman_start_event = pygame.USEREVENT + 3
        self.settings = [
            (7, 20),
            (7, 20),
            (5, 20),
            (5, 999999)
        ]
        self._current_phase = 0
        self.flag = False

    def tick(self, in_fps: int):
        BLACK = (0, 0, 0)
        self.handle_mode_switch()
        pygame.time.set_timer(self.pacman_start_event, 200)

        mixer.init()
        ground = mixer.Sound('1-track-1.mp3')
        ground.set_volume(0.7)
        ground.play(-1)
        end = mixer.Sound('2-track-2.mp3')
        end.set_volume(0.7)

        while not self.done:
            for game_object in self.object:
                game_object.tick()
                game_object.draw()
            self.display_text(f"Счёт: {self.score}                           Жизни: {self.lives}")
            if self.pacman is None or self.get_win():
                end.play()
                ground.stop()
                self.restart = pygame.image.load('gameover.jpg')
                self.restart = pygame.transform.scale(self.restart, (970, 900))
                self.screen.blit(self.restart, (0, 0))
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        ground.play(-1)
                        end.stop()
                        if event.button == 1:
                            a = event.pos
                            if a[0] < 970 and a[1] < 900:
                                SIZE_FOR_ALL = 32
                                pacman_game = Game_Control()
                                size = pacman_game.size
                                game_change = Game_Change(size[0] * SIZE_FOR_ALL, size[1] * SIZE_FOR_ALL)

                                for y, row in enumerate(pacman_game.numpy_maze):
                                    for x, column in enumerate(row):
                                        if column == 0:
                                            game_change.add_wall(Wall(game_change, x, y, SIZE_FOR_ALL))

                                for coins_place in pacman_game.cookie_spaces:
                                    translated = maze_into_screen(coins_place)
                                    cookie = Coins(game_change, translated[0] + SIZE_FOR_ALL / 2,
                                                    translated[1] + SIZE_FOR_ALL / 2)
                                    game_change.add_coins(cookie)

                                for bonuses_place in pacman_game.powerup_spaces:
                                    translated = maze_into_screen(bonuses_place)
                                    powerup = Bonuses(game_change, translated[0] + SIZE_FOR_ALL / 2,
                                                      translated[1] + SIZE_FOR_ALL / 2)
                                    game_change.add_bonuses(powerup)

                                for i, ghost_spawn in enumerate(pacman_game.ghost_spawns):
                                    translated = maze_into_screen(ghost_spawn)
                                    monsters = Monsters(game_change, translated[0], translated[1], SIZE_FOR_ALL,
                                                  pacman_game,
                                                  pacman_game.ghost_colors[i % 4])
                                    game_change.add_monsters(monsters)

                                pacman = Packman(game_change, SIZE_FOR_ALL, SIZE_FOR_ALL, SIZE_FOR_ALL)
                                game_change.add_pacman(pacman)
                                game_change.set_current_mode(Monsters_moving_const.FIND)
                                game_change.tick(120)
                                self.lives = 3
            pygame.display.flip()
            self.clock.tick(in_fps)
            self.screen.fill(BLACK)
            self.event_process()