import curses
from curses import wrapper
import logging
from logging import debug
import random
from time import sleep

class LilDude:
    def __init__(self, x, y):
        self.alive = True
        self._age = 0
        self.ch = 'O'
        self.x = x
        self.y = y
        self.observers = set()

    def update(self):
        self._age += 1
        if self._age > 300:
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
        self._age = 0

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

        self._age += 1

        self.notify()

    def _keep_on_map(self, obj):
        if obj.y < 0:
            obj.y = self.lines-1
        elif obj.y > self.lines-1:
            obj.y = 0
        if obj.x < 0:
            obj.x = self.cols-1
        elif obj.x > self.cols-1:
            obj.x = 0

        # TODO fuck this stupid hack
        if obj.y == self.lines-1 and obj.x == self.cols-1:
            obj.x = self.cols-2
            obj.y = self.lines-2

    def register_observer(self, observer):
        self.observers.add(observer)

    def notify(self):
        for observer in self.observers:
            observer.onWorldUpdate(self)
    
    @property
    def population(self):
        return len(self.objects)

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
        self.stat_scr.refresh()

        self.world_scr.clear()
        for obj in world.objects:
            debug('drawing object at {} {}'.format(obj.x, obj.y))
            self.world_scr.addstr(obj.y, obj.x, obj.ch)
        self.world_scr.refresh()

def main(stdscr):
    curses.curs_set(False)
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
    world_width = cols - stats_width - 4
    debug('world size lines {} cols {}'.format(world_height, world_width))
    world_win = curses.newwin(world_height, world_width, 0, stats_width)

    world = World(lines=world_height, cols=world_width, population=10)
    screen = Screen(stats_win, world_win)
    world.register_observer(screen)
    tick = 0
    while world.population > 0:
        debug('tick {}'.format(tick))
        tick += 1
        world.update()

logging.basicConfig(filename='log', filemode='w', level=logging.DEBUG)
wrapper(main)

