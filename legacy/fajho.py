# -*- coding: utf-8 -*-
import os
import matplotlib.pyplot as plt
plt.ion()
from scipy.optimize import curve_fit
import numpy as np
import code
import re
import multiprocessing
import time
import easygui

version = 1.5
print("Fajho v"+str(version))
print("Run man() to see manual")

fig = None
cid = None
eventX = 0
eventY = 0
eventReceived = False

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

beejtAtlag = -1
dIntegral = -1

bCalib = False
Cp = 0
dCp = 0
alfa = 0
dalfa = 0

bEpszilonVesszo = False
ev = 0

directory = ""


autoshow = True
grid = True
scaletodata = True
dualfit = True
fignum_counter = 0

R = 4.60
DR = 0.01


bLegend = False
def legend():
    global bLegend
    bLegend = not bLegend
    if(autoshow):
        show()

def man():
    # work in progress....
    print("Dokumentáció (nem teljes):")
    print("- Függvények:")
    print("    - Fájl megnyitás:")
    print("        new()")
    print("    - Könyvtár váltás:")
    print("        cd()")
    print("")
    print("    - Ábrázolás:")
    print("        s()    [alias: show]")
    print("          - Betöltött adatsor ábrázolása")
    print("        legend()")
    print("          - Ábrafelirat ki/be kapcsolása")
    print("")
    print("    - Illesztések:")
    print("        esz(xmin,xmax)    [alias: eloszakasz]")
    print("          - Előszakasz illesztése xmin és xmax között.")
    print("        fsz(xmin,xmax)    [alias: foszakasz]")
    print("          - Lineáris főszakasz illesztése xmin és xmax között.")
    print("        kfsz(xmin,xmax)")
    print("          - Lineáris főszakasz illesztése xmin és xmax között a korrigált hőmérséklet (T*) görbére.")
    print("        efsz(xmin,xmax)   [alias: expfoszakasz]")
    print("          - [Beejtéses mérésre]. Exponenciális főszakasz illesztése xmin és xmax között. Az eredmény epszilon' paramétert kimenti fájlba. [Feltételek: korrigált hőmérséklet (T*)]")
    print("        usz(xmin,xmax)    [alias: utoszakasz]")
    print("          - Utószakasz exponenciális illesztése xmin és xmax között. Ha a 'dualfit' globális konstans True, akkor automatikusan végrehajtja a df()-et is.")
    print("        df(method='ask') ")
    print("          - Kettős illesztés, az előszakasz exponenciális korrekciójához. Tud exponenciálist vagy spline-t, ha a paraméter 'ask' akkor megkérdezi mi legyen mielőtt illeszt.")
    print("")
    print("        Minden illesztés hívható paraméterek nélkül is, például: esz(). Ekkor az inputról fogja kérni a program a határokat. Minden illesztés eredménye elmentődik a fitlogba.")
    print("")
    print("    - Számolások:")
    print("        korrigaltT()      [alias: kT]")
    print("          - Korrigált hőmérséklet (T*) számolása. Feltételek: előszakasz, utószakasz.")
    print("")
    print("        - Vízérték mérés adatsora:")
    print("            calib()")
    print("              - Vízérték és hőátadási paraméter számolása (kalibráció). Az eredményeket kimenti fájlba, melyet a program minden új fájlbeolvasásnál megpróbál betölteni. [Feltételek: előszakasz, főszakasz, utószakasz.]")
    print("")
    print("        - Beejtéses mérés adatsora:")
    print("            integral(xmin,xmax)")
    print("              - Fajhő számolása xmin és xmax közti integrálból. [Feltételek: kalibráció, előszakasz.]")
    print("            si(xmin,xmax_low, xmax_high)   [alias: serialintegrate]")
    print("              - Az integrál felső határának variálása, xmax_low és xmax_high között minden értékre integrált és fajhőt számol melyet aztán ábrázol a felső határ függvényében. [Feltételek: kalibráció, előszakasz.]")
    print("        - Ráfűtéses mérés adatsora:")
    print("            rafut()")
    print("              - Fajhő számolása a ráfűtés főszakaszából. [Feltételek: kalibráció, előszakasz, főszakasz]")
    print("            rafutteljes(Ts_start)  ")
    print('              - Fajhő számolása a ráfűtés főszakaszából és utószakaszából. ("A régi módszer.") A Ts_start paraméter a T* korrigált hőmérséklet átlagolásának kezdőpontja, ha nincs megadva akkor az alapértelmezett az utószakasz illesztés kezdőpontja. [Feltételek: kalibráció, előszakasz, főszakasz, utószakasz, korrigált hőmérséklet, korábbi beejtéses mérés efsz() illesztése]')





def flin(x, a, b):
    return a*x+b

def fexp(x,A,b,c):
    return A*np.exp(-b*x)+c



def do_fit(x,y,xmin,xmax, func = flin):
    xf = []
    yf = []
    for i in range(len(x)):
        if(xmin <= x[i] <= xmax):
            xf.append(x[i])
            yf.append(y[i])


    return curve_fit(func, xf, yf)


def getK():
    if(not bEpszilonVesszo or not bCalib):
        return False
    return ev/(ev - alfa/Cp)




