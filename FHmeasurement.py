# -*- coding: utf-8 -*-
import os
import FHutil
import time
import numpy as np
import re

class Measurement:
    x,y,heater,Uarr = [],[],[],[]
    Ts = []
    bTs = False

    bBase = False
    base_a, base_b = 0,0
    base_start, base_end = 0,0
    Dbase_a = 0
    bMain = False
    main_a, main_b = 0,0
    Dmain_a = 0
    main_start, main_end = 0,0
    main_a_corr = 0
    Dmain_a_corr = 0
    bExp = False
    exp_A, exp_b, exp_c = 0,0,0
    exp_start, exp_end = 0,0
    Dexp_b = 0
    bInt = False
    bMainCorrected = False

    bBaseSpline = False
    basespline = None

    bMainExp = False
    mainexp_A, mainexp_b, mainexp_c = 0,0,0
    Dmainexp_b = 0
    mainexp_start, mainexp_end = 0,0

    bBaseExp = False
    baseexp_A, baseexp_b, baseexp_c = 0,0,0

    t_beejt = False

    R = 4.60
    DR = 0.01

    bCalib = False
    Cp = 0
    dCp = 0
    alfa = 0
    dalfa = 0

    bEpszilonVesszo = False
    ev = 0

    directory = ""

    def __init__(self, path):
        self.open(path)

    def open(self, path):
        pathtrunc = path
        while(True):
            if(pathtrunc[-1] == '/'):
                self.directory = pathtrunc
                break
            else:
                pathtrunc = pathtrunc[:-1]
            
            if(len(pathtrunc) <= 0):
                print("Error while recursing for directory")
                return

        # workaround: first log message doesn't seem to go out, if log does not exist, create it
        if(not os.path.exists(self.directory+"OUTfajho_fitlog.dat")):
            with open(self.directory+"OUTfajho_fitlog.dat", "a") as f:
                print("", file=f)

        try:
            data0 = np.loadtxt(path,skiprows=2)
        except Exception as e:
            print("Could not load file")
            return

        with open(path) as f:
            R_line = f.readline()
            self.R = float(re.sub("[^\d\.]", "", R_line))

        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        self.log("\nMegnyitva: "+path+" at ["+str(current_time)+"]\n")
        print("Megnyitva: "+path)

        try:
            os.chdir(self.directory)
            #print("Current working directory: {0}".format(os.getcwd()))
        except FileNotFoundError:
            print("Directory: {0} does not exist".format(self.directory))
        except NotADirectoryError:
            print("{0} is not a directory".format(self.directory))
        except PermissionError:
            print("You do not have permissions to cd to {0}".format(self.directory))

        if(os.path.exists(self.directory+".fh_config")):
            calin = np.loadtxt(self.directory+".fh_config",skiprows = 1)
            self.Cp = calin[0]
            self.dCp = calin[1] / self.Cp
            self.alfa = calin[2]
            self.dalfa = calin[3] / self.alfa
            self.bCalib = True
            print("Kaloriméter kalibrációs paraméterek:")
            print("Cp = ("+str(self.Cp)+" +/- "+str(self.dCp*self.Cp)+") J/K")
            print("Alfa = ("+str(self.alfa)+" +/- "+str(self.dalfa*self.alfa)+") W/K")

        if(os.path.exists(self.directory+"OUTfajho_beejtepszilon.dat")):
            evin = np.loadtxt(self.directory+"OUTfajho_beejtepszilon.dat",skiprows = 1)
            self.ev = evin
            self.bEpszilonVesszo = True
            print("Existing epszilon' found:")
            print("ev = "+str(self.ev)+" 1/s")

        self.x,self.y,self.heater,self.Uarr = FHutil.process_data(data0)

        
    def log(self,text):
        with open(self.directory+"OUTfajho_fitlog.dat", "a") as f:
            print(text, file=f)




    def fitreport(self,params, covs):
        perr = np.sqrt(np.diag(covs))
        print("Final set of parameters            Asymptotic Standard Error: ")
        print("=======================            ==========================")
        for i in range(len(params)):
            print("Param-"+str(i)+":   "+str(params[i])+"      +/-   "+str(perr[i])+"      ("+ f'{abs(perr[i]/params[i]*100):.3e}'+"%)")
        with open(self.directory+"OUTfajho_fitlog.dat", "a") as f:
            print("Final set of parameters            Asymptotic Standard Error: ",file=f)
            print("=======================            ==========================",file=f)
            for i in range(len(params)):
                print("Param-"+str(i)+":   "+str(params[i])+"      +/-   "+str(perr[i])+"      ("+ f'{abs(perr[i]/params[i]*100):.3e}'+"%)",file=f)