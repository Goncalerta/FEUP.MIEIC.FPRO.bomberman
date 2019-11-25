#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 18:06:36 2019

@author: up201905348
"""

from enum import Enum
import sys
import pygame
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
    def __init__(self, x, y):
        self.pos = (x, y)
        self.direction = 'down'

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


class Level:
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
        self.matrix[y][x] in [Block.WALL, Block.BOX, Block.BOX_GOAL]


def init():
    size = width, height = 650, 650
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

    level = Level(goal=(5, 3))
    player = Player(50, 50)

    context = {
        'size': size,
        'speed': speed,
        'assets': assets,
        'screen': screen,
    }

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.fill((0, 0, 0))
        level.draw(context)
        player.draw(context)
        pygame.display.flip()


init()