def fitreport(params, covs):
    perr = np.sqrt(np.diag(covs))
    print("Final set of parameters            Asymptotic Standard Error: ")
    print("=======================            ==========================")
    for i in range(len(params)):
        print("Param-"+str(i)+":   "+str(params[i])+"      +/-   "+str(perr[i])+"      ("+ f'{abs(perr[i]/params[i]*100):.3e}'+"%)")
    with open(directory+"OUTfajho_fitlog.dat", "a") as f:
        print("Final set of parameters            Asymptotic Standard Error: ",file=f)
        print("=======================            ==========================",file=f)
        for i in range(len(params)):
            print("Param-"+str(i)+":   "+str(params[i])+"      +/-   "+str(perr[i])+"      ("+ f'{abs(perr[i]/params[i]*100):.3e}'+"%)",file=f)




def onclick(event):
    global eventX, eventY, eventReceived
    global fig, cid
    
    if(event.dblclick):
        eventX = event.xdata
        eventY = event.ydata
        fig.canvas.mpl_disconnect(cid)
        eventReceived = True

        #endEvent("click")
        return True
    return False


def rangeselectorKeyboard(text):
    global eventX, eventY, eventReceived
    value = input(text)

    eventX = value
    eventReceived = True

    #endEvent("keyboard")

def rangeselectorMouseActivate():
    global cid
    global fig
    cid = fig.canvas.mpl_connect('button_press_event', onclick)


#def endEvent(source):
    #if(source == "click"):



def createRangeEvent(text):
    global eventReceived

    import threading
    rangeselectorMouseActivate()
    proc = threading.Thread(target=rangeselectorKeyboard, args=(text,))
    proc = multiprocessing.Process(target=rangeselectorKeyboard, args=(text,))
    proc = multiprocessing.Process(target=rangeselectorKeyboard, args=(text))
    proc.start()


    while(not eventReceived):
        time.sleep(0.1)

    if(proc.is_alive()):
        proc.terminate()
    
    xmin = eventX
    eventReceived = False
    return xmin




def fitbase(*args):
    global bBase
    global base_a
    global Dbase_a
    global base_b
    global base_start
    global base_end

    if(len(args) == 2):
        xmin = args[0]
        xmax = args[1]
    else:
        xmin = float(input("Fit start: "))
        xmax = float(input("Fit end: "))
    
    base_start = xmin
    base_end = xmax
    params, covs = do_fit(x,y,xmin,xmax)
    log("\nBase fit in x["+str(xmin)+"; "+str(xmax)+"],   y = p0*x + p1")
    fitreport(params, covs)

    bBase = True
    base_a = params[0]
    base_b = params[1]

    perr = np.sqrt(np.diag(covs))
    Dbase_a = perr[0]

    if(autoshow):
        show()
fb = fitbase
eloszakasz = fitbase
esz = fitbase



def fitmain(*args):
    global bMain
    global main_a
    global Dmain_a
    global main_b
    global main_start
    global main_end
    global main_a_corr
    global Dmain_a_corr

    if(not bBase):
        print("Error: missing base fit")
        return

    if(bMainCorrected):
        sure = input("Are you sure? (yes/no): ")
        if(sure != "yes"):
            return

    if(len(args) == 2):
        xmin = args[0]
        xmax = args[1]
    else:
        xmin = float(input("Fit start: "))
        xmax = float(input("Fit end: "))
    
    main_start = xmin
    main_end = xmax
    params, covs = do_fit(x,y,xmin,xmax)
    log("\nMain fit in x["+str(xmin)+"; "+str(xmax)+"],   y = p0*x + p1")
    fitreport(params, covs)

    bMain = True
    main_a = params[0]
    main_b = params[1]

    perr = np.sqrt(np.diag(covs))
    Dmain_a = perr[0]

    if(bBase):
        main_a_corr = main_a - base_a
        Dmain_a_corr = Dmain_a + Dbase_a


    if(autoshow):
        show()
fm = fitmain
foszakasz = fitmain
fsz = fitmain



def fitmaincorrected(*args):
    global bMainCorrected
    global bMain
    global main_a
    global Dmain_a
    global main_b
    global main_start
    global main_end
    global main_a_corr
    global Dmain_a_corr

    if(not bTs):
        print("Error: missing T* fit")
        return

    if(len(args) == 2):
        xmin = args[0]
        xmax = args[1]
    else:
        xmin = float(input("Fit start: "))
        xmax = float(input("Fit end: "))
    
    main_start = xmin
    main_end = xmax
    params, covs = do_fit(x,Ts,xmin,xmax)
    log("\nMain fit in x["+str(xmin)+"; "+str(xmax)+"] onto T*,   y = p0*x + p1")
    fitreport(params, covs)

    bMain = True
    bMainCorrected = True
    main_a = params[0]
    main_b = params[1]

    perr = np.sqrt(np.diag(covs))
    Dmain_a = perr[0]

    if(bBase):
        main_a_corr = main_a - base_a
        Dmain_a_corr = Dmain_a + Dbase_a

    if(autoshow):
        show()
kfsz = fitmaincorrected
fszk = fitmaincorrected
fmc = fitmaincorrected
fcm = fitmaincorrected




