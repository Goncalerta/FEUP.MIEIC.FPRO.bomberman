#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 18:06:36 2019

@author: up201905348
"""

from enum import Enum
import sys, pygame
pygame.init()

class Block(Enum):
    GRASS = 0
    WALL = 1
    BOX = 2
    BOX_GOAL = 3
    GOAL = 4

class Level:
    def __init__(self, matrix = None):
        if matrix == None:
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
        else:
            self.matrix = matrix

    def draw(self, ctx):
        for i, row in enumerate(self.matrix):
            for j, block in enumerate(row):
                ctx['screen'].blit(ctx['entities'][Block(block)], (j*50, i*50))

    

def init():
    size = width, height = 650, 650
    speed = [2, 2]
    
    screen = pygame.display.set_mode(size)
    entities = {
        Block.GRASS: pygame.image.load("assets/grass.png"),
        Block.WALL: pygame.image.load("assets/wall.png")
    }

    level = Level()

    context = {
        'size': size,
        'speed': speed,
        'entities': entities,
        'screen': screen,
    }
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.fill((0, 0, 0))
        level.draw(context)
        pygame.display.flip()

init()
    
