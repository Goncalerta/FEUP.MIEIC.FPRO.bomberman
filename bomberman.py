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
    'icon': pygame.image.load('assets/icon.png'),
    'title_screen': pygame.image.load('assets/title_screen.png'),
    'menu_pointer': pygame.image.load('assets/menu_pointer.png'),
    'grass': pygame.image.load('assets/grass.png'),
    'wall': pygame.image.load('assets/wall.png'),
    'box': pygame.image.load('assets/box.png'),
    'goal_closed': pygame.image.load('assets/goal_closed.png'),
    'goal_open': pygame.image.load('assets/goal_open.png'),
    'powerup_life': pygame.image.load('assets/powerup_life.png'),
    'powerup_blast': pygame.image.load('assets/powerup_blast.png'),
    'powerup_bombup': pygame.image.load('assets/powerup_bombup.png'),
    'player1_up': pygame.image.load('assets/player1_up.png'),
    'player1_down': pygame.image.load('assets/player1_down.png'),
    'player1_left': pygame.image.load('assets/player1_left.png'),
    'player1_right': pygame.image.load('assets/player1_right.png'),
    'player2_up': pygame.image.load('assets/player2_up.png'),
    'player2_down': pygame.image.load('assets/player2_down.png'),
    'player2_left': pygame.image.load('assets/player2_left.png'),
    'player2_right': pygame.image.load('assets/player2_right.png'),
    'bomb': [
      pygame.image.load('assets/bomb/bomb_{}.png'.format(i)) for i in range(1, 11)
    ],
    'exploding_box': [
      pygame.image.load('assets/exploding_box/exploding_box_{}.png'.format(i)) for i in range(1, 7)
    ],
    'flame_center': pygame.image.load('assets/explosion_center.png'),
    'flame_horizontal': pygame.image.load('assets/explosion_horizontal.png'),
    'flame_vertical': pygame.image.load('assets/explosion_vertical.png'),
    'flame_end_left': pygame.image.load('assets/explosion_end_left.png'),
    'flame_end_right': pygame.image.load('assets/explosion_end_right.png'),
    'flame_end_up': pygame.image.load('assets/explosion_end_up.png'),
    'flame_end_down': pygame.image.load('assets/explosion_end_down.png'),
    'enemy': pygame.image.load('assets/enemy.png'),
    'falling_wall': pygame.image.load('assets/falling.png'),
}

DEFAULT_SINGLEPLAYER_CONTROLS = {
    'up': pygame.K_UP,
    'down': pygame.K_DOWN,
    'left': pygame.K_LEFT,
    'right': pygame.K_RIGHT,
    'place_bomb': pygame.K_SPACE,
}

