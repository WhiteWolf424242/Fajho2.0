# -*- coding: utf-8 -*-
import os
import numpy as np
import FHutil
from scipy.optimize import curve_fit



def do_fit(x,y,xmin,xmax, func = FHutil.flin):
    xf = []
    yf = []
    for i in range(len(x)):
        if(xmin <= x[i] <= xmax):
            xf.append(x[i])
            yf.append(y[i])


    return curve_fit(func, xf, yf)


    
def fitbase(meas, xmin, xmax):
    meas.base_start = xmin
    meas.base_end = xmax
    params, covs = do_fit(meas.x,meas.y,xmin,xmax)
    meas.log("\nBase fit in x["+str(xmin)+"; "+str(xmax)+"],   y = p0*x + p1")
    meas.fitreport(params, covs)

    meas.bBase = True
    meas.base_a = params[0]
    meas.base_b = params[1]

    perr = np.sqrt(np.diag(covs))
    meas.Dbase_a = perr[0]



def fitexp(meas, xmin,xmax):
    if(not meas.bBase):
        print("Error: missing base fit")
        return


    meas.exp_start = xmin
    meas.exp_end = xmax


    xf = []
    yf = []
    for i in range(len(meas.x)):
        if(xmin <= meas.x[i] <= xmax):
            xf.append(meas.x[i])
            yf.append(meas.y[i])
    a_guess = 3.6
    b_guess = 0.001
    c_guess = 20
    params, covs = curve_fit(lambda t, a, b, c: a * np.exp(-b * t) + c, xf, yf, p0=(a_guess, b_guess, c_guess))

    meas.log("\nExponential fit in x["+str(xmin)+"; "+str(xmax)+"],   y = p0*exp(-p1 * x) + p2")
    meas.fitreport(params, covs)
    meas.bExp = True
    meas.exp_A = params[0]
    meas.exp_b = params[1]
    meas.exp_c = params[2]

    perr = np.sqrt(np.diag(covs))
    meas.Dexp_b = perr[1]






def dualfit(meas, method, limit):

    if(not meas.bBase):
        print("Error in dualfit: missing base fit")
        return
    if(not meas.bExp):
        print("Error in dualfit: missing exp fit")
        return
    
    if(method == "exp" or method == "e"):

        xf = []
        yf = []
        for i in range(len(meas.x)):
            if(meas.base_start <= meas.x[i] <= meas.base_end):
                xf.append(meas.x[i])
                yf.append(meas.y[i])



        a_guess = 3.6
        b_guess = 0.001
        c_guess = meas.exp_c

        if(limit == "free"):
            params, covs = curve_fit(lambda t, a, b, c: a * np.exp(-b * t) + c, xf, yf, p0=(a_guess, b_guess, c_guess))
            meas.log("\nDual fit: Exponential base correction,   y = p0*exp(-p1 * x) + c")
            print("Dual fit: Exponential base correction,   y = p0*exp(-p1 * x) + c")
        else:
            params, covs = curve_fit(lambda t, a, b: a * np.exp(-b * t) + meas.exp_c, xf, yf, p0=(a_guess, b_guess))
            meas.log("\nDual fit: Exponential base correction [fixed limit],   y = p0*exp(-p1 * x) + "+str(meas.exp_c))
            print("Dual fit: Exponential base correction [fixed limit],   y = p0*exp(-p1 * x) + "+str(meas.exp_c))
        meas.fitreport(params, covs)
        meas.bBaseExp = True
        meas.bBaseSpline = False
        meas.baseexp_A = params[0]
        meas.baseexp_b = params[1]
        meas.baseexp_c = params[2] if limit == "free" else meas.exp_c

    elif(method == "spline" or method == "s"):
        tandata_x = []
        tandata_y = []
        #Tkval, DTkval = getTk()
        for i in range(len(meas.x)):
            if meas.base_end - 20 <= meas.x[i] <= meas.base_end:
                tandata_x.append(meas.x[i])
                tandata_y.append(FHutil.flin(meas.x[i],meas.base_a, meas.base_b))
            if meas.exp_start <= meas.x[i] <= meas.exp_start + 20:
                tandata_x.append(meas.x[i])
                tandata_y.append(meas.exp_c)
        
        from scipy.interpolate import CubicSpline
        meas.basespline = CubicSpline(tandata_x, tandata_y)
        meas.bBaseSpline = True
        meas.bBaseExp = False

        meas.log("Dual fit: Base fit and exponential limit connected with cubic spline")





