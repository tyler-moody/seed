import curses
from curses import wrapper
import logging
from logging import debug, error
import operator
import random
import sys
from time import sleep

class Screen:
    def __init__(self, stat_scr, world_scr):
        self.stat_scr = stat_scr
        self.world_scr = world_scr

    def onWorldUpdate(self, world):
        self.stat_scr.clear()
        self.stat_scr.addstr(0, 0, 'population')
        self.stat_scr.addstr(1, 0, str(world.population))

        self.stat_scr.addstr(3, 0, 'age')
        self.stat_scr.addstr(4, 0, str(world.age))

        self.stat_scr.addstr(6, 0, 'world')
        self.stat_scr.addstr(7, 0, str(world.uid))

        self.stat_scr.refresh()

        self.world_scr.clear()
        for obj in world.objects:
            debug('drawing object at {} {}'.format(obj.x, obj.y))
            self.world_scr.addstr(obj.y, obj.x, obj.ch)
        for animal in world.animals:
            debug('drawing animal at {} {}'.format(animal.x, animal.y))
            self.world_scr.addstr(animal.y, animal.x, animal.ch)
        self.world_scr.refresh()