DEFAULT_P1CONTROLS = {
    'up': pygame.K_UP,
    'down': pygame.K_DOWN,
    'left': pygame.K_LEFT,
    'right': pygame.K_RIGHT,
    'place_bomb': pygame.K_PERIOD,
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
    BOX_POWERUP_LIFE = 5
    POWERUP_LIFE = 6
    BOX_POWERUP_BLAST = 7
    POWERUP_BLAST = 8
    BOX_POWERUP_BOMBUP = 9
    POWERUP_BOMBUP = 10
    FALLING_WALL = 11

    def draw(self, canvas, x, y, lvl):
        if self == Block.GOAL:
            if len(lvl.enemies) == 0:
                img = ASSETS['goal_open']
            else:
                img = ASSETS['goal_closed']
        else:
            assets_indexes = {
                Block.GRASS: 'grass',
                Block.WALL: 'wall',
                Block.BOX: 'box',
                Block.BOX_POWERUP_LIFE: 'box',
                Block.BOX_POWERUP_BLAST: 'box',
                Block.BOX_POWERUP_BOMBUP: 'box',
                Block.BOX_GOAL: 'box',
                Block.POWERUP_LIFE: 'powerup_life',
                Block.POWERUP_BLAST: 'powerup_blast',
                Block.POWERUP_BOMBUP: 'powerup_bombup',
                Block.FALLING_WALL: 'falling_wall'
            }
            img = ASSETS[assets_indexes[self]]
        canvas.draw(img, (x, y))


class Bomb:
    def __init__(self, x, y, placer, radius=2, timer=3):
        self.pos = (x, y)
        self.timer = timer
        self.radius = radius
        self.placer = placer
    
    def loop(self, lvl, time):
        self.draw(lvl.canvas)
        self.timer -= time
        if self.timer <= 0:
            self.detonate(lvl)
    
    def collides(self, x, y):
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return xl <= self.pos[0] <= xh and yl <= self.pos[1] <= yh

    # Used to check whether or not the placer of the bomb can still
    # walk through it with no colision.
    def collides_closer(self, x, y):
        rx, ry = round(x), round(y)
        return -0.375 <= x - self.pos[0] <= 0.375 and -0.375 <= y - self.pos[1] <= 0.375
    
    def detonate(self, lvl):
        x, y = self.pos
        flames_list = lvl.flames
        flame = CenterFlame(lvl, x, y, flames_list, self.radius)
        flames_list.append(flame)
        lvl.bombs[self.pos] = None

    def draw(self, canvas):
        current_frame = int((3-self.timer)//0.3)
        canvas.draw(ASSETS['bomb'][current_frame], self.pos)


class Flame:
    def __init__(self, lvl, x, y, timer=0.5):
        self.pos = [x, y]
        self.timer = timer
        self.should_spawn = not self.affects_environment(lvl)

        if lvl.bombs.get(tuple(self.pos), None) != None:
            bomb = lvl.bombs[tuple(self.pos)]
            if bomb.timer > 0.125:
                bomb.timer = 0.125
    
    def loop(self, lvl, time):
        self.timer -= time
        if self.timer <= 0:
            lvl.flames.remove(self)
        else:
            self.draw(lvl.canvas)

    def affects_environment(self, lvl):
        x = self.pos[0]
        y = self.pos[1]
        matrix = lvl.matrix.matrix
        if not (0 <= x <= len(matrix[0]) and 0 <= y <= len(matrix)):
            return False
        block = lvl.matrix.explode_block(x, y)
        return block in [
          Block.BOX, Block.BOX_GOAL, Block.BOX_POWERUP_BOMBUP, Block.BOX_POWERUP_BLAST, Block.BOX_POWERUP_LIFE,
          Block.WALL, Block.GOAL
        ]
    
    def collides(self, x, y):
        return self.pos[0] - 0.5 <= x <= self.pos[0] + 0.5 and self.pos[1] - 0.5 <= y <= self.pos[1] + 0.5
    
    # Abstract method to be defined in children classes
    def draw(self, canvas):
        pass


class CenterFlame(Flame):
    def __init__(self, lvl, x, y, flames_list, radius, timer=0.5):
        super().__init__(lvl, x, y, timer)
        
        if radius > 1 and self.should_spawn:
            l = HorizontalFlame(lvl, x-1, y, flames_list, radius-1, timer, False)
            r = HorizontalFlame(lvl, x+1, y, flames_list, radius-1, timer, True)
            u = VerticalFlame(lvl, x, y-1, flames_list, radius-1, timer, False)
            d = VerticalFlame(lvl, x, y+1, flames_list, radius-1, timer, True)
            new_flames = [l, r, u, d]
            flames_list += [f for f in new_flames if f.should_spawn]

    def draw(self, canvas):
        canvas.draw(ASSETS['flame_center'], self.pos)

class HorizontalFlame(Flame):
    def __init__(self, lvl, x, y, flames_list, radius, timer, left_to_right):
        super().__init__(lvl, x, y, timer)
        self.radius = radius 
        self.left_to_right = left_to_right

        if radius > 1 and self.should_spawn:
            if left_to_right:
                nx = x+1
            else:
                nx = x-1
            flame = HorizontalFlame(lvl, nx, y, flames_list, radius-1, timer, left_to_right)
            if flame.should_spawn:
                flames_list.append(flame)

    def draw(self, canvas):
        if self.radius == 1 and self.left_to_right:
            canvas.draw(ASSETS['flame_end_right'], self.pos)
        elif self.radius == 1 and not self.left_to_right:
            canvas.draw(ASSETS['flame_end_left'], self.pos)
        else:
            canvas.draw(ASSETS['flame_horizontal'], self.pos)

class VerticalFlame(Flame):
    def __init__(self, lvl, x, y, flames_list, radius, timer, up_to_down):
        super().__init__(lvl, x, y, timer)
        self.radius = radius 
        self.up_to_down = up_to_down

        if radius > 1 and self.should_spawn:
            if up_to_down:
                ny = y+1
            else:
                ny = y-1
            flame = VerticalFlame(lvl, x, ny, flames_list, radius-1, timer, up_to_down)
            if flame.should_spawn:
                flames_list.append(flame)

    def draw(self, canvas):
        if self.radius == 1 and self.up_to_down:
            canvas.draw(ASSETS['flame_end_down'], self.pos)
        elif self.radius == 1 and not self.up_to_down:
            canvas.draw(ASSETS['flame_end_up'], self.pos)
        else:
            canvas.draw(ASSETS['flame_vertical'], self.pos)


class Enemy:
    # Enemy velocity in blocks per second
    VELOCITY = 1.60

    def __init__(self, game, x, y, direction):
        self.game = game
        self.pos = [x, y]
        self.direction = direction
        self.alive = True
        self.score_worth = 50
        self.time_to_disappear = None

    def loop(self, lvl, time):
        self.draw(lvl.canvas)
        if self.alive:
            self.check_has_to_change_direction_due_to_bomb(lvl)
            self.move(lvl, self.VELOCITY*time)
            for f in lvl.flames:
                if f.collides(*self.pos):
                    self.die(lvl)
        else:
            self.time_to_disappear -= time
            if self.time_to_disappear <= 0:
                lvl.enemies.remove(self)

    def die(self, lvl):
        self.alive = False
        self.game.score += self.score_worth
        self.time_to_disappear = 2.5
    
    def check_has_to_change_direction_due_to_bomb(self, lvl):
        if self.direction == 'up':
            bx, fx = self.pos[0], self.pos[0]
            by, fy = math.ceil(self.pos[1]), math.floor(self.pos[1])
            b = 'down'
        elif self.direction == 'down':
            bx, fx = self.pos[0], self.pos[0]
            by, fy = math.floor(self.pos[1]), math.ceil(self.pos[1])
            b = 'up'
        elif self.direction == 'left':
            bx, fx = math.ceil(self.pos[0]), math.floor(self.pos[0])
            by, fy = self.pos[1], self.pos[1]
            b = 'right'
        elif self.direction == 'right':
            bx, fx = math.floor(self.pos[0]), math.ceil(self.pos[0])
            by, fy = self.pos[1], self.pos[1]
            b = 'left'
        elif self.direction == 'idle':
            return

        if (fx, fy) not in lvl.bombs:
            return
        elif (bx, by) not in lvl.bombs:
            self.direction = b
        else:
            self.direction = 'idle'

    def maybe_try_change_direction(self, lvl):
        x, y = int(self.pos[0]), int(self.pos[1])
        if self.direction == 'up':
            weights = [80, 6, 8, 6]
        elif self.direction == 'down':
            weights = [8, 6, 80, 6]
        elif self.direction == 'left':
            weights = [6, 8, 6, 80]
        elif self.direction == 'right':
            weights = [6, 80, 6, 8]
        elif self.direction == 'idle':
            weights = [25, 25, 25, 25]

        # [UP, RIGHT, DOWN, LEFT]
        available = [True, True, True, True]
        for i, pos in enumerate([(x, y-1), (x+1, y), (x, y+1), (x-1, y)]):
            for bomb in lvl.bombs.values():
                if bomb.collides(*pos):
                    available[i] = False
                    break
            available[i] = available[i] and not (
                lvl.matrix.is_solid(*pos) 
                or lvl.matrix.is_goal(*pos)
            )
        total = sum([w for w, a in zip(weights, available) if a])
        weights = [w/total if a else 0 for w, a in zip(weights, available)]
        rnd = random.random()
        aq = 0
        
        for w, direction in zip(weights, ['up', 'right', 'down', 'left']):
            if w == 0:
                continue
            aq += w
            if rnd < aq:
                self.direction = direction
                return
        self.direction = 'idle'

    def move(self, lvl, distance):
        cx, cy = self.pos
        rx, ry = round(self.pos[0]), round(self.pos[1])
        if (ry - cy == 0 and rx - cx == 0) or self.direction == 'idle':
            self.maybe_try_change_direction(lvl)

        if self.direction == 'up':
            if -distance <= ry - cy < 0:
                self.pos[1] = ry
                self.maybe_try_change_direction(lvl)
                self.move(lvl, distance - cy + ry)
            else:
                self.pos[1] -= distance
        elif self.direction == 'down':
            if 0 < ry - cy <= distance:
                self.pos[1] = ry
                self.maybe_try_change_direction(lvl)
                self.move(lvl, distance - ry + cy)
            else:
                self.pos[1] += distance
        elif self.direction == 'left':
            if -distance <= rx - cx < 0:
                self.pos[0] = rx
                self.maybe_try_change_direction(lvl)
                self.move(lvl, distance - cx + rx)
            else:
                self.pos[0] -= distance
        elif self.direction == 'right':
            if 0 < rx - cx <= distance:
                self.pos[0] = rx
                self.maybe_try_change_direction(lvl)
                self.move(lvl, distance - rx + cx)
            else:
                self.pos[0] += distance

    def collides(self, x, y):
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return xl <= self.pos[0] <= xh and yl <= self.pos[1] <= yh

    def draw(self, canvas):
        canvas.draw(ASSETS['enemy'], self.pos)

class Player:
    # Player velocity in blocks per second
    VELOCITY = 1.75

    def __init__(self, game, x, y, sprite='p1', controls=DEFAULT_SINGLEPLAYER_CONTROLS, max_bombs=1, bomb_blast_radius=2):
        self.pos = [x, y]
        self.sprite = sprite
        self.direction = 'down'
        self.controls = controls
        self.max_bombs = max_bombs
        self.game = game
        self.alive = True
        self.bomb_blast_radius = bomb_blast_radius

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
        self.game.player_died(self)
        
    def draw(self, canvas):
        if self.sprite == 'p1':
            if self.direction == 'up':
                img = ASSETS['player1_up']
            elif self.direction == 'down':
                img = ASSETS['player1_down']
            elif self.direction == 'left':
                img = ASSETS['player1_left']
            elif self.direction == 'right':
                img = ASSETS['player1_right']
        elif self.sprite == 'p2':
            if self.direction == 'up':
                img = ASSETS['player2_up']
            elif self.direction == 'down':
                img = ASSETS['player2_down']
            elif self.direction == 'left':
                img = ASSETS['player2_left']
            elif self.direction == 'right':
                img = ASSETS['player2_right']

        canvas.draw(img, self.pos)

    def check_key_move(self, lvl, time):
        new_pos = self.pos[:]
        pressed = pygame.key.get_pressed()
        distance = self.VELOCITY * time

        if pressed[self.controls['up']]:
            new_pos[1] -= distance
            self.direction = 'up'
        elif pressed[self.controls['down']]:
            new_pos[1] += distance
            self.direction = 'down'
        elif pressed[self.controls['left']]:
            new_pos[0] -= distance
            self.direction = 'left'
        elif pressed[self.controls['right']]:
            new_pos[0] += distance
            self.direction = 'right'
        else:
            return
        
        if lvl.matrix.check_collides(*new_pos):
            # Moving in a straight line will result in collision.
            # However, if close enough to a corner, the player
            # should still be able to move.
            rounded_pos = new_pos[:]
            if self.direction == 'down' or self.direction == 'up':
                rounded_pos[0] = round(rounded_pos[0])
            elif self.direction == 'left' or self.direction == 'right':
                rounded_pos[1] = round(rounded_pos[1])

            if lvl.matrix.check_collides(*rounded_pos):
                return
            
            distance *= 2

            # The player is at a corner, so they should be able to move.
            if self.direction == 'up' or self.direction == 'down':
                dif = rounded_pos[0] - new_pos[0]
                if dif > distance:
                    new_pos[0] += distance
                elif dif < -distance:
                    new_pos[0] += -distance
                else:
                    new_pos[0] += dif

            elif self.direction == 'left' or self.direction == 'right':
                dif = rounded_pos[1] - new_pos[1]
                if dif > distance:
                    new_pos[1] += distance
                elif dif < -distance:
                    new_pos[1] += -distance
                else:
                    new_pos[1] += dif
        
        for bomb in lvl.bombs.values():
            if (
              bomb.collides(*new_pos) 
              and not bomb.collides_closer(*self.pos) 
              and calculate_distance(bomb.pos, new_pos) < calculate_distance(bomb.pos, self.pos)
            ):
                return
        self.pos = new_pos
        lvl.matrix.check_obtains_powerups(self)
        if lvl.matrix.check_enters_goal(*self.pos, lvl.enemies):
            # TODO enter goal animation
            if  self.game.start_next_level_timer == None and self.game.restart_level_timer == None:
                self.game.start_next_level_timer = 2.5

    def handle_key(self, key, lvl):
        if key == self.controls['place_bomb']:
            if lvl.placed_bombs(self) < self.max_bombs:
                lvl.try_place_bomb(*self.pos, self)


class BlockMatrix:
    def __init__(self, matrix=None, goal=None):
        self.sudden_death_fallen_blocks = (0, 0)
        self.falling = None
        self.falling_direction = 'right'
        self.move_until = 9
        self.exploding = []
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

    def draw(self, time, canvas, lvl, fallen_state=0):
        for i, row in enumerate(self.matrix):
            for j, block in enumerate(row):
                block.draw(canvas, j, i, lvl)
        if self.falling != None:
            canvas.draw(ASSETS['falling_wall'], self.falling)
        for i, (x, y, e_time) in enumerate(self.exploding):
            e_time -= time 
            if e_time <= 0:
                del self.exploding[i]
                continue
            self.exploding[i] = (x, y, e_time)
            current_frame = int((0.375-e_time)//0.0625)
            current_frame = ASSETS['exploding_box'][current_frame]
            canvas.draw(current_frame, (x, y))

    def explode_block(self, x, y):
        block = self.matrix[y][x]
        
        if block in [Block.POWERUP_BLAST, Block.POWERUP_BOMBUP, Block.POWERUP_LIFE]:
            self.matrix[y][x] = Block.GRASS
        elif block == Block.BOX:
            self.exploding.append((x, y, 0.375))
            self.matrix[y][x] = Block.GRASS
        elif block == Block.BOX_GOAL:
            self.exploding.append((x, y, 0.375))
            self.matrix[y][x] = Block.GOAL
        elif block == Block.BOX_POWERUP_BOMBUP:
            self.exploding.append((x, y, 0.375))
            self.matrix[y][x] = Block.POWERUP_BOMBUP
        elif block == Block.BOX_POWERUP_BLAST:
            self.exploding.append((x, y, 0.375))
            self.matrix[y][x] = Block.POWERUP_BLAST
        elif block == Block.BOX_POWERUP_LIFE:
            self.exploding.append((x, y, 0.375))
            self.matrix[y][x] = Block.POWERUP_LIFE
        return block

    def is_solid(self, x, y):
        return self.matrix[y][x] in [
          Block.WALL, Block.BOX, Block.BOX_GOAL, Block.BOX_POWERUP_BLAST, 
          Block.BOX_POWERUP_BOMBUP, Block.BOX_POWERUP_LIFE
        ]
    
    def drop_wall(self, x, y):
        self.falling = [x, y]
        #self.matrix[y][x] = Block.FALLING_WALL
    
    def drop_next_wall(self):
        if self.falling == None:
            self.drop_wall(1, 1)
        else:
            px, py = self.falling
            self.matrix[py][px] = Block.WALL
            for _ in range(4):
                if self.falling_direction == 'right':
                    for i in range(px, 13):
                        if self.matrix[py][i] != Block.WALL:
                            self.drop_wall(i, py)
                            return
                    self.falling_direction = 'down'
                elif self.falling_direction == 'down':
                    for i in range(py, 13):
                        if self.matrix[i][px] != Block.WALL:
                            self.drop_wall(px, i)
                            return
                    self.falling_direction = 'left'
                elif self.falling_direction == 'left':
                    for i in range(px, -1, -1):
                        if self.matrix[py][i] != Block.WALL:
                            self.drop_wall(i, py)
                            return
                    self.falling_direction = 'up'
                elif self.falling_direction == 'up':
                    for i in range(py, -1, -1):
                        if self.matrix[i][px] != Block.WALL:
                            self.drop_wall(px, i)
                            return
                    self.falling_direction = 'right_j'
                if self.falling_direction == 'right_j':
                    for i in range(px, 13):
                        if self.matrix[py][i] != Block.WALL:
                            self.drop_wall(i, py)
                            return
                    px += 1
                    self.falling_direction = 'down_j'
                elif self.falling_direction == 'down_j':
                    for i in range(py, 13):
                        if self.matrix[i][px] != Block.WALL:
                            self.drop_wall(px, i)
                            return
                    py += 1
                    self.falling_direction = 'left_j'
                elif self.falling_direction == 'left_j':
                    for i in range(px, -1, -1):
                        if self.matrix[py][i] != Block.WALL:
                            self.drop_wall(i, py)
                            return
                    px -= 1
                    self.falling_direction = 'up_j'
                elif self.falling_direction == 'up_j':
                    for i in range(py, -1, -1):
                        if self.matrix[i][px] != Block.WALL:
                            self.drop_wall(px, i)
                            return
                    self.falling_direction = 'right'


    def sudden_death_loop(self, game, time):
        fallen, current = self.sudden_death_fallen_blocks
        current += time
        if current >= 1:
            fallen += 1
            current -= 1
            for player in game.level.players:
                if self.falling == None:
                    break
                wx, wy = self.falling
                px, py = player.pos
                if -0.9 <= px - wx <= 0.9 and -0.9 <= py - wy <= 0.9:
                    player.die()
                elif -1 <= px - wx <= 1 and -0.9 <= py - wy <= 0.9:
                    player.pos[0] = round(player.pos[0])
                elif -0.9 <= px - wx <= 0.9 and -1 <= py - wy <= 1:
                    player.pos[1] = round(player.pos[1])
                elif -1 <= px - wx <= 1 and -1 <= py - wy <= 1:
                    player.pos[0] = round(player.pos[0])
                    player.pos[1] = round(player.pos[1])
            for flame in game.level.flames:
                if flame.pos == self.falling:
                    flame.timer = 0
            if self.falling != None:
                if tuple(self.falling) in game.level.bombs:
                    del game.level.bombs[tuple(self.falling)]
            self.drop_next_wall()
        self.sudden_death_fallen_blocks = fallen, current

    def is_goal(self, x, y):
        return self.matrix[y][x] == Block.GOAL

    def check_obtains_powerups(self, player):
        x, y = player.pos
        rx, ry = int(round(x)), int(round(y))
        if -0.25 <= x - rx <= 0.25 and -0.25 <= y - ry <= 0.25:
            if self.matrix[ry][rx] == Block.POWERUP_BOMBUP:
                self.matrix[ry][rx] = Block.GRASS
                player.max_bombs += 1
            elif self.matrix[ry][rx] == Block.POWERUP_BLAST:
                self.matrix[ry][rx] = Block.GRASS
                player.bomb_blast_radius += 1
            elif self.matrix[ry][rx] == Block.POWERUP_LIFE:
                self.matrix[ry][rx] = Block.GRASS
                player.game.lives += 1

    def check_enters_goal(self, x, y, enemies=[]):
        xl, xh, yl, yh = list_colliding_coordinates(x, y)
        return len(enemies) == 0 and (
          self.is_goal(xl, yl) 
          or self.is_goal(xl, yh) 
          or self.is_goal(xh, yl) 
          or self.is_goal(xh, yh)
        )

    def check_bomb_placeable(self, x, y):
        return self.matrix[y][x] in [Block.GRASS, Block.FALLING_WALL]

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
        self.matrix.draw(time, self.canvas, self)
        for player in self.players:
            player.loop(self, time)
        for bomb in self.bombs.values():
            bomb.loop(self, time)
        # Remove items that have a None value
        for k in list(self.bombs.keys()):
            if self.bombs[k] == None:
                del self.bombs[k]
        for flame in self.flames:
            flame.loop(self, time)
        for enemy in self.enemies:
            enemy.loop(self, time)

    def handle_key(self, key):
        for player in self.players:
            player.handle_key(key, self)

    def try_place_bomb(self, x, y, placer):
        pos = round(x), round(y)
        if pos not in self.bombs and self.matrix.check_bomb_placeable(*pos):
            self.bombs[pos] = Bomb(*pos, placer, placer.bomb_blast_radius)

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
        # 4: Powerups
        elements = [0]*grass_n + [1]*boxes_n + [2] + [3]*enemies_n + [4]
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
                    elif rnd_element == 4:
                        powerup = random.choice([
                          Block.BOX_POWERUP_BLAST, Block.BOX_POWERUP_BOMBUP, Block.BOX_POWERUP_LIFE
                        ])
                        matrix[y][x] = powerup

        matrix = BlockMatrix(matrix)
        return Level(canvas, matrix, players, enemies)

    @staticmethod
    def generate_multiplayer(game, canvas, boxes_limits=[35, 55], powerups_limits=[5, 8]):
        boxes_n = random.randrange(boxes_limits[0], boxes_limits[1]+1)
        powerups_n = random.randrange(powerups_limits[0], powerups_limits[1]+1)
        # Doesn't include grass in spawn areas
        grass_n = Level.NUMBER_OF_RANDOMIZABLE_TILES_MP - boxes_n - powerups_n

        # 0: Grass
        # 1: Boxes
        # 2: Goal
        # 3: Enemies
        # 4: Powerups
        elements = [0]*grass_n + [1]*boxes_n + [4]*powerups_n
        random.shuffle(elements)

        matrix = [[None]*13 for _ in range(13)]
        players = [Player(game, 1, 1, 'p1', DEFAULT_P1CONTROLS), Player(game, 11, 11, 'p2', DEFAULT_P2CONTROLS)]
        
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
                    elif rnd_element == 4:
                        powerup = random.choice([
                          Block.BOX_POWERUP_BLAST, Block.BOX_POWERUP_BOMBUP,
                        ])
                        matrix[y][x] = powerup

        matrix = BlockMatrix(matrix)
        return Level(canvas, matrix, players)


class Game:
    def __init__(self, context, screen, initial_time=200):
        self.context = context
        self.screen = screen
        self.initial_time = initial_time

        self.time = None
        self.level = None 
        self.initialize_level()
        
    def initialize_level(self):
        pass

    def loop(self, time):
        self.draw_gamebar(time)
        self.level.loop(time)
        
    def draw_gamebar(self, time):
        pass

    def handle_key(self, key):
        self.level.handle_key(key)


class ClassicGame(Game):
    def __init__(self, context, screen, initial_time=200, lives=3):
        self.score = 0
        self.stage = 1
        self.lives = lives

        self.restart_level_timer = None
        self.start_next_level_timer = None
        super().__init__(context, screen, initial_time)
        
    def initialize_level(self):
        self.restart_level_timer = None
        self.start_next_level_timer = None
        self.time = self.initial_time

        canvas = LevelCanvas(self.screen, (0, 130))
        self.level = Level.generate_singleplayer(self, canvas)

    def trigger_level_failed(self):
        self.lives -= 1

        if self.lives >= 0:
            self.initialize_level()
        else:
            self.context.menu.open('gameover', score=self.score, stage=self.stage)
    
    def trigger_level_complete(self):
        self.stage += 1
        self.initialize_level()

    def loop(self, time):
        if self.restart_level_timer != None:
            self.restart_level_timer -= time
            if self.restart_level_timer <= 0:
                self.trigger_level_failed()
        if self.start_next_level_timer != None:
            self.start_next_level_timer -= time
            if self.start_next_level_timer <= 0:
                self.trigger_level_complete()
        super().loop(time)
        
    def draw_gamebar(self, time):
        self.time -= time
        if self.time <= 0: 
            if self.restart_level_timer == None and self.start_next_level_timer == None:
                self.restart_level_timer = 2.5
            timer = 'TIME\'S UP'
            timer = GAME_FONT.render(timer, True, (200, 0, 0))
        else:
            timer = 'TIME: {:03d}'.format(int(self.time))
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

    def player_died(self, player):
        if self.restart_level_timer == None and self.start_next_level_timer == None:
            self.restart_level_timer = 2.5


class DuelGame(Game):
    def __init__(self, context, screen, initial_time=90):
        self.loser = None
        self.end_level_timer = None
        self.sudden_death = False
        self.p1_wins = 0
        self.p2_wins = 0
        super().__init__(context, screen, initial_time)
        
    def initialize_level(self):
        self.time = self.initial_time

        canvas = LevelCanvas(self.screen, (0, 130))
        self.level = Level.generate_multiplayer(self, canvas)

    def trigger_level_over(self):
        if self.loser != self.level.players[0]:
            self.p1_wins += 1
            self.context.menu.open('mp_gameover_winsp1')
        elif self.loser != self.level.players[1]:
            self.p2_wins += 1
            self.context.menu.open('mp_gameover_winsp2')

    def play_again(self):
        self.loser = None
        self.end_level_timer = None 
        self.sudden_death = None
        self.initialize_level()

    def loop(self, time):
        if self.sudden_death:
            self.level.matrix.sudden_death_loop(self, time)
        if self.end_level_timer != None:
            self.end_level_timer -= time
            if self.end_level_timer <= 0:
                self.trigger_level_over()
        super().loop(time)
        
    def draw_gamebar(self, time):
        self.time -= time
        if self.time <= 0: 
            self.sudden_death = True
            timer = 'SUDDEN DEATH'
            timer = GAME_FONT.render(timer, True, (200, 0, 0))
        else:
            timer = 'TIME: {:02d}'.format(int(self.time))
            timer = GAME_FONT.render(timer, True, (0, 0, 0))

        p1_wins = 'P1 WINS: {:02d}'.format(int(self.p1_wins))
        p1_wins = GAME_FONT.render(p1_wins, True, (29, 112, 250))
        p2_wins = 'P2 WINS: {:02d}'.format(int(self.p2_wins))
        p2_wins = GAME_FONT.render(p2_wins, True, (240, 30, 0))

        self.screen.blit(p1_wins, p1_wins.get_rect(left=30, centery=35))
        self.screen.blit(timer, timer.get_rect(right=610, centery=35))
        self.screen.blit(p2_wins, p2_wins.get_rect(left=30, centery=95))        

    def player_died(self, player):
        if self.end_level_timer == None:
            self.loser = player
            self.end_level_timer = 2.5


class MenuOption:
    def __init__(self, screen, label, select):
        self.screen = screen
        self.label = label
        self.select = select

    def draw(self, y, sel):
        cursor = ASSETS['menu_pointer']
        label = GAME_FONT.render(self.label, True, (255, 255, 255))

        if sel:
            self.screen.blit(cursor, cursor.get_rect(left=110, centery=y))
        self.screen.blit(label, label.get_rect(left=175, centery=y))


class Menu:
    def __init__(self, screen, context):
        self.context = context
        self.screen = screen
        self.is_open = True
        self.selected = 0
        self.mode = 'main'
        self.score = None
        self.stage = None
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
          'gameover': [
            MenuOption(screen, 'New Game', self.context.restart_game), 
            MenuOption(screen, 'Main menu', lambda: self.open('main'))
          ],
          'mp_gameover_winsp1': [
            MenuOption(screen, 'Play Again', self.context.play_again), 
            MenuOption(screen, 'Main menu', lambda: self.open('main'))
          ],
          'mp_gameover_winsp2': [
            MenuOption(screen, 'Play Again', self.context.play_again), 
            MenuOption(screen, 'Main menu', lambda: self.open('main'))
          ],
        }

    def open(self, mode, score=None, stage=None):
        self.score = score
        self.stage = stage
        if self.mode != mode:
            self.selected = 0
        self.mode = mode
        self.is_open = True

    def draw(self):
        if self.mode == 'main' or self.mode == 'pause':
            title_screen = ASSETS['title_screen']
            self.screen.blit(title_screen, title_screen.get_rect(centerx=325, top=25))
        elif self.mode == 'gameover':
            gameover_label = GAME_FONT.render('Game Over', True, (255, 255, 255))
            score = 'SCORE: {:04d}'.format(self.score)
            score = GAME_FONT.render(score, True, (255, 255, 255))
            stage = 'STAGE: {:02d}'.format(self.stage)
            stage = GAME_FONT.render(stage, True, (255, 255, 255))

            self.screen.blit(gameover_label, gameover_label.get_rect(left=80, top=190))
            self.screen.blit(score, gameover_label.get_rect(left=80, top=250))
            self.screen.blit(stage, gameover_label.get_rect(left=80, top=300))
        elif self.mode == 'mp_gameover_winsp1':
            gameover_label = GAME_FONT.render('Player one wins!', True, (0, 200, 255))
            self.screen.blit(gameover_label, gameover_label.get_rect(left=80, top=300))
        elif self.mode == 'mp_gameover_winsp2':
            gameover_label = GAME_FONT.render('Player two wins!', True, (255, 30, 0))
            self.screen.blit(gameover_label, gameover_label.get_rect(left=80, top=300))
            
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
        pygame.display.set_caption('Bomberman')
        pygame.display.set_icon(ASSETS['icon'])
        self.clock = pygame.time.Clock()
        self.game = None
        self.menu = Menu(self.screen, self)

    def new_classic_game(self):
        self.menu.is_open = False
        self.game = ClassicGame(self, self.screen)

    def new_duel_game(self):
        self.menu.is_open = False
        self.game = DuelGame(self, self.screen)

    def resume_game(self):
        if self.game != None:
            self.menu.is_open = False

    def restart_game(self):
        self.menu.is_open = False
        if type(self.game) is ClassicGame:
            self.game = ClassicGame(self, self.screen)
        else:
            self.game = DuelGame(self, self.screen)

    def play_again(self):
        self.menu.is_open = False
        self.game.play_again()

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
                self.game.loop(self.clock.get_time()/1000)
            
            pygame.display.flip()

Context().loop()