def fitexp(*args):
    global bExp
    global exp_A
    global exp_b
    global Dexp_b
    global exp_c
    global exp_start
    global exp_end


    if(not bBase):
        print("Error: missing base fit")
        return


    if(len(args) == 2):
        xmin = args[0]
        xmax = args[1]
    else:
        xmin = float(input("Fit start: "))
        xmax = float(input("Fit end: "))
    
    exp_start = xmin
    exp_end = xmax


    xf = []
    yf = []
    for i in range(len(x)):
        if(xmin <= x[i] <= xmax):
            xf.append(x[i])
            yf.append(y[i])
    a_guess = 3.6
    b_guess = 0.001
    c_guess = 20
    params, covs = curve_fit(lambda t, a, b, c: a * np.exp(-b * t) + c, xf, yf, p0=(a_guess, b_guess, c_guess))

    log("\nExponential fit in x["+str(xmin)+"; "+str(xmax)+"],   y = p0*exp(-p1 * x) + p2")
    fitreport(params, covs)
    bExp = True
    exp_A = params[0]
    exp_b = params[1]
    exp_c = params[2]

    perr = np.sqrt(np.diag(covs))
    Dexp_b = perr[1]


    if(autoshow):
        show()


    if(dualfit):
        df()
fe = fitexp
utoszakasz = fitexp
usz = fitexp


'''
# Amugy is global fit kellene ha ilyet akarunk: https://mail.python.org/pipermail/scipy-user/2013-April/034403.html
def globalfit(*args):
    global bExp
    global exp_A
    global exp_b
    global Dexp_b
    global exp_c

    global y #ez meg minek kell

    # fixme: this doesn't work yet


    if(not bBase):
        print("Error: missing base fit")
        return
    if(len(args) == 2):
        xmin = args[0]
        xmax = args[1]
    else:
        xmin = float(input("Fit start: "))
        xmax = float(input("Fit end: "))


    # create datasets and xf sets
    yf_exp = []
    yf_lin = []
    xf_exp = []
    xf_lin = []
    for i in range(len(x)):
        if(base_start <= x[i] <= base_end):
            yf_lin.append(y[i])
            xf_lin.append(x[i])
        if(xmin <= x[i] <= xmax):
            yf_exp.append(y[i])
            xf_exp.append(x[i])


    data = np.array([xf_exp,yf_exp,xf_lin,yf_lin])

    # get starting value for fit
    Tk, DTk = getTk()

    from lmfit import minimize, Parameters, report_fit

    def exponential(x, A, b, c):
        return A * np.exp(-b * x) + c
    def linconst(x, c):
        return c

    def func_dataset(params, func, x):
        amp = params['amp_%i' % (i+1)].value
        tau = params['tau_%i' % (i+1)].value
        lim = params['lim_%i' % (i+1)].value
        if(func == "exp"):
            return exponential(x, amp, tau, lim)
        return linconst(x,lim)

    def objective(params, data):
        resid1 = 0.0*data[1]
        resid2 = 0.0*data[3]
        # make residual per data set
        resid1[:] = data[1, :] - func_dataset(params, "exp", data[0])
        resid2[:] = data[3, :] - func_dataset(params, "lin", data[2])

        return resid1+resid2



    # create sets of parameters, one per data set
    fit_params = Parameters()
    for iy in range(2):
        fit_params.add( 'amp_%i' % (iy+1), value=3.6)
        fit_params.add( 'tau_%i' % (iy+1), value=0.001)
        fit_params.add( 'lim_%i' % (iy+1), value=Tk)

    # but now constrain all values of lim to have the same value
    #for iy in (2, 3, 4, 5):
    fit_params['lim_%i' % 2].expr='lim_1'

    # run the global fit to all the data sets
    result = minimize(objective, fit_params, args=(data))
    report_fit(result)
'''







def getTs(*args):
    global Ts
    global bTs
    if(not bBase):
        print("Error: base fit not found")
        return
    if(not bExp):
        print("Error: exponential fit not found")
        return
    
    if(len(args) == 1):
        startpoint = args[0]
    else:
        startpoint = base_end

    Ts = []

    
    for i in range(len(x)):
        if(x[i] < startpoint):
            Ts.append(y[i])
        else:
            t = x[i]
            xf = []
            yf = []
            for j in range(len(x)):
                if(startpoint <= x[j] <= t):
                    xf.append(x[j])
                    yf.append(y[j])


            Tk = getTkValue(x[j])
            # ez igy garantalja hogy ha van dualfit akkor azt kapjuk, ha nem akkor pedig az exp_limeszt kapjuk vissza

            for j in range(len(xf)):
                yf[j] -= Tk

            Ts.append(y[i] + exp_b*trapcalc(xf,yf))
    bTs = True
    if(autoshow):
        show()
korrigaltT = getTs
kT = getTs
kt = kT


def fitmainexp(*args):
    global bMainExp
    global mainexp_A
    global mainexp_b
    global Dmainexp_b
    global mainexp_c
    global mainexp_start
    global mainexp_end
    global bEpszilonVesszo
    global ev

    if(not bTs):
        print("Main exp must be fit onto T*!")
        return


    if(len(args) == 2):
        xmin = args[0]
        xmax = args[1]
    else:
        xmin = float(input("Fit start: "))
        xmax = float(input("Fit end: "))
    
    mainexp_start = xmin
    mainexp_end = xmax


    xf = []
    yf = []
    for i in range(len(x)):
        if(xmin <= x[i] <= xmax):
            xf.append(x[i])
            yf.append(Ts[i])
    a_guess = -2.44586e+06
    b_guess = 0.0426355
    c_guess = 22.0029
    params, covs = curve_fit(lambda t, a, b, c: a * np.exp(-b * t) + c, xf, yf, p0=(a_guess, b_guess, c_guess))

    log("\nExponential fit (main) in x["+str(xmin)+"; "+str(xmax)+"],   y = p0*exp(-p1 * x) + p2")
    fitreport(params, covs)
    bMainExp = True
    mainexp_A = params[0]
    mainexp_b = params[1]
    mainexp_c = params[2]

    perr = np.sqrt(np.diag(covs))
    Dmainexp_b = perr[1]


    with open(directory+"OUTfajho_beejtepszilon.dat", "w") as f:
        print("# b (ev) [1/s]", file=f)
        print(mainexp_b,file=f)

    bEpszilonVesszo = True
    ev = mainexp_b

    if(autoshow):
        show()
