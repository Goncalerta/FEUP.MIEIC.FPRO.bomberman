#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 11:50:13 2019

@author: up201905348
"""

def comprehensions(i, j):
    c1 = [x for x in range(i, j) if x%10 == 3 or x%10 == 8]
    c2 = (round(x**0.5, 2) for x in range(i, j))
    c3 = {n: ord(n) for n in range(i, j)}
    return (list(c1), tuple(c2), c3)