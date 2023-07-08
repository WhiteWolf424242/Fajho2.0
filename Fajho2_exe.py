# -*- coding: utf-8 -*-
import os
import FHdisplay
#import FHmeasurement
#import FHutil
#import FHeval
import code
import multiprocessing
from datetime import datetime
import time


# todo: add argument handler

version = "2.0"
'''
def pollDesperateMeasures():
    while(datetime.now().strftime("%H:%M") != "21:40"):
        time.sleep(1)
    print("Desperate times call for desperate measures...")
    return 0


proc = {}
proc[0] = multiprocessing.Process(target=pollDesperateMeasures)
proc[0].start()
'''

print("Fajhő program v"+str(version))
display = FHdisplay.DisplayWindow()


code.interact(local=locals())