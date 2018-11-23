import curses
from curses import wrapper
import logging
from logging import debug, error
import operator
import random
import sys
from time import sleep
import curses

from entity import Entity
from world import World
from screen import Screen
from food import Food

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
