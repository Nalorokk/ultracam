from pprint import pprint
import cv2
import threading
import time
import argparse
import os
import os.path
import datetime
import numpy as np
import ctypes
import json


import shared
import web
import opencv






def processStream(name, url):
    shared.logger.debug('processStream thread started')

    if(shared.args.debug is None):
        counter = 0
        err = 0
        cap = cv2.VideoCapture(url)
        while True:
            ret, frame = cap.read()
            if(ret):
                counter = counter + 1
                shared.framebuffer[name] = frame
            else:
                shared.logger.debug('Not recieved frame #'+str(counter)+' on name: '+name)
                err = err + 1
                
                if(err > 50):
                    shared.logger.debug('Trying to restart stream')
                    shared.increase_counter('stream_resets')
                    cap.release()
                    err = 0
                    counter = 0
                    time.sleep(10)
                    cap = cv2.VideoCapture(url)
    
    else:
        with open(shared.args.debug, mode='rb') as file:
            shared.framebuffer[name] = file.read()
            shared.logger.debug('Loaded image as stream output')



def init_processnamehack():
    LIB = 'libcap.so.2'
    try:
        libcap = ctypes.CDLL(LIB)
    except OSError:
        print(
            'Library {} not found. Unable to set thread name.'.format(LIB)
        )
    else:
        def _name_hack(self):
            # PR_SET_NAME = 15
            libcap.prctl(15, self.name.encode())
            threading.Thread._bootstrap_original(self)

        threading.Thread._bootstrap_original = threading.Thread._bootstrap
        threading.Thread._bootstrap = _name_hack


if __name__ == "__main__":
    shared.logger.info('Ultracam startup')
    nice = os.nice(5)
    shared.logger.info('nice level: {}'.format(nice))

    init_processnamehack()

    for stream in shared.config['streams']:
        threading.Thread(target=processStream, name=stream['label'], args=(stream['label'], stream['url'],), daemon=True).start()
    
    threading.Thread(target=opencv.processFrame, name="opencv", daemon=True).start()
    #tg.begin()
    web.begin()
    print('Main end')

