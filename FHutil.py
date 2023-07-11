# -*- coding: utf-8 -*-
import os
import easygui
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import FHmeasurement

def process_data(data_in):
    t = []
    T = []
    heater = []
    Uarr = []
    for i in range(len(data_in)):
        t.append(data_in[i][0])
        T.append(data_in[i][1])
        heater.append(data_in[i][3])
        Uarr.append(data_in[i][4])
    return t,T,heater,Uarr


def new(*args):
    if(len(args)==0):
        path = easygui.fileopenbox(filetypes=[["*","All files"],["*.*","All files"]]) 
    else:
        path = args[0]
    if(path):
        return FHmeasurement.Measurement(path)
    else:
        print("Error <FHutil.new>: no file found in path")
    return False



def flin(x, a, b):
    return a*x+b

def fexp(x,A,b,c):
    return A*np.exp(-b*x)+c

def trapcalc(x,y):
    sum = 0
    for i in range(len(x)-1):
        if(y[i] < y[i+1]):
            sum += y[i] * (x[i+1]-x[i])  +  (y[i+1]-y[i]) * (x[i+1]-x[i])/2
        else:
            sum += y[i+1] * (x[i+1]-x[i])  +  (y[i]-y[i+1]) * (x[i+1]-x[i])/2
    return sum


def trapadd(sum, x0, y0, x1, y1):
    if(y0 < y1):
        return sum + y0 * (x1-x0)  +  (y1-y0) * (x1-x0)/2
    return sum + y1 * (x1-x0)  +  (y0-y1) * (x1-x0)/2

def getheatingdata(meas):
    act = False
    start = 0
    end = 0
    Uact = []
    for i in range(len(meas.x)):
        if meas.Uarr[i] < 0.5 and act:
            end = meas.x[i]
            break

        if meas.Uarr[i] > 0.5 and not act:
            start = meas.x[i]
            act = True

        if act:
            Uact.append(meas.Uarr[i])

    # turnon workaround
    counts = 0
    av = np.average(Uact)
    retake = True
    while(retake):
        for i in range(len(Uact)):
            if(Uact[i] < av - 0.1 or Uact[i] > av + 0.1):
                counts += 1
                del Uact[i]
                break
        else:
            retake = False


    return end - start, np.average(Uact), np.std(Uact)
