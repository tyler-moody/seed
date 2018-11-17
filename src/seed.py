import curses
from curses import wrapper
import logging
from logging import debug
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

class LilDude(Object):
    def __init__(self, x, y, world, parameters):
        super().__init__()
        self.alive = True
        self._age = 0
        self.hunger = 0
        self.ch = 'O'
        self.x = x
        self.y = y
        self.hunger_threshold = parameters['hunger_threshold']
        self.starvation_threshold = parameters['starvation_threshold']
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

        r = random.random()
        if r < 0.25:
            delta = (0,-1)
        elif r < 0.5:
            delta = (0, 1)
        elif r < 0.75:
            delta = (1, 0)
        else:
            delta = (-1, 0)
        coordinate = tuple(map(operator.add, delta, (self.x, self.y)))
        self.world.move(self, coordinate)

    def eat_food_within_reach(self):
        deltas = [(-1, 0), (-1, -1), (0, 1), (1, 1)]
        coordinates = [tuple(map(operator.add, (self.x, self.y), delta)) for delta in deltas]
        for coord in coordinates:
            if coord in self.world.occupants:
                target = self.world.occupants[coord]
                if type(target) == Food:
                    self.world.eat(target, self)

class Food(Object):
    def __init__(self, x, y):
        super().__init__()
        self.ch = '.'
        self.x = x
        self.y = y
        debug('created a Food at ({},{})'.format(x, y))

    def update(self):
        pass

class World(Object):
    def __init__(self, lines, cols, population, parameters):
        debug('creating world size lines {} cols {}'.format(lines, cols))
        super().__init__()
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
        for n in range(population):
            (x,y) = self._location()
            lil_dude = LilDude(x, y, world=self, parameters=self.parameters)
            self.occupants[(x,y)] = lil_dude
            self.animals.append(lil_dude)

        self.observers = set()

    def _location(self):
            x = random.randint(0, self.cols-1)
            y = random.randint(0, self.rows-1)
            while (x,y) in self.occupants or (x,y) in self.forbidden_cells:
                x = random.randint(0, self.cols-1)
                y = random.randint(0, self.rows-1)
            return (x,y)

    def move(self, subject, destination):
        self.move_requests.append((subject, destination))

    def eat(self, target, eater):
        self.eat_requests.append((target, eater))

    def update(self):
        for obj in self.objects:
            obj.update()
        self.move_requests = list()
        self.eat_requests = list()
        for animal in self.animals:
            animal.update()
        for (subject, destination) in self.move_requests:
            (x, y) = destination
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
                self.eat_requests = [req for req in self.eat_requests if req[1] is not eater]

        # trim the dead animals
        for animal in self.animals:
            if not animal.alive:
                del self.occupants[(animal.x, animal.y)]
                self.animals.remove(animal)

        # look for collisions
#        parents = self.animals
#        for n in range(len(parents)):
#            for m in range(n+1, len(parents)):
#                if parents[n].x == parents[m].x and parents[n].y == parents[m].y:
#                    debug('collision at {} {}'.format(parents[n].x, parents[n].y))
#                    if len(self.animals) < self.parameters['population_cap']:
#                        r = random.random()
#                        if r > self.parameters['fertility']:
#                            child = LilDude(parents[n].x, parents[n].y)
#                            self.animals.append(child)
#                            debug('creating child at {} {}, population is {}'.format(parents[n].x, parents[n].y, len(self.animals)))
#
        # place a food
        r = random.random()
        if r > 1-self.parameters['food_chance']:
            (x,y) = self._location()
            food = Food(x,y)
            self.occupants[(x,y)] = food
            self.objects.append(food)

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
    initial_population = parameters['initial_population']
    while True:
        world = World(lines=height, cols=width, population=initial_population, parameters=parameters)
        world.register_observer(screen)
        period = parameters['tick_seconds']
        while (world.population > 0):
            world.update()
            if period:
                sleep(period)

def get_parameters():
    parameters = dict()
    parameters['initial_population'] = 10
    parameters['max_population'] = 200
    parameters['max_age'] = sys.maxsize
    parameters['fertility'] = 0.8
    parameters['food_chance'] = 0.2
    parameters['hunger_threshold'] = 50
    parameters['starvation_threshold'] = 100
    parameters['tick_seconds'] = None
    return parameters

logging.basicConfig(filename='log', filemode='w', level=logging.DEBUG)
wrapper(main)