def getTs(meas):
    if(not meas.bBase):
        print("Error: base fit not found")
        return
    if(not meas.bExp):
        print("Error: exponential fit not found")
        return
    
    startpoint = meas.base_end

    meas.Ts = []

    
    for i in range(len(meas.x)):
        if(meas.x[i] < startpoint):
            meas.Ts.append(meas.y[i])
        else:
            t = meas.x[i]
            xf = []
            yf = []
            for j in range(len(meas.x)):
                if(startpoint <= meas.x[j] <= t):
                    xf.append(meas.x[j])
                    yf.append(meas.y[j])


            Tk = getTkValue(meas, meas.x[j])
            # ez igy garantalja hogy ha van dualfit akkor azt kapjuk, ha nem akkor pedig az exp_limeszt kapjuk vissza

            for j in range(len(xf)):
                yf[j] -= Tk

            meas.Ts.append(meas.y[i] + meas.exp_b*FHutil.trapcalc(xf,yf))
    meas.bTs = True


def getTkValue(meas, xp = "indep"):
    if(not meas.bBase):
        print("Error in getTkValue(): missing base fit")
        return False

    if(xp != "indep"):

        if(meas.bBaseSpline):
            if(xp <= meas.base_end):
                return FHutil.flin(xp,meas.base_a,meas.base_b)
            elif(xp <= meas.exp_start):
                return float(meas.basespline(xp))
            else:
                return meas.exp_c

        if(meas.bBaseExp):
            return FHutil.fexp(xp,meas.baseexp_A,meas.baseexp_b,meas.baseexp_c)
        if(meas.bExp):
            return meas.exp_c
        return FHutil.flin(xp,meas.base_a,meas.base_b)

    aTk = []
    for i in range(len(meas.x)):
        if(meas.base_end - 10 <= meas.x[i] <= meas.base_end + 5):
            aTk.append( FHutil.flin(meas.x[i], meas.base_a, meas.base_b) )
    return np.average(aTk)





def fitmaincorrected(meas, xmin, xmax):

    if(not meas.bTs):
        print("Error: missing T* fit")
        return

    
    meas.main_start = xmin
    meas.main_end = xmax

    params, covs = do_fit(meas.x,meas.Ts,xmin,xmax)
    meas.log("\nMain fit in x["+str(xmin)+"; "+str(xmax)+"] onto T*,   y = p0*x + p1")
    meas.fitreport(params, covs)

    meas.bMain = True
    meas.bMainCorrected = True
    meas.main_a = params[0]
    meas.main_b = params[1]

    perr = np.sqrt(np.diag(covs))
    meas.Dmain_a = perr[0]

    if(meas.bBase):
        meas.main_a_corr = meas.main_a - meas.base_a
        meas.Dmain_a_corr = meas.Dmain_a + meas.Dbase_a





def calib(meas):
    if(not meas.bBase):
        print("Error: missing base")
        return
    if(not meas.bMain):
        print("Error: missing main")
        return
    if(not meas.bExp):
        print("Error: missing exp")
        return

    print("R = ("+str(meas.R)+" +/- "+str(meas.DR)+") Ohm")


    # get U
    t, U, DU = FHutil.getheatingdata(meas)
    print("U = ("+str(U)+" +/- "+str(DU)+") V")

    # FIXME: MIERT IS??
    print("a_corr = ("+str(meas.main_a_corr)+" +/- "+str(meas.Dmain_a_corr)+") K/s")

    print("Beta = ("+str(meas.exp_b)+" +/- "+str(meas.Dexp_b)+") 1/s")
    # get Cp
    meas.Cp = U**2/meas.R/meas.main_a_corr
    meas.dCp = 2*DU/U + meas.DR/meas.R + meas.Dmain_a_corr/meas.main_a_corr
    print("=======================")
    print("Cp = ("+str(meas.Cp)+" +/- "+str(meas.dCp*meas.Cp)+") J/K")

    meas.alfa = meas.exp_b * meas.Cp
    meas.dalfa = meas.dCp + meas.Dexp_b/meas.exp_b
    print("Alfa = ("+str(meas.alfa)+" +/- "+str(meas.dalfa*meas.alfa)+") W/K")
    meas.bCalib = True

    meas.log("\nCalibration data:")
    meas.log("R = ("+str(meas.R)+" +/- "+str(meas.DR)+") Ohm")
    meas.log("U = ("+str(U)+" +/- "+str(DU)+") V")
    meas.log("a_corr = ("+str(meas.main_a_corr)+" +/- "+str(meas.Dmain_a_corr)+") K/s")
    meas.log("Beta = ("+str(meas.exp_b)+" +/- "+str(meas.Dexp_b)+") 1/s")
    meas.log("=======================")
    meas.log("Cp = ("+str(meas.Cp)+" +/- "+str(meas.dCp*meas.Cp)+") J/K")
    meas.log("Alfa = ("+str(meas.alfa)+" +/- "+str(meas.dalfa*meas.alfa)+") W/K\n")

    with open(meas.directory+"OUTfajho_kalibracio.dat", "w") as f:
        print("# Cp [J/K], D(Cp) [J/K], alfa [W/K], D(alfa) [W/K]", file=f)
        print(meas.Cp, meas.dCp*meas.Cp, meas.alfa, meas.dalfa*meas.alfa,file=f)



