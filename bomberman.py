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


def snap_coordinates(x, y):
    return round(x/50)*50, round(y/50)*50

def list_colliding_coordinates(x, y):
    x = x/50
    y = y/50
    return math.floor(x), math.ceil(x), math.floor(y), math.ceil(y)

class Block(Enum):
    GRASS = 0
    WALL = 1
    BOX = 2
    BOX_GOAL = 3
    GOAL = 4

    def draw(self, ctx, x, y):
        assets_indexes = {
            Block.GRASS: 'grass',
            Block.WALL: 'wall',
            Block.BOX: 'box',
            Block.BOX_GOAL: 'box',
            Block.GOAL: 'goal',
        }
        img = ctx['assets'][assets_indexes[self]]
        ctx['screen'].blit(img, (x, y))


class Bomb:
    def __init__(self, x, y, radius=3, timer=3):
        self.pos = [x, y]
        self.timer = timer
        self.radius = radius
        self.place_time = time.process_time()
    
    def loop(self, ctx):
        self.draw(ctx)
        if time.process_time() - self.place_time >= self.timer:
            self.detonate(ctx)
    
    def collides(self, x, y):
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return xl <= self.pos[0]//50 <= xh and yl <= self.pos[1]//50 <= yh
    
    def detonate(self, ctx):
        x, y = self.pos
        flames_list = ctx['level']['flames']
        flame = CenterFlame(ctx, x, y, flames_list, self.radius, time.process_time())
        flames_list.append(flame)
        ctx['level']['bombs'].remove(self)

    def draw(self, ctx):
        assets = ctx['assets']
        img = assets['bomb']

        ctx['screen'].blit(img, self.pos)


class Flame:
    def __init__(self, x, y, place_time, timer=1):
        self.pos = [x, y]
        self.timer = timer
        self.place_time = place_time
    
    def loop(self, ctx):
        self.draw(ctx)
        if time.process_time() - self.place_time >= self.timer:
            ctx['level']['flames'].remove(self)

    def affects_environment(self, ctx):
        x = self.pos[0]//50
        y = self.pos[1]//50
        matrix = ctx['level']['matrix'].matrix
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
        return xl <= self.pos[0]//50 <= xh and yl <= self.pos[1]//50 <= yh
    
    # Defined in children classes
    def draw(self, ctx):
        pass


class CenterFlame(Flame):
    def __init__(self, ctx, x, y, flames_list, radius, place_time, timer=1):
        super().__init__(x, y, place_time, timer)
        
        if radius > 1 and not self.affects_environment(ctx):
            l = HorizontalFlame(ctx, x-50, y, flames_list, radius-1, place_time, timer, False)
            r = HorizontalFlame(ctx, x+50, y, flames_list, radius-1, place_time, timer, True)
            u = VerticalFlame(ctx, x, y-50, flames_list, radius-1, place_time, timer, False)
            d = VerticalFlame(ctx, x, y+50, flames_list, radius-1, place_time, timer, True)
            new_flames = [l, r, u, d]
            flames_list += [f for f in new_flames if not f.affects_environment(ctx)]

    def draw(self, ctx):
        assets = ctx['assets']
        img = assets['flame_center']

        ctx['screen'].blit(img, self.pos)

class HorizontalFlame(Flame):
    def __init__(self, ctx, x, y, flames_list, radius, place_time, timer, left_to_right):
        super().__init__(x, y, place_time, timer)

        if radius > 1 and not self.affects_environment(ctx):
            if left_to_right:
                nx = x+50
            else:
                nx = x-50
            flame = HorizontalFlame(ctx, nx, y, flames_list, radius-1, place_time, timer, left_to_right)
            if not flame.affects_environment(ctx):
                flames_list.append(flame)

    def draw(self, ctx):
        assets = ctx['assets']
        img = assets['flame_horizontal']

        ctx['screen'].blit(img, self.pos)

