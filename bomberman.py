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
pygame.init()


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
        }
        img = ctx['assets'][assets_indexes[self]]
        ctx['screen'].blit(img, (x, y))


class Player:
    def __init__(self, x, y, controls):
        self.pos = [x, y]
        self.direction = 'down'
        self.controls = controls

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
        
    def handle_key(self, key, lvl):
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
        
        if not lvl.check_collides(*new_pos):
            self.pos = new_pos
            self.direction = new_direction

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
        x = x/50
        y = y/50
        xl, xh, yl, yh = math.floor(x), math.ceil(x), math.floor(y), math.ceil(y)
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
            ctx['level']['player'].handle_key(event.key, ctx['level']['matrix'])

    ctx['screen'].fill((0, 0, 0))
    ctx['level']['matrix'].draw(context)
    ctx['level']['player'].draw(context)
    pygame.display.flip()


context = init()
while True:
    gameloop(context)