def rafut(meas):
    if(not meas.bCalib):
        print("Error: missing calib")
        return
    if(not meas.bBase):
        print("Error: missing base fit")
        return
    if(not meas.bMain):
        print("Error: missing main fit")
        return

    print("R = ("+str(meas.R)+" +/- "+str(meas.DR)+") Ohm")


    # get U
    t, U, DU = FHutil.getheatingdata(meas)
    print("\nCalculating Cm data:")
    print("R = ("+str(meas.R)+" +/- "+str(meas.DR)+") Ohm")
    print("U = ("+str(U)+" +/- "+str(DU)+") V")
    print("a_corr = ("+str(meas.main_a_corr)+" +/- "+str(meas.Dmain_a_corr)+") K/s")
    # get Ck
    Ck = U**2/meas.R/meas.main_a_corr
    dCk = 2*DU/U + meas.DR/meas.R + meas.Dmain_a_corr/meas.main_a_corr
    print("=======================")
    print("Ck = ("+str(Ck)+" +/- "+str(dCk*Ck)+") J/K")
    print("Cm = ("+str(Ck-meas.Cp)+" +/- "+str(dCk*Ck + meas.dCp*meas.Cp)+") J/K")

    meas.log("\nCalculating Cm data:")
    meas.log("R = ("+str(meas.R)+" +/- "+str(meas.DR)+") Ohm")
    meas.log("U = ("+str(U)+" +/- "+str(DU)+") V")
    meas.log("a_corr = ("+str(meas.main_a_corr)+" +/- "+str(meas.Dmain_a_corr)+") K/s")
    meas.log("=======================")
    meas.log("Ck = ("+str(Ck)+" +/- "+str(dCk*Ck)+") J/K")
    meas.log("Cm = ("+str(Ck-meas.Cp)+" +/- "+str(dCk*Ck + meas.dCp*meas.Cp)+") J/K")


    with open(meas.directory+"OUTfajho_rafutes.dat", "w") as f:
        print("# Ck [J/K], D(Ck) [J/K], Cm [J/K], D(Cm) [J/K]", file=f)
        print(Ck, dCk*Ck, Ck-meas.Cp, dCk*Ck + meas.dCp*meas.Cp,file=f)





def getTm(meas,position):
    Tm_l = []
    for i in range(len(meas.x)):
        if(position - 10 <= meas.x[i] <= position + 5):
            Tm_l.append(meas.heater[ i ])
    return np.average(Tm_l), np.std(Tm_l)


def integrate(meas, xmin, xmax):
    if(not meas.bCalib):
        print("Error: missing calib")
        return
    if(not meas.bExp):
        print("Error: missing exp fit")
        return

    xf = []
    yf = []
    for i in range(len(meas.x)):
        if(xmin <= meas.x[i] <= xmax):
            xf.append(meas.x[i])
            yf.append(meas.y[i])


    Tt = yf[-1]

    Tm, DTm = getTm(meas, xmin)

    #Tk, DTk = getTk()
    # this used to average over the whole baseline
    # no need, we need it at the start of the thing, so more precise to average just there!
    Tk, DTk = getTkValue(meas, xmin)

    for i in range(len(xf)):
        yf[i] -= getTkValue(meas, xf[i])   # nem kell [0] #FIXME két visszatérési érték ven!!!!!

    integ = FHutil.trapcalc(xf,yf)

    cm = (meas.Cp*(Tt - Tk)+meas.alfa*integ)/( Tm-Tt )

    # assuming DTk deviation for T(t) as well, and assuming DI ~ 0
    Dcm = abs((Tt - Tk)/(Tm-Tt))* (meas.dCp*meas.Cp) + abs((meas.alfa*integ + meas.Cp*(Tm - Tk)/(Tm - Tt)**2))*DTk + abs(-meas.Cp/(Tm - Tt))*DTk + abs(integ/(Tm - Tt))*(meas.dalfa*meas.alfa) + abs((meas.Cp*(Tk - Tt) - meas.alfa*integ)/(Tm - Tt)**2)* DTm

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