class VerticalFlame(Flame):
    def __init__(self, ctx, x, y, flames_list, radius, place_time, timer, up_to_down):
        super().__init__(x, y, place_time, timer)

        if radius > 1 and not self.affects_environment(ctx):
            if up_to_down:
                ny = y+50
            else:
                ny = y-50
            flame = VerticalFlame(ctx, x, ny, flames_list, radius-1, place_time, timer, up_to_down)
            if not flame.affects_environment(ctx):
                flames_list.append(flame)

    def draw(self, ctx):
        assets = ctx['assets']
        img = assets['flame_vertical']

        ctx['screen'].blit(img, self.pos)


class Player:
    def __init__(self, x, y, controls):
        self.pos = [x, y]
        self.direction = 'down'
        self.controls = controls

    def loop(self, ctx):
        self.draw(ctx)
        
        for f in ctx['level']['flames']:
            if f.collides(*self.pos):
                self.die()
                
    def die(self):
        print("PLAYER DIED PLACEHOLDER")
        
    def draw(self, ctx):
        assets = ctx['assets']
        if self.direction == 'up':
            img = assets['player_up']
        elif self.direction == 'down':
            img = assets['player_down']
        elif self.direction == 'left':
            img = assets['player_left']
        elif self.direction == 'right':
            img = assets['player_right']

        ctx['screen'].blit(img, self.pos)
        
    def check_key_move(self, key, lvl):
        new_pos = self.pos[:]

        if key == self.controls['up']:
            new_pos[1] -= 10
            new_direction = 'up'
        elif key == self.controls['down']:
            new_pos[1] += 10
            new_direction = 'down'
        elif key == self.controls['left']:
            new_pos[0] -= 10
            new_direction = 'left'
        elif key == self.controls['right']:
            new_pos[0] += 10
            new_direction = 'right'
        else:
            return
        
        if lvl['matrix'].check_collides(*new_pos):
            return
        
        for bomb in lvl['bombs']:
            if bomb.collides(*new_pos) and not bomb.collides(*self.pos):
                return
        self.pos = new_pos
        self.direction = new_direction

    def check_key_place_bomb(self, key, lvl):
        if key == self.controls['place_bomb']:
            lvl['bombs'].append(Bomb(*snap_coordinates(*self.pos)))

    def handle_key(self, key, lvl):
        self.check_key_move(key, lvl)
        self.check_key_place_bomb(key, lvl)


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

    def draw(self, ctx):
        for i, row in enumerate(self.matrix):
            for j, block in enumerate(row):
                block.draw(ctx, j*50, i*50)

    def is_solid(self, x, y):
        return self.matrix[y][x] in [Block.WALL, Block.BOX, Block.BOX_GOAL]
    
    def check_collides(self, x, y):
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return self.is_solid(xl, yl) or self.is_solid(xl, yh) or self.is_solid(xh, yl) or self.is_solid(xh, yh)


def init():
    size = 650, 650
    speed = [2, 2]

    screen = pygame.display.set_mode(size)
    assets = {
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

    controls = {
        'up': pygame.K_UP,
        'down': pygame.K_DOWN,
        'left': pygame.K_LEFT,
        'right': pygame.K_RIGHT,
        'place_bomb': pygame.K_SPACE,
    }

    level = {
        'matrix': BlockMatrix(goal=(5, 3)),
        'player': Player(50, 50, controls),
        'bombs': [],
        'flames': [],
    }
    
    level['matrix'].matrix[7][7] = Block.BOX

    context = {
        'size': size,
        'speed': speed,
        'assets': assets,
        'screen': screen,
        'level': level,
    }

    pygame.key.set_repeat(5, 90)

    return context

def gameloop(ctx):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN:
            ctx['level']['player'].handle_key(event.key, ctx['level'])

    ctx['screen'].fill((0, 0, 0))
    ctx['level']['matrix'].draw(ctx)
    ctx['level']['player'].loop(ctx)
    for bomb in ctx['level']['bombs']:
        bomb.loop(ctx)
    for flame in ctx['level']['flames']:
        flame.loop(ctx)
    pygame.display.flip()


context = init()
while True:
    gameloop(context)
