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

def init():
    size = width, height = 650, 650
    speed = [2, 2]
    
    screen = pygame.display.set_mode(size)
    entities = {
        Block.GRASS: pygame.image.load("assets/grass.png"),
        Block.WALL: pygame.image.load("assets/wall.png")
    }
    
    block_rect = entities[Block.GRASS].get_rect()

    level = [
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
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.fill((0, 0, 0))

        for i, row in enumerate(level):
            for j, block in enumerate(row):
                screen.blit(entities[Block(block)], (j*50, i*50))


            
        
        pygame.display.flip()

init()
    
