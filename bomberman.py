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
import time
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
}

DEFAULT_P1CONTROLS = {
    'up': pygame.K_UP,
    'down': pygame.K_DOWN,
    'left': pygame.K_LEFT,
    'right': pygame.K_RIGHT,
    'place_bomb': pygame.K_SPACE,
}

GAME_FONT = pygame.font.Font(None, 58) 

def list_colliding_coordinates(x, y):
    return math.floor(x), math.ceil(x), math.floor(y), math.ceil(y)

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
    def __init__(self, lvl, x, y, place_time, timer=1):
        self.pos = [x, y]
        self.timer = timer
        self.place_time = place_time
        self.should_spawn = not self.affects_environment(lvl)
    
    def loop(self, lvl):
        self.draw(lvl.canvas)
        if pygame.time.get_ticks()//1000 - self.place_time >= self.timer:
            lvl.flames.remove(self)

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
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return xl <= self.pos[0] <= xh and yl <= self.pos[1] <= yh
    
    # Abstract method to be defined in children classes
    def draw(self, canvas):
        pass


class CenterFlame(Flame):
    def __init__(self, lvl, x, y, flames_list, radius, place_time, timer=1):
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


class Player:
    def __init__(self, x, y, controls=DEFAULT_P1CONTROLS, max_bombs=1):
        self.pos = [x, y]
        self.direction = 'down'
        self.controls = controls
        self.max_bombs = max_bombs

    def loop(self, lvl):
        self.draw(lvl.canvas)
        
        for f in lvl.flames:
            if f.collides(*self.pos):
                self.die()
                
    def die(self):
        print("PLAYER DIED PLACEHOLDER")
        
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
        
    def check_key_move(self, key, lvl):
        new_pos = self.pos[:]

        if key == self.controls['up']:
            new_pos[1] -= 0.0625
            new_direction = 'up'
        elif key == self.controls['down']:
            new_pos[1] += 0.0625
            new_direction = 'down'
        elif key == self.controls['left']:
            new_pos[0] -= 0.0625
            new_direction = 'left'
        elif key == self.controls['right']:
            new_pos[0] += 0.0625
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
            
            # The player is at a corner, so they should be able to move.
            if new_direction == 'up' or new_direction == 'down':
                dif = rounded_pos[0] - new_pos[0]
                if dif > 0.125:
                    new_pos[0] += 0.125
                elif dif < -0.125:
                    new_pos[0] += -0.125
                else:
                    new_pos[0] += dif

            elif new_direction == 'left' or new_direction == 'right':
                dif = rounded_pos[1] - new_pos[1]
                if dif > 0.125:
                    new_pos[1] += 0.125
                elif dif < -0.125:
                    new_pos[1] += -0.125
                else:
                    new_pos[1] += dif
        
        for bomb in lvl.bombs.values():
            if bomb.collides(*new_pos) and not bomb.collides(*self.pos):
                return
        self.pos = new_pos
        self.direction = new_direction

    def handle_key(self, key, lvl):
        if key == self.controls['place_bomb']:
            if lvl.placed_bombs(self) < self.max_bombs:
                lvl.try_place_bomb(*self.pos, self)
        self.check_key_move(key, lvl)


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
    def __init__(self, canvas, matrix, players):
        self.canvas = canvas
        self.matrix = matrix
        self.players = players
        self.bombs = {}
        self.flames = []
        self.enemies = []

    def loop(self):
        self.matrix.draw(self.canvas)
        for player in self.players:
            player.loop(self)
        for bomb in self.bombs.values():
            bomb.loop(self)
        # Remove items that have a None value
        for k in list(self.bombs.keys()):
            if self.bombs[k] == None:
                del self.bombs[k]
        for flame in self.flames:
            flame.loop(self)
        for enemy in self.enemies:
            enemy.loop(self)

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
        

class Game:
    def __init__(self, screen, initial_time=300):
        # TODO Don't hardcode level layout
        matrix = BlockMatrix(goal=(5, 3))
        matrix.matrix[7][7] = Block.BOX
        players = [Player(1, 1)]

        canvas = LevelCanvas(screen, (0, 100))
        self.level = Level(canvas, matrix, players)
        
        self.screen = screen
        self.time = initial_time
        self.begin_time = pygame.time.get_ticks()//1000
    
    def loop(self):
        self.draw_gamebar()
        self.level.loop()
        
    def draw_gamebar(self):
        timer = self.time - pygame.time.get_ticks()//1000 + self.begin_time
        timer = 'TIME: {:03d}'.format(int(timer))
        timer = GAME_FONT.render(timer, True, (0, 0, 0)) 
        
        self.screen.blit(timer, timer.get_rect(x=25, centery=50))

    def handle_key(self, key):
        self.level.handle_key(key)
        


class Context:
    def __init__(self):
        self.size = 650, 750
        self.speed = [2, 2]
        self.screen = pygame.display.set_mode(self.size)
        self.game = Game(self.screen)

        pygame.key.set_repeat(5, 60)


    def loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    self.game.handle_key(event.key)

            self.screen.fill((140, 140, 140))
            # if self.menu.is_open:
            #     self.menu.draw()
            # else:
            self.game.loop()
            
            pygame.display.flip()

Context().loop()
