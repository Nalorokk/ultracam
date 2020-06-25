from __future__ import print_function

import os
import time
from sys import getsizeof, stderr
from itertools import chain
from collections import deque

import utils

#import psutil as psutil

try:
    from reprlib import repr
except ImportError:
    pass

import argparse
import json
import logging
import sys


def total_size(o, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                   }
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:       # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


framebuffer = {}
stats = {}
frame_stats = {}

stopStreams = False


ap = argparse.ArgumentParser()
ap.add_argument('-d', '--debug', required=False, help = 'path to input image')
ap.add_argument('-od', '--outputdir', required=False, help = 'path to output folder', default = 'output')
ap.add_argument('-c', '--config', required=False, help = 'path to yolo config file', default = 'cfg/yolov3.cfg')
ap.add_argument('-w', '--weights', required=False, help = 'path to yolo pre-trained weights', default = 'cfg/yolov3.weights')
ap.add_argument('-cl', '--classes', required=False, help = 'path to text file containing class names',  default = 'cfg/yolov3.txt')
ap.add_argument('-ic', '--invertcolor', required=False, help = 'invert RGB 2 BGR',  default = 'false')
args = ap.parse_args()

if(os.path.exists('config.json')):
    with open('config.json') as f:
        try:
            config = json.load(f)
        except:
            config = {}
            config['streams'] = []
else:
    config = {}
    config['streams'] = []

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#if (logger.hasHandlers()):
 #   logger.handlers.clear()

fileHandler = logging.FileHandler('ultracam.log')
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

def add_framestat(name, stat):
    stats = []
    if(name in frame_stats):
        stats = frame_stats[name]

    stats.append({'time': time.time(), 'stat': stat})
    frame_stats[name] = stats

def get_size():
    #process = psutil.Process(os.getpid())
    #return process.memory_info().rss / 1024 / 1024
    return total_size(framebuffer) / 1024

def get_counter(name):
    currentValue = 0

    if(name in stats):
        currentValue = stats[name]

    return currentValue

def increase_counter(name, value = 1):
    currentValue = get_counter(name)

    stats[name] = currentValue + value