fme = fitmainexp
fem = fitmainexp
expfoszakasz = fitmainexp
foszakaszexp = fitmainexp
efsz = fitmainexp
fsze = fitmainexp





def eszusz(method="ask"):
    global bBaseExp, baseexp_A, baseexp_b, baseexp_c
    global bBaseSpline, basespline

    if(not bBase):
        print("Error in dualfit: missing base fit")
        return
    if(not bExp):
        print("Error in dualfit: missing exp fit")
        return
    
    if(method != "exp" and method != "spline" and method != "e" and method != "s"):
        met = str(input("Dualfit method ('exp'/'spline'): "))
        if(met != "exp" and met != "spline" and met != "e" and met != "s"):
            print("Dualfit canceled")
            return
        method = met


    if(method == "exp" or method == "e"):

        limit = str(input("Exp dualfit method for limit ('fixed'/'free'/'forced'): "))
        if(limit != "fixed" and limit != "forced" and limit != "free"):
            print("Dualfit canceled")
            return

        xf = []
        yf = []
        for i in range(len(x)):
            if(base_start <= x[i] <= base_end):
                xf.append(x[i])
                yf.append(y[i])

            if(limit=="free" or limit == "forced"):
                if(i > len(x) - 10):
                    xf.append(x[i])
                    yf.append(exp_c)

        mp = (exp_c - base_b)/base_a

        a_guess = 3.6
        b_guess = 0.001
        c_guess = exp_c
        #if(mp < base_end):
        #    getav = []
        #    for i in range(len(x)):
        #        if(base_end - 10 <= x[i] <= base_end + 1):
        #            getav.append(y[i])
        #    c_guess = np.average(getav)
        if(limit == "free"):
            params, covs = curve_fit(lambda t, a, b, c: a * np.exp(-b * t) + c, xf, yf, p0=(a_guess, b_guess, c_guess))
            log("\nDual fit: Exponential base correction,   y = p0*exp(-p1 * x) + c")
            print("Dual fit: Exponential base correction,   y = p0*exp(-p1 * x) + c")
        elif(limit == "fixed" or limit == "forced"):
            params, covs = curve_fit(lambda t, a, b: a * np.exp(-b * t) + exp_c, xf, yf, p0=(a_guess, b_guess))
            log("\nDual fit: Exponential base correction [fixed limit],   y = p0*exp(-p1 * x) + "+str(exp_c))
            print("Dual fit: Exponential base correction [fixed limit],   y = p0*exp(-p1 * x) + "+str(exp_c))
        else:
            print("bad argument to 'limit' (free/fixed/forced)")
            return
        fitreport(params, covs)
        bBaseExp = True
        bBaseSpline = False
        baseexp_A = params[0]
        baseexp_b = params[1]
        baseexp_c = params[2] if limit == "free" else exp_c

    elif(method == "spline" or method == "s"):
        tandata_x = []
        tandata_y = []
        #Tkval, DTkval = getTk()
        for i in range(len(x)):
            if base_end - 20 <= x[i] <= base_end:
                tandata_x.append(x[i])
                tandata_y.append(flin(x[i],base_a, base_b))
            if exp_start <= x[i] <= exp_start + 20:
                tandata_x.append(x[i])
                tandata_y.append(exp_c)
        
        from scipy.interpolate import CubicSpline
        basespline = CubicSpline(tandata_x, tandata_y)
        bBaseSpline = True
        bBaseExp = False

        log("Dual fit: Base fit and exponential limit connected with cubic spline")

    if(autoshow):
        show()
df = eszusz
ki = eszusz

def calib(save=True):
    global bCalib
    global Cp
    global dCp
    global alfa
    global dalfa

    if(not bBase):
        print("Error: missing base")
        return
    if(not bMain):
        print("Error: missing main")
        return
    if(not bExp):
        print("Error: missing exp")
        return

    print("R = ("+str(R)+" +/- "+str(DR)+") Ohm")


    # get U
    t, U, DU = getheatingdata()
    print("U = ("+str(U)+" +/- "+str(DU)+") V")

    print("a_corr = ("+str(main_a_corr)+" +/- "+str(Dmain_a_corr)+") K/s")

    print("Beta = ("+str(exp_b)+" +/- "+str(Dexp_b)+") 1/s")
    # get Cp
    Cp = U**2/R/main_a_corr
    dCp = 2*DU/U + DR/R + Dmain_a_corr/main_a_corr
    print("=======================")
    print("Cp = ("+str(Cp)+" +/- "+str(dCp*Cp)+") J/K")

    alfa = exp_b * Cp
    dalfa = dCp + Dexp_b/exp_b
    print("Alfa = ("+str(alfa)+" +/- "+str(dalfa*alfa)+") W/K")
    bCalib = True

    log("\nCalibration data:")
    log("R = ("+str(R)+" +/- "+str(DR)+") Ohm")
    log("U = ("+str(U)+" +/- "+str(DU)+") V")
    log("a_corr = ("+str(main_a_corr)+" +/- "+str(Dmain_a_corr)+") K/s")
    log("Beta = ("+str(exp_b)+" +/- "+str(Dexp_b)+") 1/s")
    log("=======================")
    log("Cp = ("+str(Cp)+" +/- "+str(dCp*Cp)+") J/K")
    log("Alfa = ("+str(alfa)+" +/- "+str(dalfa*alfa)+") W/K\n")


    if(save):
        with open(directory+"OUTfajho_kalibracio.dat", "w") as f:
            print("# Cp [J/K], D(Cp) [J/K], alfa [W/K], D(alfa) [W/K]", file=f)
            print(Cp, dCp*Cp, alfa, dalfa*alfa,file=f)
