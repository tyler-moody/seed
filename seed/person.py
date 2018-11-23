
import curses
from curses import wrapper
import logging
from logging import debug, error
import operator
import random
import sys
from time import sleep

from entity import Entity
from food import Food

class Person(Entity):
    def __init__(self, world, parameters):
        super().__init__()
        self.name = 'Person'
        self.alive = True
        self._age = 0
        self.ch = 'O'
        self.x = None
        self.y = None
        self.last_ate = -1
        self.last_mated = 0
        self.fertility = parameters['fertility']
        self.hunger_threshold = parameters['hunger_threshold']
        self.starvation_threshold = parameters['starvation_threshold']
        self.hunger = self.starvation_threshold // 2
        self.time_til_mate = self.starvation_threshold - self.hunger + 1
        self.max_age = parameters['max_age']
        self.world = world
        self.observers = set()

    def update(self):
        self._age += 1
        if self._age > self.max_age:
            debug('animal {} died of old age'.format(self.uid))
            self.alive = False
            return

        self.hunger += 1
        if self.hunger > self.hunger_threshold:
            self.eat_food_within_reach()
        if self.hunger > self.starvation_threshold:
            debug('animal {} died of starvation'.format(self.uid))
            self.alive = False
            return

        self.mate()
        self.move()

    def _adjacent_cells(self):
        return [tuple(map(operator.add, (self.x, self.y), delta)) for delta in self.deltas]

    def eat_food_within_reach(self):
        coordinates = self._adjacent_cells()
        for coord in coordinates:
            if coord in self.world.occupants:
                target = self.world.occupants[coord]
                if type(target) == Food:
                    self.world.eat(target, self)

    def move(self):
        r = random.random()
        n = int(r*8)
        delta = self.deltas[n]
        coordinate = tuple(map(operator.add, delta, (self.x, self.y)))
        self.world.move(self, coordinate)

    def mate(self):
        if self.last_ate > self.last_mated:
            coordinates = self._adjacent_cells()
            for coord in coordinates:
                if coord in self.world.occupants:
                    target = self.world.occupants[coord]
                    if type(target) == Person:
                        r = random.random()
                        if r > 1-self.fertility:
                            self.world.reproduce(self, target)
