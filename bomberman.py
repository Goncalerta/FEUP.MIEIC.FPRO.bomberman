#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 18:06:36 2019

@author: up201905348
"""

from enum import Enum
import sys
import pygame
import math
import random
pygame.init()


ASSETS = {
    'grass': pygame.image.load('assets/grass.png'),
    'wall': pygame.image.load('assets/wall.png'),
    'box': pygame.image.load('assets/box.png'),
    'goal': pygame.image.load('assets/goal.png'),
    'player_up': pygame.image.load('assets/player_up.png'),
    'player_down': pygame.image.load('assets/player_down.png'),
    'player_left': pygame.image.load('assets/player_left.png'),
    'player_right': pygame.image.load('assets/player_right.png'),
    'bomb': pygame.image.load('assets/bomb.png'),
    'flame_center': pygame.image.load('assets/explosion_center.png'),
    'flame_horizontal': pygame.image.load('assets/explosion_horizontal.png'),
    'flame_vertical': pygame.image.load('assets/explosion_vertical.png'),
    'enemy': pygame.image.load('assets/enemy.png'),
    'title_screen': pygame.image.load('assets/title_screen.png'),
    'menu_pointer': pygame.image.load('assets/menu_pointer.png'),
}

DEFAULT_P1CONTROLS = {
    'up': pygame.K_UP,
    'down': pygame.K_DOWN,
    'left': pygame.K_LEFT,
    'right': pygame.K_RIGHT,
    'place_bomb': pygame.K_SPACE,
}

DEFAULT_P2CONTROLS = {
    'up': pygame.K_w,
    'down': pygame.K_s,
    'left': pygame.K_a,
    'right': pygame.K_d,
    'place_bomb': pygame.K_q,
}

PAUSE_KEY = pygame.K_ESCAPE
SELECT_KEY = pygame.K_RETURN
UP_KEY = pygame.K_UP 
DOWN_KEY = pygame.K_DOWN

GAME_FONT = pygame.font.Font(None, 58) 


def list_colliding_coordinates(x, y):
    return math.floor(x), math.ceil(x), math.floor(y), math.ceil(y)


def calculate_distance(p1, p2):
    return ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)**0.5


class Block(Enum):
    GRASS = 0
    WALL = 1
    BOX = 2
    BOX_GOAL = 3
    GOAL = 4

    def draw(self, canvas, x, y):
        assets_indexes = {
            Block.GRASS: 'grass',
            Block.WALL: 'wall',
            Block.BOX: 'box',
            Block.BOX_GOAL: 'box',
            Block.GOAL: 'goal',
        }
        img = ASSETS[assets_indexes[self]]
        canvas.draw(img, (x, y))


class Bomb:
    def __init__(self, x, y, placer, radius=2, timer=3):
        self.pos = (x, y)
        self.timer = timer
        self.radius = radius
        self.place_time = pygame.time.get_ticks()//1000
        self.placer = placer
    
    def loop(self, lvl):
        self.draw(lvl.canvas)
        if pygame.time.get_ticks()//1000 - self.place_time >= self.timer:
            self.detonate(lvl)
    
    def collides(self, x, y):
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return xl <= self.pos[0] <= xh and yl <= self.pos[1] <= yh
    
    def detonate(self, lvl):
        x, y = self.pos
        flames_list = lvl.flames
        flame = CenterFlame(lvl, x, y, flames_list, self.radius, pygame.time.get_ticks()//1000)
        flames_list.append(flame)
        lvl.bombs[self.pos] = None

    def draw(self, canvas):
        canvas.draw(ASSETS['bomb'], self.pos)


class Flame:
    def __init__(self, lvl, x, y, place_time, timer=0.5):
        self.pos = [x, y]
        self.timer = timer
        self.place_time = place_time
        self.should_spawn = not self.affects_environment(lvl)
    
    def loop(self, lvl):
        if pygame.time.get_ticks()/1000 - self.place_time >= self.timer:
            lvl.flames.remove(self)
        else:
            self.draw(lvl.canvas)

    def affects_environment(self, lvl):
        x = self.pos[0]
        y = self.pos[1]
        matrix = lvl.matrix.matrix
        if not (0 <= x <= len(matrix[0]) and 0 <= y <= len(matrix)):
            return False
        block = matrix[y][x]
        if block in [Block.GRASS, Block.GOAL]:
            return False
        if block == Block.BOX:
            matrix[y][x] = Block.GRASS
        elif block == Block.BOX_GOAL:
            matrix[y][x] = Block.GOAL
        return True
    
    def collides(self, x, y):
        return self.pos[0] - 0.5 <= x <= self.pos[0] + 0.5 and self.pos[1] - 0.5 <= y <= self.pos[1] + 0.5
    
    # Abstract method to be defined in children classes
    def draw(self, canvas):
        pass


class CenterFlame(Flame):
    def __init__(self, lvl, x, y, flames_list, radius, place_time, timer=0.5):
        super().__init__(lvl, x, y, place_time, timer)
        
        if radius > 1 and self.should_spawn:
            l = HorizontalFlame(lvl, x-1, y, flames_list, radius-1, place_time, timer, False)
            r = HorizontalFlame(lvl, x+1, y, flames_list, radius-1, place_time, timer, True)
            u = VerticalFlame(lvl, x, y-1, flames_list, radius-1, place_time, timer, False)
            d = VerticalFlame(lvl, x, y+1, flames_list, radius-1, place_time, timer, True)
            new_flames = [l, r, u, d]
            flames_list += [f for f in new_flames if f.should_spawn]

    def draw(self, canvas):
        canvas.draw(ASSETS['flame_center'], self.pos)

class HorizontalFlame(Flame):
    def __init__(self, lvl, x, y, flames_list, radius, place_time, timer, left_to_right):
        super().__init__(lvl, x, y, place_time, timer)

        if radius > 1 and self.should_spawn:
            if left_to_right:
                nx = x+1
            else:
                nx = x-1
            flame = HorizontalFlame(lvl, nx, y, flames_list, radius-1, place_time, timer, left_to_right)
            if flame.should_spawn:
                flames_list.append(flame)

    def draw(self, canvas):
        canvas.draw(ASSETS['flame_horizontal'], self.pos)

class VerticalFlame(Flame):
    def __init__(self, lvl, x, y, flames_list, radius, place_time, timer, up_to_down):
        super().__init__(lvl, x, y, place_time, timer)

        if radius > 1 and self.should_spawn:
            if up_to_down:
                ny = y+1
            else:
                ny = y-1
            flame = VerticalFlame(lvl, x, ny, flames_list, radius-1, place_time, timer, up_to_down)
            if flame.should_spawn:
                flames_list.append(flame)

    def draw(self, canvas):
        canvas.draw(ASSETS['flame_vertical'], self.pos)


class Enemy:
    # Enemy velocity in blocks per second
    VELOCITY = 1.70

    def __init__(self, game, x, y, direction):
        self.game = game
        self.pos = [x, y]
        self.direction = direction
        self.alive = True
        self.score_worth = 50
        self.disappear_time = None
    
    def loop(self, lvl, time):
        self.draw(lvl.canvas)
        if self.alive:
            self.move(lvl, time)
            for f in lvl.flames:
                if f.collides(*self.pos):
                    self.die(lvl)
        else:
            if pygame.time.get_ticks() > self.disappear_time:
                lvl.enemies.remove(self)

    def die(self, lvl):
        self.alive = False
        self.game.score += self.score_worth
        self.disappear_time = pygame.time.get_ticks() + 2500
    
    def should_change_direction(self, lvl, new_pos):
        for bomb in lvl.bombs.values():
            if bomb.collides(*new_pos):
                if calculate_distance(bomb.pos, new_pos) < calculate_distance(bomb.pos, self.pos):
                    return True
        return (
          (
            lvl.matrix.check_enters_goal(*new_pos) 
            and not lvl.matrix.check_enters_goal(*self.pos)
          )
          or lvl.matrix.check_collides(*new_pos)
        )

    def move(self, lvl, time):
        new_pos = self.pos[:]
        distance = self.VELOCITY * time/1000

        if self.direction == 'up':
            new_pos[1] -= distance
        elif self.direction == 'down':
            new_pos[1] += distance
        elif self.direction == 'left':
            new_pos[0] -= distance
        elif self.direction == 'right':
            new_pos[0] += distance
        
        if self.should_change_direction(lvl, new_pos):
            if self.direction == 'up': 
                self.direction = 'down'
            elif self.direction == 'down': 
                self.direction = 'up'
            elif self.direction == 'right': 
                self.direction = 'left'
            elif self.direction == 'left': 
                self.direction = 'right'
            return

        for bomb in lvl.bombs.values():
            if bomb.collides(*new_pos):
                if calculate_distance(bomb.pos, new_pos) < calculate_distance(bomb.pos, self.pos):
                    return 
        self.pos = new_pos

    def collides(self, x, y):
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return xl <= self.pos[0] <= xh and yl <= self.pos[1] <= yh

    def draw(self, canvas):
        canvas.draw(ASSETS['enemy'], self.pos)

class Player:
    # Player velocity in blocks per second
    VELOCITY = 1.75

    def __init__(self, game, x, y, controls=DEFAULT_P1CONTROLS, max_bombs=1):
        self.pos = [x, y]
        self.direction = 'down'
        self.controls = controls
        self.max_bombs = max_bombs
        self.game = game
        self.alive = True

    def loop(self, lvl, time):
        self.draw(lvl.canvas)
        if self.alive:
            self.check_key_move(lvl, time)
            for f in lvl.flames:
                if f.collides(*self.pos):
                    self.die()
            for e in lvl.enemies:
                if e.alive and e.collides(*self.pos):
                    self.die()
                
    def die(self):
        self.alive = False
        self.game.restart_level_instant = pygame.time.get_ticks() + 2500
        
    def draw(self, canvas):
        if self.direction == 'up':
            img = ASSETS['player_up']
        elif self.direction == 'down':
            img = ASSETS['player_down']
        elif self.direction == 'left':
            img = ASSETS['player_left']
        elif self.direction == 'right':
            img = ASSETS['player_right']

        canvas.draw(img, self.pos)

    def check_key_move(self, lvl, time):
        new_pos = self.pos[:]
        pressed = pygame.key.get_pressed()
        distance = self.VELOCITY * time/1000

        if pressed[self.controls['up']]:
            new_pos[1] -= distance
            new_direction = 'up'
        elif pressed[self.controls['down']]:
            new_pos[1] += distance
            new_direction = 'down'
        elif pressed[self.controls['left']]:
            new_pos[0] -= distance
            new_direction = 'left'
        elif pressed[self.controls['right']]:
            new_pos[0] += distance
            new_direction = 'right'
        else:
            return
        
        if lvl.matrix.check_collides(*new_pos):
            # Moving in a straight line will result in collision.
            # However, if close enough to a corner, the player
            # should still be able to move.
            rounded_pos = new_pos[:]
            if new_direction == 'down' or new_direction == 'up':
                rounded_pos[0] = round(rounded_pos[0])
            elif new_direction == 'left' or new_direction == 'right':
                rounded_pos[1] = round(rounded_pos[1])

            if lvl.matrix.check_collides(*rounded_pos):
                return
            
            distance *= 2

            # The player is at a corner, so they should be able to move.
            if new_direction == 'up' or new_direction == 'down':
                dif = rounded_pos[0] - new_pos[0]
                if dif > distance:
                    new_pos[0] += distance
                elif dif < -distance:
                    new_pos[0] += -distance
                else:
                    new_pos[0] += dif

            elif new_direction == 'left' or new_direction == 'right':
                dif = rounded_pos[1] - new_pos[1]
                if dif > distance:
                    new_pos[1] += distance
                elif dif < -distance:
                    new_pos[1] += -distance
                else:
                    new_pos[1] += dif
        
        for bomb in lvl.bombs.values():
            if bomb.collides(*new_pos) and not bomb.collides(*self.pos):
                return
        self.pos = new_pos
        self.direction = new_direction
        if lvl.matrix.check_enters_goal(*self.pos):
            # TODO enter goal animation
            self.game.start_next_level_instant = pygame.time.get_ticks() + 2500    

    def handle_key(self, key, lvl):
        if key == self.controls['place_bomb']:
            if lvl.placed_bombs(self) < self.max_bombs:
                lvl.try_place_bomb(*self.pos, self)


class BlockMatrix:
    def __init__(self, matrix=None, goal=None):
        if matrix is None:
            self.matrix = [
                [1 for _ in range(13)],
                [i == 0 or i == 12 for i in range(13)],
                [(i+1) % 2 for i in range(13)],
                [i == 0 or i == 12 for i in range(13)],
                [(i+1) % 2 for i in range(13)],
                [i == 0 or i == 12 for i in range(13)],
                [(i+1) % 2 for i in range(13)],
                [i == 0 or i == 12 for i in range(13)],
                [(i+1) % 2 for i in range(13)],
                [i == 0 or i == 12 for i in range(13)],
                [(i+1) % 2 for i in range(13)],
                [i == 0 or i == 12 for i in range(13)],
                [1 for _ in range(13)],
            ]

            self.matrix = [[Block(i) for i in row] for row in self.matrix]
        else:
            self.matrix = matrix

        if goal is not None:
            x, y = goal
            self.matrix[y][x] = Block.BOX_GOAL

    def draw(self, canvas):
        for i, row in enumerate(self.matrix):
            for j, block in enumerate(row):
                block.draw(canvas, j, i)

    def is_solid(self, x, y):
        return self.matrix[y][x] in [Block.WALL, Block.BOX, Block.BOX_GOAL]
    
    def is_goal(self, x, y):
        return self.matrix[y][x] == Block.GOAL

    def check_enters_goal(self, x, y):
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return self.is_goal(xl, yl) or self.is_goal(xl, yh) or self.is_goal(xh, yl) or self.is_goal(xh, yh)

    def check_collides(self, x, y):
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return self.is_solid(xl, yl) or self.is_solid(xl, yh) or self.is_solid(xh, yl) or self.is_solid(xh, yh)


class LevelCanvas:
    def __init__(self, screen, pos, scale=50):
        self.screen = screen
        self.pos = pos
        self.scale = scale
    
    def draw(self, img, pos):
        x = pos[0]*self.scale + self.pos[0]
        y = pos[1]*self.scale + self.pos[1]
        self.screen.blit(img, (x, y))


class Level:
    def __init__(self, canvas, matrix, players, enemies=[]):
        self.canvas = canvas
        self.matrix = matrix
        self.players = players
        self.bombs = {}
        self.flames = []
        self.enemies = enemies

    def loop(self, time):
        self.matrix.draw(self.canvas)
        for player in self.players:
            player.loop(self, time)
        for bomb in self.bombs.values():
            bomb.loop(self)
        # Remove items that have a None value
        for k in list(self.bombs.keys()):
            if self.bombs[k] == None:
                del self.bombs[k]
        for flame in self.flames:
            flame.loop(self)
        for enemy in self.enemies:
            enemy.loop(self, time)

    def handle_key(self, key):
        for player in self.players:
            player.handle_key(key, self)

    def try_place_bomb(self, x, y, placer):
        pos = round(x), round(y)
        if pos not in self.bombs:
            self.bombs[pos] = Bomb(*pos, placer)

    def placed_bombs(self, player):
        count = 0
        for bomb in self.bombs.values():
            if bomb.placer == player:
                count += 1
        return count
    
    NUMBER_OF_TILES = 13*13
    NUMBER_OF_RANDOMIZABLE_TILES_SP = NUMBER_OF_TILES - 77
    NUMBER_OF_RANDOMIZABLE_TILES_MP = NUMBER_OF_TILES - 79

    @staticmethod
    def generate_singleplayer(game, canvas, enemies_limits=[3, 5], boxes_limits=[15, 35]):
        enemies_n = random.randrange(enemies_limits[0], enemies_limits[1]+1)
        boxes_n = random.randrange(boxes_limits[0], boxes_limits[1]+1)
        # Doesn't include grass in spawn area
        grass_n = Level.NUMBER_OF_RANDOMIZABLE_TILES_SP - enemies_n - boxes_n

        # 0: Grass
        # 1: Boxes
        # 2: Goal
        # 3: Enemies
        # 4: Powerups TODO
        elements = [0]*grass_n + [1]*boxes_n + [2] + [3]*enemies_n
        enemies = []
        random.shuffle(elements)

        matrix = [[None]*13 for _ in range(13)]
        players = [Player(game, 1, 1)]
        
        for x in range(0, 13):
            for y in range(0, 13): 
                if x == 0 or x == 12 or y == 0 or y == 12:
                    matrix[y][x] = Block.WALL
                elif x % 2 == 0 and y % 2 == 0:
                    matrix[y][x] = Block.WALL
                elif x in [1, 2] and y in [1, 2]:
                    matrix[y][x] = Block.GRASS
                else:
                    rnd_element = elements.pop()
                    if rnd_element == 0:
                        matrix[y][x] = Block.GRASS
                    elif rnd_element == 1:
                        matrix[y][x] = Block.BOX
                    elif rnd_element == 2:
                        matrix[y][x] = Block.BOX_GOAL
                    elif rnd_element == 3:
                        matrix[y][x] = Block.GRASS
                        direction = random.choice(['up', 'down', 'left', 'right'])
                        enemies.append(Enemy(game, x, y, direction))

        matrix = BlockMatrix(matrix)
        return Level(canvas, matrix, players, enemies)

    @staticmethod
    def generate_multiplayer(game, canvas, boxes_limits=[40, 60]):
        boxes_n = random.randrange(boxes_limits[0], boxes_limits[1]+1)
        # Doesn't include grass in spawn areas
        grass_n = Level.NUMBER_OF_RANDOMIZABLE_TILES_MP - boxes_n

        # 0: Grass
        # 1: Boxes
        # 2: Goal
        # 3: Enemies
        # 4: Powerups TODO
        elements = [0]*grass_n + [1]*boxes_n 
        random.shuffle(elements)

        matrix = [[None]*13 for _ in range(13)]
        players = [Player(game, 1, 1), Player(game, 11, 11, DEFAULT_P2CONTROLS)]
        
        for x in range(0, 13):
            for y in range(0, 13): 
                if x == 0 or x == 12 or y == 0 or y == 12:
                    matrix[y][x] = Block.WALL
                elif x % 2 == 0 and y % 2 == 0:
                    matrix[y][x] = Block.WALL
                elif (x in [1, 2] and y in [1, 2]) or (x in [10, 11] and y in [10, 11]):
                    matrix[y][x] = Block.GRASS
                else:
                    rnd_element = elements.pop()
                    if rnd_element == 0:
                        matrix[y][x] = Block.GRASS
                    elif rnd_element == 1:
                        matrix[y][x] = Block.BOX

        matrix = BlockMatrix(matrix)
        return Level(canvas, matrix, players)


class Game:
    def __init__(self, screen, initial_time=200):
        self.screen = screen
        self.initial_time = initial_time

        self.time = None
        self.begin_time = None
        self.level = None 
        self.initialize_level()
        
    def initialize_level(self):
        pass

    def loop(self, time):
        self.draw_gamebar()
        self.level.loop(time)
        
    def draw_gamebar(self):
        pass

    def handle_key(self, key):
        self.level.handle_key(key)


class ClassicGame(Game):
    def __init__(self, screen, initial_time=200, lives=3):
        self.score = 0
        self.stage = 1
        self.lives = lives

        self.restart_level_instant = None
        self.start_next_level_instant = None
        super().__init__(screen, initial_time)
        
    def initialize_level(self):
        self.restart_level_instant = None
        self.start_next_level_instant = None
        self.time = self.initial_time
        self.begin_time = pygame.time.get_ticks()//1000

        canvas = LevelCanvas(self.screen, (0, 130))
        self.level = Level.generate_singleplayer(self, canvas)

    def trigger_level_failed(self):
        self.lives -= 1

        if self.lives >= 0:
            self.initialize_level()
        else:
            # TODO GAMEOVER screen
            pass
    
    def trigger_level_complete(self):
        self.stage += 1
        self.initialize_level()

    def loop(self, time):
        if self.restart_level_instant != None:
            if pygame.time.get_ticks() > self.restart_level_instant:
                self.trigger_level_failed()
        if self.start_next_level_instant != None:
            if pygame.time.get_ticks() > self.start_next_level_instant:
                self.trigger_level_complete()
        super().loop(time)
        
    def draw_gamebar(self):
        timer = self.time - pygame.time.get_ticks()//1000 + self.begin_time
        if timer < 0: 
            if self.restart_level_instant == None:
                self.restart_level_instant = pygame.time.get_ticks() + 2500
            timer = 'TIME\'S UP'
            timer = GAME_FONT.render(timer, True, (200, 0, 0))
        else:
            timer = 'TIME: {:03d}'.format(int(timer))
            timer = GAME_FONT.render(timer, True, (0, 0, 0))
        
        score = 'SCORE: {:04d}'.format(self.score)
        score = GAME_FONT.render(score, True, (0, 0, 0))

        stage = 'STAGE: {:02d}'.format(self.stage)
        stage = GAME_FONT.render(stage, True, (0, 0, 0))
        
        lives = 'LIVES: {:02d}'.format(self.lives)
        lives = GAME_FONT.render(lives, True, (0, 0, 0))

        self.screen.blit(stage, score.get_rect(left=30, centery=35))
        self.screen.blit(timer, lives.get_rect(right=610, centery=35))
        self.screen.blit(score, score.get_rect(left=30, centery=95))
        self.screen.blit(lives, lives.get_rect(right=610, centery=95))


class DuelGame(Game):
    def __init__(self, screen, initial_time=200):
        self.end_level_instant = None
        super().__init__(screen, initial_time)
        
    def initialize_level(self):
        self.restart_level_instant = None
        self.start_next_level_instant = None
        self.time = self.initial_time
        self.begin_time = pygame.time.get_ticks()//1000

        canvas = LevelCanvas(self.screen, (0, 130))
        self.level = Level.generate_multiplayer(self, canvas)

    def trigger_level_over(self):
        pass # TODO end menu

    def loop(self, time):
        if self.end_level_instant != None:
            if pygame.time.get_ticks() > self.end_level_instant:
                self.trigger_level_over()
        super().loop(time)
        
    def draw_gamebar(self):
        timer = self.time - pygame.time.get_ticks()//1000 + self.begin_time
        if timer < 0: 
            # TODO trigger sudden death
            timer = 'SUDDEN DEATH'
            timer = GAME_FONT.render(timer, True, (200, 0, 0))
        else:
            timer = 'TIME: {:03d}'.format(int(timer))
            timer = GAME_FONT.render(timer, True, (0, 0, 0))

        self.screen.blit(timer, timer.get_rect(right=610, centery=35))


class MenuOption:
    def __init__(self, screen, label, select):
        self.screen = screen
        self.label = label
        self.select = select

    def draw(self, y, sel):
        cursor = ASSETS['menu_pointer']
        label = GAME_FONT.render(self.label, True, (255, 255, 255))

        if sel:
            self.screen.blit(cursor, cursor.get_rect(left=100, centery=y))
        self.screen.blit(label, label.get_rect(left=175, centery=y))


class Menu:
    def __init__(self, screen, context):
        self.context = context
        self.screen = screen
        self.is_open = True
        self.selected = 0
        self.mode = 'main'
        self.options = {
          'main': [
            MenuOption(screen, 'Classic Mode', self.context.new_classic_game), 
            MenuOption(screen, '2P Duel Mode', self.context.new_duel_game),
            MenuOption(screen, 'Quit Game', sys.exit),
          ],
          'pause': [
            MenuOption(screen, 'Continue', self.context.resume_game), 
            MenuOption(screen, 'Main menu', lambda: self.open('main'))
          ],
          'game_over': [
            MenuOption(screen, 'New Game', self.context.restart_game), 
            MenuOption(screen, 'Main menu', lambda: self.open('main'))
          ]
        }

    def open(self, mode):
        if self.mode != mode:
            self.selected = 0
        self.mode = mode
        self.is_open = True

    def draw(self):
        title_screen = ASSETS['title_screen']
        self.screen.blit(title_screen, title_screen.get_rect(centerx=325, top=25))
        y = 500
        for i, option in enumerate(self.options[self.mode]):
          option.draw(y, self.selected == i)
          y += 70
        
    def handle_key(self, key):
        if key == PAUSE_KEY and self.mode == 'pause':
            self.context.resume_game()
        elif key == SELECT_KEY:
            self.options[self.mode][self.selected].select()
        elif key == UP_KEY:
            if self.selected == 0:
                self.selected = len(self.options[self.mode]) - 1
            else:
                self.selected -= 1
        elif key == DOWN_KEY:
            if self.selected == len(self.options[self.mode]) - 1:
                self.selected = 0
            else:
                self.selected += 1

    
class Context:
    def __init__(self):
        self.size = 650, 780
        self.speed = [2, 2]
        self.screen = pygame.display.set_mode(self.size)
        self.clock = pygame.time.Clock()
        self.game = None
        self.menu = Menu(self.screen, self)

    def new_classic_game(self):
        self.menu.is_open = False
        self.game = ClassicGame(self.screen)

    def new_duel_game(self):
        self.menu.is_open = False
        self.game = DuelGame(self.screen)

    def resume_game(self):
        if self.game != None:
            self.menu.is_open = False

    def restart_game(self):
        pass

    def loop(self):
        while True:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.menu.is_open:
                        self.menu.handle_key(event.key)
                    elif event.key == PAUSE_KEY:
                        self.menu.open('pause')
                    else:
                        self.game.handle_key(event.key)

            if self.menu.is_open:
                self.screen.fill((0, 0, 0))
                self.menu.draw()
            else:
                self.screen.fill((140, 140, 140))
                self.game.loop(self.clock.get_time())
            
            pygame.display.flip()

Context().loop()