c = calib
k = calib
kalib = calib
kalibracio = calib
calibrate = calib



def trapcalc(x,y):
    sum = 0
    for i in range(len(x)-1):
        if(y[i] < y[i+1]):
            sum += y[i] * (x[i+1]-x[i])  +  (y[i+1]-y[i]) * (x[i+1]-x[i])/2
        else:
            sum += y[i+1] * (x[i+1]-x[i])  +  (y[i]-y[i+1]) * (x[i+1]-x[i])/2
    return sum



def integrate(*args):
    if(not bCalib):
        print("Error: missing calib")
        return
    if(not bExp):
        print("Error: missing exp fit")
        return
    if(len(args) == 0):
        xmin = float(input("Integral start: "))
        xmax = float(input("Integral end: "))
    elif(len(args) == 2):
        xmin = args[0]
        xmax = args[1]
    else:
        print("Insufficient arguments")
        return

    xf = []
    yf = []
    for i in range(len(x)):
        if(xmin <= x[i] <= xmax):
            xf.append(x[i])
            yf.append(y[i])


    Tt = yf[-1]

    if(not bBase):
        fitbase(0,xmin)


    Tm, DTm = getTm(xmin)

    Tk, DTk = getTk()

    for i in range(len(xf)):
        yf[i] -= getTkValue(xf[i])

    integ = trapcalc(xf,yf)

    cm = (Cp*(Tt - Tk)+alfa*integ)/( Tm-Tt )

    # assuming DTk deviation for T(t) as well, and assuming DI ~ 0
    Dcm = abs((Tt - Tk)/(Tm-Tt))* (dCp*Cp) + abs((alfa*integ + Cp*(Tm - Tk)/(Tm - Tt)**2))*DTk + abs(-Cp/(Tm - Tt))*DTk + abs(integ/(Tm - Tt))*(dalfa*alfa) + abs((Cp*(Tk - Tt) - alfa*integ)/(Tm - Tt)**2)* DTm

    print("Tm = ("+str(Tm)+" +/- "+str(DTm)+") C")
    print("T0 = ("+str(Tk)+" +/- "+str(DTk)+") C")
    print("T(t) = "+str(Tt)+" C")
    print("Integral = "+str(integ)+" Cs")
    print("=======================")
    print("Cm = ("+str(cm)+" +/- "+str(Dcm)+") J/K")

    with open(directory+"OUTfajho_beejtesEgyszeruIntegral.dat", "w") as f:
        print("Tm = ("+str(Tm)+" +/- "+str(DTm)+") C", file=f)
        print("T0 = ("+str(Tk)+" +/- "+str(DTk)+") C", file=f)
        print("T(t) = "+str(Tt)+" C", file=f)
        print("Integral = "+str(integ)+" Cs", file=f)
        print("=======================", file=f)
        print("Cm = ("+str(cm)+" +/- "+str(Dcm)+") J/K", file=f)
integral = integrate




def getTkValue(*args):
    if(not bBase):
        print("Error in getTkValue(): missing base fit")
        return False

    if(len(args) == 1):
        xp = args[0]

        if(bBaseSpline):
            if(xp <= base_end):
                return flin(xp,base_a,base_b)
            elif(xp <= exp_start):
                return float(basespline(xp))
            else:
                return exp_c

        if(bBaseExp):
            return fexp(xp,baseexp_A,baseexp_b,baseexp_c)
        if(bExp):
            return exp_c
        return flin(xp,base_a,base_b)


    aTk = []
    for i in range(len(x)):
        if(base_end - 10 <= x[i] <= base_end + 5):
            aTk.append( flin(x[i], base_a, base_b) )
    return np.average(aTk)

def getTk(*args):
    # ha kell Tk, ehhez kell at least base

    # fv viselkedese:
    # DTk szorast eloszakaszbol veszi
    # ha van beadva x pont neki, akkor ott veszi Tk-t, ha nincs akkor a base_end kornyeken

    if(not bBase):
        print("Error in getTk(): missing base fit")
        return False

    aTk = []
    for i in range(len(x)):
        if(base_start <= x[i] <= base_end):
            aTk.append(y[i])
    DTk = np.std(aTk)

    if(len(args) == 1):
        return getTkValue(args[0]), DTk
    return getTkValue(), DTk




def getTm(position):
    Tm_l = []
    for i in range(len(x)):
        if(position - 10 <= x[i] <= position + 5):
            Tm_l.append(heater[ i ])
    return np.average(Tm_l), np.std(Tm_l)



