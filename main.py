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
        global flag
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
                flag = True
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
                if self.pacman is None:
                    self.restart = pygame.image.load('gameover.jpg')
                    self.restart = pygame.transform.scale(self.restart, (970, 900))
                    self.screen.blit(self.restart, (0, 0))
                elif self.get_win():
                    self.restart = pygame.image.load('youwin.jpg')
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

    def handle_mode_switch(self):
        current_phase_timings = self.settings[self._current_phase]
        scatter_timing = current_phase_timings[0]
        chase_timing = current_phase_timings[1]

        if self.settings_in_time == Monsters_moving_const.FIND:
            self._current_phase += 1
            self.set_current_mode(Monsters_moving_const.MONSTER_POS)
        else:
            self.set_current_mode(Monsters_moving_const.FIND)

        used_timing = scatter_timing if self.settings_in_time == Monsters_moving_const.MONSTER_POS else chase_timing
        pygame.time.set_timer(self.switch_settings, used_timing * 1000)

    def start_pacman(self):
        pygame.time.set_timer(self.pacman_end_event, 15000)  # 15s

    def add_game_object(self, obj: Object_in_game):
        self.object.append(obj)

    def add_coins(self, obj: Object_in_game):
        self.object.append(obj)
        self.coins.append(obj)

    def add_monsters(self, obj: Object_in_game):
        self.object.append(obj)
        self.monsters.append(obj)

    def add_bonuses(self, obj: Object_in_game):
        self.object.append(obj)
        self.bonuses.append(obj)

    def pacman_move(self):
        self.pacman_active = True
        self.set_current_mode(Monsters_moving_const.MONSTER_POS)
        self.start_pacman()

    def set_win(self):
        self.won = True

    def get_win(self):
        return self.won

    def add_score(self, score: Const):
        self.score += score.value

    def get_hero_position(self):
        return self.pacman.get_new_position() if self.pacman != None else (0, 0)

    def set_current_mode(self, setting: Monsters_moving_const):
        self.settings_in_time = setting

    def get_current_mode(self):
        return self.settings_in_time

    def end_game(self):
        if self.pacman in self.object:
            self.object.remove(self.pacman)
        self.pacman = None

    def kill_pacman(self):
        self.lives -= 1
        self.pacman.new_position(32, 32)
        self.pacman.set_direction(Moving_const.AGAIN_POS)
        if self.lives == 0: self.end_game()

    def display_text(self, text, in_position=(200, 0), in_size=30):
        font = pygame.font.SysFont('Arial', in_size)
        text_surface = font.render(text, False, (255, 255, 255))
        self.screen.blit(text_surface, in_position)

    def pacman_in_move(self):
        return self.pacman_active

    def add_wall(self, obj: Wall):
        self.add_game_object(obj)
        self.walls.append(obj)

    def get_walls(self):
        return self.walls

    def get_coins(self):
        return self.coins

    def get_monsters(self):
        return self.monsters

    def get_bonuses(self):
        return self.bonuses

    def get_game_objects(self):
        return self.object

    def add_pacman(self, pacman):
        self.add_game_object(pacman)
        self.pacman = pacman

    def event_process(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True

            if event.type == self.switch_settings:
                self.handle_mode_switch()

            if event.type == self.pacman_end_event:
                self.pacman_active = False

            if event.type == self.pacman_start_event:
                if self.pacman is None: break
                self.pacman.mouth_open = not self.pacman.mouth_open

        pressed = pygame.key.get_pressed()
        if self.pacman is None: return
        if pressed[pygame.K_UP]:
            self.pacman.set_direction(Moving_const.UP)
        elif pressed[pygame.K_LEFT]:
            self.pacman.set_direction(Moving_const.LEFT)
        elif pressed[pygame.K_DOWN]:
            self.pacman.set_direction(Moving_const.DOWN)
        elif pressed[pygame.K_RIGHT]:
            self.pacman.set_direction(Moving_const.RIGHT)

class MovableObject(Object_in_game):
    def __init__(self, in_surface, x, y, in_size: int, in_color=(255, 0, 0), is_circle: bool = False):
        super().__init__(in_surface, x, y, in_size, in_color, is_circle)
        self.current_direction = Moving_const.AGAIN_POS
        self.direction_buffer = Moving_const.AGAIN_POS
        self.last_working_direction = Moving_const.AGAIN_POS
        self.location_queue = []
        self.next_target = None
        # self.image = pygame.image.load('ghost.png')

    def get_next_location(self):
        return None if len(self.location_queue) == 0 else self.location_queue.pop(0)

    def set_direction(self, in_direction):
        self.current_direction = in_direction
        self.direction_buffer = in_direction

    def collides_with_wall(self, in_position):
        collision_rect = pygame.Rect(in_position[0], in_position[1], self._size, self._size)
        collides = False
        walls = self._renderer.get_walls()
        for wall in walls:
            collides = collision_rect.colliderect(wall.shape())
            if collides: break
        return collides

    def check_collision_in_direction(self, in_direction: Moving_const):
        desired_position = (0, 0)
        if in_direction == Moving_const.AGAIN_POS: return False, desired_position
        if in_direction == Moving_const.UP:
            desired_position = (self.x, self.y - 1)
        elif in_direction == Moving_const.DOWN:
            desired_position = (self.x, self.y + 1)
        elif in_direction == Moving_const.LEFT:
            desired_position = (self.x - 1, self.y)
        elif in_direction == Moving_const.RIGHT:
            desired_position = (self.x + 1, self.y)

        return self.collides_with_wall(desired_position), desired_position

    def automatic_move(self, in_direction: Moving_const):
        pass

    def tick(self):
        self.reached_target()
        self.automatic_move(self.current_direction)

    def reached_target(self):
        pass

    def draw(self):
        self.image = pygame.transform.scale(self.image, (32, 32))
        self.area.blit(self.image, self.shape())

class Packman(MovableObject):
    def __init__(self, in_surface, x, y, in_size: int):
        super().__init__(in_surface, x, y, in_size, (255, 255, 0), False)
        self.last_non_colliding_position = (0, 0)
        self.open = pygame.image.load("pacman_rot_otkrit.png")
        self.closed = pygame.image.load("man.png")
        self.image = self.open
        self.mouth_open = True

    def tick(self):
        if self.x < 0:
            self.x = self._renderer.width

        if self.x > self._renderer.width:
            self.x = 0

        if self.y < 0:
            self.y = self._renderer.height

        if self.y > self._renderer.height:
            self.y = 0

        self.last_non_colliding_position = self.get_new_position()

        if self.check_collision_in_direction(self.direction_buffer)[0]:
            self.automatic_move(self.current_direction)
        else:
            self.automatic_move(self.direction_buffer)
            self.current_direction = self.direction_buffer

        if self.collides_with_wall((self.x, self.y)):
            self.new_position(self.last_non_colliding_position[0], self.last_non_colliding_position[1])

        self.handle_cookie_pickup()
        self.handle_ghosts()

    def automatic_move(self, in_direction: Moving_const):
        collision_result = self.check_collision_in_direction(in_direction)

        desired_position_collides = collision_result[0]
        if not desired_position_collides:
            self.last_working_direction = self.current_direction
            desired_position = collision_result[1]
            self.new_position(desired_position[0], desired_position[1])
        else:
            self.current_direction = self.last_working_direction

    def handle_cookie_pickup(self):
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        cookies = self._renderer.get_coins()
        powerups = self._renderer.get_bonuses()
        game_objects = self._renderer.get_game_objects()
        cookie_to_remove = None
        for cookie in cookies:
            collides = collision_rect.colliderect(cookie.shape())
            if collides and cookie in game_objects:
                game_objects.remove(cookie)
                self._renderer.add_score(Const.BONUSES)
                cookie_to_remove = cookie

        if cookie_to_remove is not None:
            cookies.remove(cookie_to_remove)

        if len(self._renderer.get_coins()) == 0:
            self._renderer.set_win()

        for powerup in powerups:
            collides = collision_rect.colliderect(powerup.shape())
            if collides and powerup in game_objects:
                if not self._renderer.pacman_in_move():
                    game_objects.remove(powerup)
                    self._renderer.add_score(Const.POWER)
                    self._renderer.pacman_move()

    def handle_ghosts(self):
        collision_rect = pygame.Rect(self.x, self.y, self._size, self._size)
        ghosts = self._renderer.get_monsters()
        game_objects = self._renderer.get_game_objects()
        for ghost in ghosts:
            collides = collision_rect.colliderect(ghost.shape())
            if collides and ghost in game_objects:
                if self._renderer.pacman_in_move():
                    game_objects.remove(ghost)
                    self._renderer.add_score(Const.MONSTERS)
                else:
                    if not self._renderer.get_win():
                        self._renderer.kill_pacman()

    def draw(self):
        half_size = self._size / 2
        self.image = self.open if self.mouth_open else self.closed
        if self.current_direction.value == 180:
            self.image = pygame.transform.flip(self.image, True, False)
        else:
            self.image = pygame.transform.rotate(self.image, self.current_direction.value)
        super(Packman, self).draw()


class Monsters(MovableObject):
    def __init__(self, in_surface, x, y, in_size: int, in_game_controller, sprite_path="ghost_fright.png"):
        super().__init__(in_surface, x, y, in_size)
        self.game_controller = in_game_controller
        self.sprite_normal = pygame.image.load(sprite_path)
        self.sprite_fright = pygame.image.load("ghost_fright.png")

    def reached_target(self):
        if (self.x, self.y) == self.next_target:
            self.next_target = self.get_next_location()
        self.current_direction = self.calculate_direction_to_next_target()

    def set_new_path(self, in_path):
        for item in in_path:
            self.location_queue.append(item)
        self.next_target = self.get_next_location()

    def calculate_direction_to_next_target(self) -> Moving_const:
        if self.next_target is None:
            if self._renderer.get_current_mode() == Monsters_moving_const.FIND and not self._renderer.pacman_in_move():
                self.request_path_to_player(self)
            else:
                self.game_controller.request_new_random_path(self)
            return Moving_const.AGAIN_POS

        diff_x = self.next_target[0] - self.x
        diff_y = self.next_target[1] - self.y
        if diff_x == 0:
            return Moving_const.DOWN if diff_y > 0 else Moving_const.UP
        if diff_y == 0:
            return Moving_const.LEFT if diff_x < 0 else Moving_const.RIGHT

        if self._renderer.get_current_mode() == Monsters_moving_const.FIND and not self._renderer.pacman_in_move():
            self.request_path_to_player(self)
        else:
            self.game_controller.request_new_random_path(self)
        return Moving_const.AGAIN_POS

    def request_path_to_player(self, in_ghost):
        player_position = screen_into_maze(in_ghost._renderer.get_hero_position())
        current_maze_coord = screen_into_maze(in_ghost.get_new_position())
        path = self.game_controller.p.get_path(current_maze_coord[1], current_maze_coord[0], player_position[1],
                                               player_position[0])

        new_path = [maze_into_screen(item) for item in path]
        in_ghost.set_new_path(new_path)

    def automatic_move(self, in_direction: Moving_const):
        if in_direction == Moving_const.UP:
            self.new_position(self.x, self.y - 1)
        elif in_direction == Moving_const.DOWN:
            self.new_position(self.x, self.y + 1)
        elif in_direction == Moving_const.LEFT:
            self.new_position(self.x - 1, self.y)
        elif in_direction == Moving_const.RIGHT:
            self.new_position(self.x + 1, self.y)

    def draw(self):
        self.image = self.sprite_fright if self._renderer.pacman_in_move() else self.sprite_normal
        super(Monsters, self).draw()


class Coins(Object_in_game):
    def __init__(self, in_surface, x, y):
        super().__init__(in_surface, x, y, 4, (255, 255, 0), True)


class Bonuses(Object_in_game):
    def __init__(self, in_surface, x, y):
        super().__init__(in_surface, x, y, 8, (255, 255, 255), True)


class Find_Packman:
    def __init__(self, in_arr):
        cost = np.array(in_arr, dtype=np.bool_).tolist()
        self.pf = tcod.path.AStar(cost=cost, diagonal=0)

    def get_path(self, from_x, from_y, to_x, to_y) -> object:
        res = self.pf.get_path(from_x, from_y, to_x, to_y)
        return [(sub[1], sub[0]) for sub in res]


class Game_Control:
    def __init__(self):
        self.ascii_maze = [
            "XXXX  XXXXXXXX XXXXXXXX  XXXX",
            "X                           X",
            "X XXXX XXXXXXX XXXXXXX XXXX X",
            "X                           X",
            "  XXXXXX X XXXXXXX X XXXXXX  ",
            "X        X    X    X        X",
            "XXX XXXXXXXXX X XXXXXXXXX XXX",
            "X    O  X           X  O    X",
            "XX XX XXX XXXXXXXXX XXX XX XX",
            "X   X X       O       X X   X",
            "X X    X    X X X    X      X",
            "X XX XXX XXXX X XXXX XXX XX X",
            "       X XG   X   GX X       ",
            "X XXXXXX XG       GX XXXXXX X",
            "X        XXXXX XXXXX        X",
            "  X  XXX             XXX  X  ",
            "X       XX  XXXXX  XX       X",
            "X XXXXX   XX  X  XX   XXXXX X",
            "X       X     O     X       X",
            "XX XX XXX XXXXXXXXX XXX XX XX",
            "X       X     O     X       X",
            "XXX XXXXXXXXX X XXXXXXXXX XXX",
            "X             X             X",
            "  XXXXXX X XXXXXXX X XXXXXX  ",
            "X     O               O     X",
            "X XXXX XXXXXXX XXXXXXX XXXX X",
            "X                           X",
            "XXXX  XXXXXXXX XXXXXXXX  XXXX",
        ]

        self.numpy_maze = []
        self.cookie_spaces = []
        self.powerup_spaces = []
        self.reachable_spaces = []
        self.ghost_spawns = []
        self.ghost_colors = [
            "4monst-transformed.png",
            "3monst-transformed.png",
            "6monst-transformed.png",
            "5monst-ddVBTHuZv-transformed.png"
        ]
        self.size = (0, 0)
        self.convert_maze_to_numpy()
        self.p = Find_Packman(self.numpy_maze)

    def request_new_random_path(self, in_ghost: Monsters):
        random_space = random.choice(self.reachable_spaces)
        current_maze_coord = screen_into_maze(in_ghost.get_new_position())

        path = self.p.get_path(current_maze_coord[1], current_maze_coord[0], random_space[1],
                               random_space[0])
        test_path = [maze_into_screen(item) for item in path]
        in_ghost.set_new_path(test_path)

    def convert_maze_to_numpy(self):
        for x, row in enumerate(self.ascii_maze):
            self.size = (len(row), x + 1)
            binary_row = []
            for y, column in enumerate(row):
                if column == "G":
                    self.ghost_spawns.append((y, x))

                if column == "X":
                    binary_row.append(0)
                else:
                    binary_row.append(1)
                    self.cookie_spaces.append((y, x))
                    self.reachable_spaces.append((y, x))
                    if column == "O":
                        self.powerup_spaces.append((y, x))

            self.numpy_maze.append(binary_row)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = Access()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(main_window)
    widget.setFixedWidth(450)
    widget.setFixedHeight(650)
    widget.show()
    flag = False
    app.exec_()
    if flag:
        SIZE_FOR_ALL = 32
        game_start = Game_Control()
        size = game_start.size
        game_change = Game_Change(size[0] * SIZE_FOR_ALL, size[1] * SIZE_FOR_ALL)
    
        for y, row in enumerate(game_start.numpy_maze):
            for x, column in enumerate(row):
                if column == 0:
                    game_change.add_wall(Wall(game_change, x, y, SIZE_FOR_ALL))
    
        for coins_place in game_start.cookie_spaces:
            translated = maze_into_screen(coins_place)
            cookie = Coins(game_change, translated[0] + SIZE_FOR_ALL / 2, translated[1] + SIZE_FOR_ALL / 2)
            game_change.add_coins(cookie)
    
        for bonuses_place in game_start.powerup_spaces:
            translated = maze_into_screen(bonuses_place)
            powerup = Bonuses(game_change, translated[0] + SIZE_FOR_ALL / 2, translated[1] + SIZE_FOR_ALL / 2)
            game_change.add_bonuses(powerup)
    
        for i, ghost_spawn in enumerate(game_start.ghost_spawns):
            translated = maze_into_screen(ghost_spawn)
            monsters = Monsters(game_change, translated[0], translated[1], SIZE_FOR_ALL, game_start,
                          game_start.ghost_colors[i % 4])
            game_change.add_monsters(monsters)
    
        pacman = Packman(game_change, SIZE_FOR_ALL, SIZE_FOR_ALL, SIZE_FOR_ALL)
        game_change.add_pacman(pacman)
        game_change.set_current_mode(Monsters_moving_const.FIND)
        game_change.tick(120)
