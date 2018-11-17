import curses
from curses import wrapper
import logging
from logging import debug, error
import operator
import random
import sys
from time import sleep

current_uid = 0
def get_uid():
    global current_uid
    u = current_uid
    current_uid += 1
    return u

class Object:
    def __init__(self):
        self.uid = get_uid()
        self.deltas = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]

class Person(Object):
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

class Food(Object):
    def __init__(self):
        super().__init__()
        self.name = 'Food'
        self.ch = '.'
        self.x = None
        self.y = None

    def update(self):
        pass

class World(Object):
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
        self.move_requests.append((subject, destination))

    def eat(self, target, eater):
        self.eat_requests.append((target, eater))

    def reproduce(self, subject0, subject1):
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
        (x,y) = location
        return (x%self.cols, y%self.rows)

    def update(self):
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
        self.observers.add(observer)

    def notify(self):
        for observer in self.observers:
            observer.onWorldUpdate(self)
    
    @property
    def population(self):
        return len(self.animals)

    @property
    def age(self):
        return self._age

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

def make_windows():
    lines = curses.LINES-1
    cols = curses.COLS-1
    debug('lines = {} cols = {}'.format(lines, cols))

    stats_height = lines
    stats_width = 16
    stats_win = curses.newwin(stats_height, stats_width, 0, 0)
    stats_win.clear()
    for line in range(stats_height):
        for col in range(stats_width-1):
            stats_win.addch(line, col, 'x')
    stats_win.refresh()

    world_height = lines
    world_width = cols - stats_width 
    world_win = curses.newwin(world_height, world_width, 0, stats_width)
    return (stats_win, world_win)

def main(stdscr):
    parameters = get_parameters()
    curses.curs_set(False)
    (stats_win, world_win) = make_windows()
    screen = Screen(stats_win, world_win)
    (height, width) = world_win.getmaxyx()
    while True:
        world = World(lines=height, cols=width, parameters=parameters)
        world.register_observer(screen)
        period = parameters['tick_seconds']
        while (world.population > 0):
            world.update()
            if period:
                sleep(period)

def get_parameters():
    parameters = dict()
    parameters['initial_population'] = 10
    parameters['initial_food'] = 20
    parameters['max_population'] = 200
    parameters['max_age'] = 200
    parameters['fertility'] = 0.5
    parameters['food_chance'] = 0.5
    parameters['hunger_threshold'] = 75
    parameters['starvation_threshold'] = 100
    parameters['tick_seconds'] = 0.01
    return parameters

logging.basicConfig(filename='log', filemode='w', level=logging.DEBUG)
wrapper(main)