def serialintegrate(*args):
    global dIntegral
    global beejtAtlag

    if(not bCalib):
        print("Error: missing calib")
        return
    if(not bExp):
        print("Error: missing exp")
        return
    if(not bBase):
        fitbase(0,xmin)

    if(len(args) == 3):
        xmin = args[0]
        xmax1 = args[1]
        xmax2 = args[2]
    else:
        xmin = float(input("Integral start: "))
        xmax1 = float(input("Integral end low: "))
        xmax2 = float(input("Integral end high: "))


    Tm, DTm = getTm(xmin)

    # kell Tk
    Tk = getTkValue()

    integrals = []
    uplims = []
    Tts = []

    for i in range(len(x)):
        if(xmax1 <= x[i] <= xmax2):
            uplims.append(x[i])
            xf = []
            yf = []
            for j in range(len(x)):
                if(xmin <= x[j] <= x[i]):
                    xf.append(x[j])
                    yf.append(y[j])

            # base correction
            for j in range(len(xf)):
                yf[j] -= getTkValue(xf[j])
                #yf[j] -= exp_c

            integ = trapcalc(xf,yf)
            integrals.append(integ)
            Tts.append(y[i])  # yes this is i

    cms = []
    for i in range(len(integrals)):
        cms.append( (Cp*(Tts[i] - Tk)+alfa*integrals[i])/( Tm-Tts[i] ) )

    beejtAtlag = np.average(cms)
    dIntegral = np.std(cms)
    plt.close()
    plt.plot(uplims,cms)
    plt.xlabel("Integral upper limit (s)")
    plt.ylabel(r'$C_{m}$ $(J/K)$')

    with open(directory+"OUTfajho_beejtesSorozatosIntegral.dat", "w") as f:
        print("# t [s], Cm [J/K]", file=f)
        for i in range(len(uplims)):
            print(uplims[i], cms[i], file=f)

ismeteltintegral = serialintegrate
repeatintegrate = serialintegrate
si = serialintegrate
ii = serialintegrate


def beejtes():



beejt = beejtes

def beejtesregi(*args):
    if(not bCalib):
        print("Error: missing calibration")
        return
    if(not bBase):
        print("Error: missing base fit")
        return
    if(not bMainExp):
        print("Error: missing main fit")
        return
    if(not bExp):
        print("Error: missing exp fit")
        return
    if(not bTs):
        print("Error: missing T*")
        return

    if(len(args) == 1):
        Tsint_start = args[0]
    else:
        Tsint_start = exp_start
    Tsav, DTsav = getAvTs(Tsint_start)


    Tk, DTk = getTk()
    Tm, DTm = getTm(mainexp_start)

    K = getK()
    Tms = Tk + K*(Tsav - Tk)
    # deltaK = e0/ev*(delta e0 + delta ev) = e0/ev*6%
    deltaK = (alfa/Cp) / ev * 0.06 
    DTms = K*DTsav + (K - 1)*DTk + (Tsav - Tk)*deltaK
    cm = Cp*(Tsav- Tk)/(Tm - Tms)

    dcm = dCp + (DTsav + DTk)/(Tsav - Tk) + (DTm + DTsav)/(Tm - Tsav)

    print("Tm = ("+str(Tm)+" +/- "+str(DTm)+") C")
    print("Tm* = ("+str(Tms)+" +/- "+str(DTms)+") C")
    print("Tk = ("+str(Tk)+" +/- "+str(DTk)+") C")
    print("T* = ("+str(Tsav)+" +/- "+str(DTsav)+") C")
    print("=======================")
    print("Cm = ("+str(cm)+" +/- "+str(dcm * cm)+") J/K")

    with open(directory+"OUTfajho_beejtesRegi.dat", "w") as f:
        print("Tm = ("+str(Tm)+" +/- "+str(DTm)+") C", file=f)
        print("Tm* = ("+str(Tms)+" +/- "+str(DTms)+") C", file=f)
        print("Tk = ("+str(Tk)+" +/- "+str(DTk)+") C", file=f)
        print("T* = ("+str(Tsav)+" +/- "+str(DTsav)+") C", file=f)
        print("=======================")
        print("Cm = ("+str(cm)+" +/- "+str(dcm * cm)+") J/K", file=f)


def rafut():
    if(not bCalib):
        print("Error: missing calib")
        return
    if(not bBase):
        print("Error: missing base fit")
        return
    if(not bMain):
        print("Error: missing main fit")
        return

    print("R = ("+str(R)+" +/- "+str(DR)+") Ohm")


    # get U
    t, U, DU = getheatingdata()
    print("\nCalculating Cm data:")
    print("R = ("+str(R)+" +/- "+str(DR)+") Ohm")
    print("U = ("+str(U)+" +/- "+str(DU)+") V")
    print("a_corr = ("+str(main_a_corr)+" +/- "+str(Dmain_a_corr)+") K/s")
    # get Ck
    Ck = U**2/R/main_a_corr
    dCk = 2*DU/U + DR/R + Dmain_a_corr/main_a_corr
    print("=======================")
    print("Ck = ("+str(Ck)+" +/- "+str(dCk*Ck)+") J/K")
    print("Cm = ("+str(Ck-Cp)+" +/- "+str(dCk*Ck + dCp*Cp)+") J/K")

    log("\nCalculating Cm data:")
    log("R = ("+str(R)+" +/- "+str(DR)+") Ohm")
    log("U = ("+str(U)+" +/- "+str(DU)+") V")
    log("a_corr = ("+str(main_a_corr)+" +/- "+str(Dmain_a_corr)+") K/s")
    log("=======================")
    log("Ck = ("+str(Ck)+" +/- "+str(dCk*Ck)+") J/K")
    log("Cm = ("+str(Ck-Cp)+" +/- "+str(dCk*Ck + dCp*Cp)+") J/K")


    with open(directory+"OUTfajho_rafutes.dat", "w") as f:
        print("# Ck [J/K], D(Ck) [J/K], Cm [J/K], D(Cm) [J/K]", file=f)
        print(Ck, dCk*Ck, Ck-Cp, dCk*Ck + dCp*Cp,file=f)
