import curses
from curses import wrapper
import logging
from logging import debug
import random
from time import sleep

class LilDude:
    def __init__(self, x, y):
        self.alive = True
        self.age = 0
        self.ch = 'O'
        self.x = x
        self.y = y
        self.observers = set()

    def update(self):
        self.age += 1
        if self.age > 400:
            self.alive = False
        r = random.random()
        if r < 0.25:
            self.y = self.y - 1
        elif r < 0.5:
           self.y = self.y + 1
        elif r < 0.75:
            self.x = self.x - 1
        else:
            self.x = self.x + 1

class World:
    def __init__(self, lines, cols, population=1):
        self.lines = lines
        self.cols = cols
        self.population_cap = 200

        self.objects = list()
        for n in range(population):
            y = random.randint(0, lines)
            x = random.randint(0, cols)
            lil_dude = LilDude(x, y)
            self.objects.append(lil_dude)

        self.observers = set()

    def update(self):
        for obj in self.objects:
            obj.update()
            self._keep_on_map(obj)

        self.objects = [obj for obj in self.objects if obj.alive]

        # look for collisions
        parents = self.objects
        for n in range(len(parents)):
            for m in range(n+1, len(parents)):
                if parents[n].x == parents[m].x and parents[n].y == parents[m].y:
                    debug('collision at {} {}'.format(parents[n].x, parents[n].y))
                    if len(self.objects) < self.population_cap:
                        r = random.random()
                        if r > 0.8:
                            child = LilDude(parents[n].x, parents[n].y)
                            self.objects.append(child)
                            debug('creating child at {} {}, population is {}'.format(parents[n].x, parents[n].y, len(self.objects)))
        self.notify()

    def _keep_on_map(self, obj):
        if obj.y < 0:
            obj.y = self.lines
        if obj.y > self.lines:
            obj.y = 0
        if obj.x < 0:
            obj.x = self.cols
        if obj.x > self.cols:
            obj.x = 0

    def register_observer(self, observer):
        self.observers.add(observer)

    def notify(self):
        for observer in self.observers:
            observer.onWorldUpdate(self.objects)
    
    @property
    def population(self):
        return len(self.objects)

class Screen:
    def __init__(self, scr):
        self.scr = scr

    def onWorldUpdate(self, objects):
        self.scr.clear()
        for obj in objects:
            if (obj.x, obj.y) != (92, 17): # TODO fix this hack
                debug('drawing object at {} {}'.format(obj.x, obj.y))
                self.scr.addstr(obj.y, obj.x, obj.ch)
        self.scr.refresh()

def main(stdscr):
    curses.curs_set(False)
    lines = curses.LINES-1
    cols = curses.COLS-1
    debug('lines = {} cols = {}'.format(lines-1, cols-1))

    world = World(lines=lines, cols=cols, population=5)
    screen = Screen(stdscr)
    world.register_observer(screen)
    tick = 0
    while world.population > 0:
        debug('tick {}'.format(tick))
        tick += 1
        world.update()
        #sleep(0.1)

logging.basicConfig(filename='log', filemode='w', level=logging.DEBUG)
wrapper(main)

