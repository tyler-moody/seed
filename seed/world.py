"""Tracks the location of all entities, manages interactions between entities"""
import logging
from logging import debug, error
import operator
import random
import sys
from time import sleep

from entity import Entity
from person import Person
from food import Food

class World(Entity):
    def __init__(self, lines, cols, parameters):
        super().__init__()
        debug('creating world size lines {} cols {}'.format(lines, cols))
        self.observers = set()
        self.rows = lines
        self.cols = cols
        self._age = 0
        self.parameters = parameters

        self.move_requests = list()
        self.eat_requests = list()

        self.occupants = dict()
        self.objects = list()
        self.animals = list()
        self.forbidden_cells = [(cols-1, lines-1)]
        debug('forbidden cells: {}'.format(self.forbidden_cells))
        for n in range(parameters['initial_population']):
            lil_dude = Person(world=self, parameters=self.parameters)
            self.place(lil_dude, category='animal', retry=True)
        for n in range(parameters['initial_food']):
            food = Food()
            self.place(food, category='object', retry=True)

    def move(self, subject, destination):
        """handle a move request from an entity"""
        self.move_requests.append((subject, destination))

    def eat(self, target, eater):
        """handle an eat request from an entity"""
        self.eat_requests.append((target, eater))

    def reproduce(self, subject0, subject1):
        """handle a reproduce request from an entity"""
        coordinates = subject0._adjacent_cells()
        for coord in coordinates:
            coord = self._sanitize_location(coord)
            if coord not in self.occupants and coord not in self.forbidden_cells:
                child = Person(world=self, parameters=self.parameters)
                self.place(child, category='animal', retry=False, location=coord)
                subject0.last_mated = self.age
                subject1.last_mated = self.age
                debug('{} mated with {} to create {} on tick {}'.format(subject0.uid, subject1.uid, child.uid, self.age))
                return

    def _location(self, retry=False):
        """generate a random valid location"""
        while True:
            x = random.randint(0, self.cols-1)
            y = random.randint(0, self.rows-1)
            if (x,y) in self.forbidden_cells:
                continue
            if (x,y) in self.occupants:
                if retry:
                    continue
                else: 
                    (x,y) = None, None
                    break
            break
        return (x,y)

    def place(self, obj, category, retry=False, location=None):
        """put an entity at a location"""
        if location is None:
            (x,y) = self._location(retry)
        else:
            (x,y) = location
        if (x,y) != (None, None):
            obj.x = x
            obj.y = y
            self.occupants[(x,y)] = obj
            if category == 'animal':
                self.animals.append(obj)
            elif category == 'object':
                self.objects.append(obj)
            else:
                error('placed {} {} with unknown category {}'.format(obj.name, obj, category))
            debug('placed a {} at {},{}'.format(obj.name, obj.x, obj.y))

    def _sanitize_location(self, location):
        """make sure a location is within the bounds of the world"""
        (x,y) = location
        return (x%self.cols, y%self.rows)

    def update(self):
        """update self and all entities"""
        for obj in self.objects:
            obj.update()
        self.move_requests = list()
        self.eat_requests = list()
        for animal in self.animals:
            animal.update()

        for (subject, destination) in self.move_requests:
            (x, y) = self._sanitize_location(destination)
            x = x % self.cols
            y = y % self.rows
            if (x,y) in self.forbidden_cells:
                # drawing here will crash :(
                continue
            if (x,y) in self.occupants:
                # the cell is occupied
                continue
            else:
                debug('moving entity {} from {},{} to {},{}'.format(subject.uid, subject.x, subject.y, x, y))
                old_location = (subject.x, subject.y)
                if old_location in self.occupants:
                    del self.occupants[old_location]
                subject.x = x
                subject.y = y
                self.occupants[(x,y)] = subject

        for (target, eater) in self.eat_requests:
            if target in self.objects:
                self.objects.remove(target)
                del self.occupants[(target.x, target.y)]
                eater.hunger = 0
                eater.last_ate = self.age
                self.eat_requests = [req for req in self.eat_requests if req[1] is not eater and req[0] is not target]
                debug('{} ate {}'.format(eater.uid, target.uid))

        # trim the dead animals
        for animal in self.animals:
            if not animal.alive:
                del self.occupants[(animal.x, animal.y)]
                self.animals.remove(animal)

        # place a food
        # TODO scale food placement rate to world area
        r = random.random()
        if r > 1-self.parameters['food_chance']:
            food = Food()
            self.place(food, category='object')

        self._age += 1

        self.notify()

    def register_observer(self, observer):
        """observers are notified on every update"""
        self.observers.add(observer)

    def notify(self):
        """notify all observers"""
        for observer in self.observers:
            observer.onWorldUpdate(self)
    
    @property
    def population(self):
        return len(self.animals)

    @property
    def age(self):
        return self._age