r = rafut
rafutes = rafut
rafuteses = rafut



def getheatingdata():
    act = False
    start = 0
    end = 0
    Uact = []
    for i in range(len(x)):
        if Uarr[i] < 0.5 and act:
            end = x[i]
            break

        if Uarr[i] > 0.5 and not act:
            start = x[i]
            act = True

        if act:
            Uact.append(Uarr[i])

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


def rafutteljes(*args):
    if(not bCalib):
        print("Error: missing calib")
        return
    if(not bEpszilonVesszo):
        print("Error: epsilon' not found")
        return
    if(not bBase):
        print("Error: base fit not found")
        return
    if(not bTs):
        print("Error: T* fit not found")
        return
    
    if(len(args) == 1):
        Tsint_start = args[0]
    else:
        Tsint_start = exp_start


    # cm = z/K
    #K = ev/(ev-e0),  e0: b kalib, ev: b beejtes
    # z = Q(Ts-Tk) - v

    t, U, DU = getheatingdata()
    Q = U**2/R *t
    dQ = 2*DU/U + DR/R
    Tk, DTk = getTk()

    Tsav, DTsav = getAvTs(Tsint_start)

    z = Q/(Tsav - Tk) - Cp

    Dtort = Q/(Tsav - Tk) * (dQ + (DTsav + DTk)/(Tsav - Tk))
    Dz = Dtort + dCp*Cp

    dK = 0.06 * (alfa/Cp)/ev 
    cm = z/getK()
    dcm = Dz/z + dK
    

    print("\nCalculating Cm data:")
    print("R = ("+str(R)+" +/- "+str(DR)+") Ohm")
    print("U = ("+str(U)+" +/- "+str(DU)+") V")
    print("t = "+str(t)+" s")
    print("Q = ("+str(Q)+" +/- "+str(dQ*Q)+") J")
    print("Tk = ("+str(Tk)+" +/- "+str(DTk)+") C")
    print("T* = ("+str(Tsav)+" +/- "+str(DTsav)+") C")
    print("=======================")
    print("Cm = ("+str(cm)+" +/- "+str(dcm*cm)+") J/K")
    print("Cm [K=1] = ("+str(z)+" +/- "+str(Dz)+") J/K")


    log("\nCalculating Cm data:")
    log("R = ("+str(R)+" +/- "+str(DR)+") Ohm")
    log("U = ("+str(U)+" +/- "+str(DU)+") V")
    log("t = "+str(t)+" s")
    log("Q = ("+str(Q)+" +/- "+str(dQ*Q)+") J")
    log("Tk = ("+str(Tk)+" +/- "+str(DTk)+") C")
    log("T* = ("+str(Tsav)+" +/- "+str(DTsav)+") C")
    log("=======================")
    log("Cm = ("+str(cm)+" +/- "+str(dcm*cm)+") J/K")
    log("Cm [K=1] = ("+str(z)+" +/- "+str(Dz)+") J/K")



def getAvTs(start):
    Tsavarr = []
    for i in range(len(x)):
        if( start < x[i]):
            Tsavarr.append(Ts[i])
    return np.average(Tsavarr), np.std(Tsavarr)




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



colors = {}
colors["data"] = "blue"
colors["base"] = "dimgrey"
colors["main"] = "darkorange"
colors["exp"] = "crimson"
colors["T*"] = "green"



def show():
    global fig
    if(not fig):
        fig = plt.figure()
    plt.clf()
    plt.plot(x,y, color=colors["data"], label='Kaloriméter hőmérséklet')
    plt.xlabel("t (s)")
    plt.ylabel(r'T $(^{\circ}C)$')


    auto_ylim = plt.gca().get_ylim()
    auto_xlim = plt.gca().get_xlim()


    if(grid):
        plt.grid("true",linestyle="--")

    xs = np.linspace(x[0], x[-1], 100)
    if(bBase):
        #plt.autoscale(False)
        if(bBaseExp):
            plt.plot(xs,fexp(xs,baseexp_A,baseexp_b,baseexp_c),color=colors["base"], label="Előszakasz illesztés (exp. korr.)")
        elif(bBaseSpline):
            def getcomplexbase(x_arr):
                ret_y = []
                for x_i in x_arr:
                    if(x_i <= base_end):
                        ret_y.append(flin(x_i,base_a,base_b))
                    elif(x_i <= exp_start):
                        ret_y.append(float(basespline(x_i)))
                    else:
                        ret_y.append(exp_c)
                return ret_y
                
            plt.plot(xs,getcomplexbase(xs),color=colors["base"], label="Előszakasz illesztés")

        else:
            plt.plot(xs,flin(xs,base_a,base_b),color=colors["base"], label="Előszakasz illesztés")

    if(bTs):
        #plt.autoscale(True)
        plt.plot(x,Ts, color=colors["T*"], label="Korrigált hőmérséklet")
        auto_ylim = plt.gca().get_ylim()

    if(bMain):
        #plt.autoscale(False)
        plt.plot(xs,flin(xs,main_a,main_b), color=colors["main"], label=("Főszakasz illesztés (korr.)" if bMainCorrected else "Főszakasz illesztés") )
    if(bMainExp):
        xs2 = np.linspace(mainexp_start, mainexp_end, 100)
        #plt.autoscale(False)
        plt.plot(xs2,fexp(xs2,mainexp_A,mainexp_b,mainexp_c), color=colors["main"], label="Exp. főszakasz illesztés")
    if(bExp):
        #plt.autoscale(False)
        plt.plot(xs,fexp(xs,exp_A,exp_b,exp_c), color=colors["exp"], label="Utószakasz illesztés")
        plt.plot(xs,flin(xs,0,exp_c), color=colors["exp"], linestyle="--")

    if(bLegend):
        plt.legend()

    if(scaletodata):
        plt.xlim(auto_xlim)
        plt.ylim(auto_ylim)

s = show
p = show


def log(text):
    with open(directory+"OUTfajho_fitlog.dat", "a") as f:
        print(text, file=f)


def loadcalib():
    global bCalib
    global Cp
    global dCp
    global alfa
    global dalfa
    path = easygui.fileopenbox()
    if(path):
        calin = np.loadtxt(path,skiprows = 1)
        Cp = calin[0]
        dCp = calin[1] / Cp
        alfa = calin[2]
        dalfa = calin[3] / alfa
        bCalib = True
        print("Calibration loaded:")
        print("Cp = ("+str(Cp)+" +/- "+str(dCp*Cp)+") J/K")
        print("Alfa = ("+str(alfa)+" +/- "+str(dalfa*alfa)+") W/K")
    else:
        print("Error: no calibration file found in path")





def cd(*args):
    global directory
    if(len(args)==0):
        path = easygui.diropenbox()
    else:
        path = args[0]

    try:
        os.chdir(path)
        print("Current working directory: {0}".format(os.getcwd()))
        directory = path
    except FileNotFoundError:
        print("Directory: {0} does not exist".format(path))
    except NotADirectoryError:
        print("{0} is not a directory".format(path))
    except PermissionError:
        print("You do not have permissions to change to {0}".format(path))




def png():
    plt.rcParams["savefig.format"] = "png"
def pdf():
    plt.rcParams["savefig.format"] = "pdf"






def new(*args):
    global directory

    global bBase
    global bMain
    global bExp
    global bInt
    global bTs
    global bMainExp
    global bBaseExp
    global bMainCorrected
    global bBaseSpline

    global x
    global y
    global heater
    global Uarr
    global R

    global bCalib
    global Cp
    global dCp
    global alfa
    global dalfa

    global bEpszilonVesszo
    global ev


    if(len(args)==0):
        path = easygui.fileopenbox(filetypes=[["*","All files"],["*.*","All files"]]) 
    else:
        path = args[0]
    if(path):

        # get the directory
        pathtrunc = path
        while(True):
            if(pathtrunc[-1] == '/'):
                directory = pathtrunc
                break
            else:
                pathtrunc = pathtrunc[:-1]
            
            if(len(pathtrunc) <= 0):
                print("Error while recursing for directory")
                return

        # workaround: first log message doesn't seem to go out, if log does not exist, create it
        if(not os.path.exists(directory+"OUTfajho_fitlog.dat")):
            with open(directory+"OUTfajho_fitlog.dat", "a") as f:
                print("", file=f)
            
        bBase = False
        bMain = False
        bMainCorrected = False
        bExp = False
        bInt = False
        bTs = False
        bMainExp = False
        bCalib = False
        bEpszilonVesszo = False
        bBaseExp = False
        bBaseSpline = False

        try:
            data0 = np.loadtxt(path,skiprows=2)
        except Exception as e:
            print("Could not load file")
            return

        with open(path) as f:
            R_line = f.readline()
            R = float(re.sub("[^\d\.]", "", R_line))

        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        log("\nOpened file: "+path+" at ["+str(current_time)+"]\n")

        try:
            os.chdir(directory)
            #print("Current working directory: {0}".format(os.getcwd()))
        except FileNotFoundError:
            print("Directory: {0} does not exist".format(directory))
        except NotADirectoryError:
            print("{0} is not a directory".format(directory))
        except PermissionError:
            print("You do not have permissions to change to {0}".format(directory))

        if(os.path.exists(directory+"OUTfajho_kalibracio.dat")):
            calin = np.loadtxt(directory+"OUTfajho_kalibracio.dat",skiprows = 1)
            Cp = calin[0]
            dCp = calin[1] / Cp
            alfa = calin[2]
            dalfa = calin[3] / alfa
            bCalib = True
            print("Existing calibration found:")
            print("Cp = ("+str(Cp)+" +/- "+str(dCp*Cp)+") J/K")
            print("Alfa = ("+str(alfa)+" +/- "+str(dalfa*alfa)+") W/K")

        if(os.path.exists(directory+"OUTfajho_beejtepszilon.dat")):
            evin = np.loadtxt(directory+"OUTfajho_beejtepszilon.dat",skiprows = 1)
            ev = evin
            bEpszilonVesszo = True
            print("Existing epszilon' found:")
            print("ev = "+str(ev)+" 1/s")


        x,y,heater,Uarr = process_data(data0)
        s()
    else:
        print("Error: no file found in path")
o = new
uj = new


new()

import matplotlib as mpl 
mpl.rcParams["savefig.directory"] = ""
plt.rcParams["savefig.format"] = "pdf"

code.interact(local=locals())
