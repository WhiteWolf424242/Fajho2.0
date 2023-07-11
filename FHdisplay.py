# -*- coding: utf-8 -*-
import os
import tkinter as tk
import FHutil
import matplotlib.pyplot as plt
plt.ion()
plt.rcParams["savefig.format"] = "pdf"
import numpy as np
import FHeval



class ToolTipBase:

    def __init__(self, button):
        self.button = button
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self._id1 = self.button.bind("<Enter>", self.enter)
        self._id2 = self.button.bind("<Leave>", self.leave)
        self._id3 = self.button.bind("<ButtonPress>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.button.after(700, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.button.after_cancel(id)

    def showtip(self):
        if self.tipwindow:
            return
        # The tip window must be completely outside the button;
        # otherwise when the mouse enters the tip window we get
        # a leave event and it disappears, and then we get an enter
        # event and it reappears, and so on forever :-(
        x = self.button.winfo_rootx() + 20
        y = self.button.winfo_rooty() + self.button.winfo_height() + 1
        self.tipwindow = tw =tk.Toplevel(self.button)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        self.showcontents()

    def showcontents(self, text="Your text here"):
        # Override this in derived class
        label = tk.Label(self.tipwindow, text=text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack()

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class ToolTip(ToolTipBase):

    def __init__(self, button, text):
        ToolTipBase.__init__(self, button)
        self.text = text

    def showcontents(self):
        ToolTipBase.showcontents(self, self.text)


class ListboxToolTip(ToolTipBase):

    def __init__(self, button, items):
        ToolTipBase.__init__(self, button)
        self.items = items

    def showcontents(self):
        listbox = tk.Listbox(self.tipwindow, background="#ffffe0")
        listbox.pack()
        for item in self.items:
            listbox.insert(tk.END, item)





class DisplayWindow:
    window = None
    currentcall = None
    prevcall = None
    active_measurement = None
    figure = None
    cid = None
    ccloseid = None
    boundstarget = None
    parentfunc = None
    evaltarget = None
    finishfunction = None

    aBounds = None
    bDrawRangeSelectorGuideLine = False
    rangeSelectorGuideLinex = 0

    dualfitlimit = "fixed"

    figtitle = ""
    grid = True
    bLegend = False
    scaletodata = True
    autoshow = True

    colors = {}
    colors["data"] = "blue"
    colors["base"] = "dimgrey"
    colors["main"] = "darkorange"
    colors["exp"] = "crimson"
    colors["T*"] = "green"


    def __init__(self):
        self.mainwindow(init=True)




    def pushcall(self, function):
        self.prevcall = self.currentcall
        self.currentcall = function

    def mainwindow(self, init=False):
        self.pushcall(self.mainwindow)

        if self.window == None: 
            self.window = tk.Tk()
            self.window.geometry('%dx%d+%d+%d' % (700, 400, 0, 0))

        for widget in self.window.winfo_children():
            widget.destroy()

        self.window.title("Fajhő kiértékelő 2.0")
        texts = ["Kalibráció","Beejtés","Ráfűtés"]


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Új betöltése", command=self.newfile)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ábrázol", command=lambda: self.show(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Kalibráció", command=self.calibwindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="Beejtés", command=self.beejteswindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=2, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ráfűtés", command=self.futeswindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])



        self.window.columnconfigure([0,1,2,3,4], weight=1, minsize=75)
        self.window.rowconfigure([0,1,2,3,4], weight=1, minsize=50)

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        if(init):
            self.newfile()
        self.window.mainloop()




    def newfile(self):
        self.active_measurement = FHutil.new()
        self.show(self.active_measurement)


    def calibwindow(self):
        self.pushcall(self.calibwindow)


        if(not self.active_measurement):
            print("Error <FHdisplay.calibwindow>: No active measurement")
            self.prevcall()


        self.setfigtitle("Vízérték mérése", "vizertek_abra")


        for widget in self.window.winfo_children():
            widget.destroy()

        #self.window.destroy()
        #self.window = tk.Tk()
        self.window.title("Vízérték kiértékelése")

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Vissza", command = self.mainwindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ábrázol", command=lambda: self.show(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="1) Előszakasz illesztése" if not self.active_measurement.bBase else "1) Előszakasz módosítása", command = lambda: self.selecteloszakaszwindow(self.calibwindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="2) Utószakasz illesztése" if not self.active_measurement.bExp else "2) Utószakasz módosítása", command = lambda: self.selectutoszakaszwindow(self.calibwindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=2, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="3) Korrigált hőmérséklet számolása", command = self.calculateTs)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=3, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="4) Főszakasz illesztése" if not self.active_measurement.bMainCorrected else "4) Főszakasz módosítása", command = lambda: self.selectfoszakaszwindow(self.calibwindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=4, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="5) Cp, alfa számolása", command = lambda: FHeval.calib(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])



        self.window.columnconfigure([0,1,2,3,4,5], weight=1, minsize=75)
        self.window.rowconfigure([0,1,2,3,4,5], weight=1, minsize=50)

        self.window.mainloop()



    def futeswindow(self):
        self.pushcall(self.futeswindow)

        if(not self.active_measurement):
            print("Error <FHdisplay.futeswindow>: No active measurement")
            self.prevcall()


        self.setfigtitle("Fajhő mérése ráfűtéssel", "rafutes_abra")


        for widget in self.window.winfo_children():
            widget.destroy()

        #self.window.destroy()
        #self.window = tk.Tk()
        self.window.title("Ráfűtés kiértékelése")
        texts = ["1) Előszakasz illesztése","2) Utószakasz illesztése","3) Korrigált hőmérséklet","4) Főszakasz illesztése"]


        self.window.columnconfigure(0, weight=1, minsize=75)
        self.window.rowconfigure(0, weight=1, minsize=50)

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Vissza", command = self.mainwindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ábrázol", command=lambda: self.show(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="1) Előszakasz illesztése" if not self.active_measurement.bBase else "1) Előszakasz módosítása", command = lambda: self.selecteloszakaszwindow(self.futeswindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="2) Utószakasz illesztése" if not self.active_measurement.bExp else "2) Utószakasz módosítása", command = lambda: self.selectutoszakaszwindow(self.futeswindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=2, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="3) Korrigált hőmérséklet számolása", command = self.calculateTs)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=3, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="4) Főszakasz illesztése" if not self.active_measurement.bMainCorrected else "4) Főszakasz módosítása", command = lambda: self.selectfoszakaszwindow(self.futeswindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=4, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="5) Hőkapacitás számolása", command = lambda: FHeval.rafut(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])



        self.window.columnconfigure([0,1,2,3,4,5], weight=1, minsize=75)
        self.window.rowconfigure([0,1,2,3,4,5], weight=1, minsize=50)

        self.window.mainloop()

    def beejteswindow(self):
        self.pushcall(self.beejteswindow)

        if(not self.active_measurement):
            print("Error <FHdisplay.beejteswindow>: No active measurement")
            self.prevcall()


        for widget in self.window.winfo_children():
            widget.destroy()
        self.window.title("Beejtés kiértékelése")


        self.setfigtitle("Fajhő mérése beejtéssel", "beejtes_abra")

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Vissza", command = self.mainwindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ábrázol", command=lambda: self.show(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="1) Előszakasz illesztése" if not self.active_measurement.bBase else "1) Előszakasz módosítása", command = lambda: self.selecteloszakaszwindow(self.beejteswindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="2) Utószakasz illesztése" if not self.active_measurement.bExp else "2) Utószakasz módosítása", command = lambda: self.selectutoszakaszwindow(self.beejteswindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=2, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="3) Korrigált hőmérséklet számolása", command = self.calculateTs)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=3, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="4) Integrálás", command = lambda: self.selectintegralwindow(self.beejteswindow) )
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=4, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="5) Variált határú integrálás", )
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])



        self.window.columnconfigure([0,1,2,3,4,5], weight=1, minsize=75)
        self.window.rowconfigure([0,1,2,3,4,5], weight=1, minsize=50)

        self.window.mainloop()


    def on_closing(self):
        if(self.currentcall != None):
            self.pushcall(None)
            for widget in self.window.winfo_children():
                widget.destroy()

            self.window.title("Biztos ki akarsz lépni?")

            self.window.columnconfigure(0, weight=1, minsize=75)
            self.window.rowconfigure(0, weight=1, minsize=50)
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1
            )
            frame.grid(row=0, column=0, padx=5, pady=5)
            label = tk.Button(master=frame, text="Kilépés", command = quit)
            label.pack(padx=5, pady=5)

            self.window.columnconfigure(0, weight=1, minsize=75)
            self.window.rowconfigure(0, weight=1, minsize=50)
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1
            )
            frame.grid(row=0, column=1, padx=5, pady=5)
            label = tk.Button(master=frame, text="Vissza", command=self.prevcall)
            label.pack(padx=5, pady=5)


            self.window.mainloop()


    def on_figure_close(self, event):
        self.figure.canvas.mpl_disconnect(self.ccloseid)
        self.figure = None


    def show(self,meas, bKeepZoom = False):
        if(not self.active_measurement):
            print("Error <FHdisplay.show>: No selected data")
            return


        if(not self.figure):
            self.figure = plt.figure()
            self.ccloseid = self.figure.canvas.mpl_connect('close_event', self.on_figure_close)

        current_xlim = plt.gca().get_xlim()
        current_ylim = plt.gca().get_ylim()

        plt.clf()
        plt.plot(meas.x,meas.y, color=self.colors["data"], label='Kaloriméter hőmérséklet')
        plt.xlabel("t (s)")
        plt.ylabel(r'T $(^{\circ}C)$')


        auto_ylim = plt.gca().get_ylim()
        auto_xlim = plt.gca().get_xlim()


        if(self.grid):
            plt.grid("true",linestyle="--")

        xs = np.linspace(meas.x[0], meas.x[-1], 100)
        if(meas.bBase):
            #plt.autoscale(False)
            if(meas.bBaseExp):
                plt.plot(xs,FHutil.fexp(xs,meas.baseexp_A,meas.baseexp_b,meas.baseexp_c),color=self.colors["base"], label="Előszakasz illesztés (exp. korr.)")
            elif(meas.bBaseSpline):
                def getcomplexbase(x_arr):
                    ret_y = []
                    for x_i in x_arr:
                        if(x_i <= meas.base_end):
                            ret_y.append(FHutil.flin(x_i,meas.base_a,meas.base_b))
                        elif(x_i <= meas.exp_start):
                            ret_y.append(float(meas.basespline(x_i)))
                        else:
                            ret_y.append(meas.exp_c)
                    return ret_y
                    
                plt.plot(xs,getcomplexbase(xs),color=self.colors["base"], label="Előszakasz illesztés")

            else:
                plt.plot(xs,FHutil.flin(xs,meas.base_a,meas.base_b),color=self.colors["base"], label="Előszakasz illesztés")

        if(meas.bTs):
            #plt.autoscale(True)
            plt.plot(meas.x,meas.Ts, color=self.colors["T*"], label="Korrigált hőmérséklet")
            auto_ylim = plt.gca().get_ylim()

        if(meas.bMain):
            #plt.autoscale(False)
            plt.plot(xs,FHutil.flin(xs,meas.main_a,meas.main_b), color=self.colors["main"], label=("Főszakasz illesztés (korr.)" if meas.bMainCorrected else "Főszakasz illesztés") )
        if(meas.bMainExp):
            xs2 = np.linspace(meas.mainexp_start, meas.mainexp_end, 100)
            #plt.autoscale(False)
            plt.plot(xs2,FHutil.fexp(xs2,meas.mainexp_A,meas.mainexp_b,meas.mainexp_c), color=self.colors["main"], label="Exp. főszakasz illesztés")
        if(meas.bExp):
            #plt.autoscale(False)
            plt.plot(xs,FHutil.fexp(xs,meas.exp_A,meas.exp_b,meas.exp_c), color=self.colors["exp"], label="Utószakasz illesztés")
            plt.plot(xs,FHutil.flin(xs,0,meas.exp_c), color=self.colors["exp"], linestyle="--")

        if(self.bDrawRangeSelectorGuideLine):
            plt.axvline(x = self.rangeSelectorGuideLinex, color = 'magenta', alpha = 0.8, linestyle = (0, (1, 1)))

        if(self.bLegend):
            plt.legend()

        if(self.scaletodata):
            plt.xlim(auto_xlim)
            plt.ylim(auto_ylim)


        plt.title(self.figtitle)

        if(bKeepZoom):
            plt.gca().set_xlim(current_xlim)
            plt.gca().set_ylim(current_ylim)
        plt.show(block=False)
        return


    def setfigtitle(self, title, wintitle):
        self.figtitle = title 
        self.figure.canvas.manager.set_window_title(wintitle)
        self.show(self.active_measurement, bKeepZoom=True)



    def dualfitwindow(self):
        self.pushcall(self.dualfitwindow)

        for widget in self.window.winfo_children():
            widget.destroy()

        self.window.title("Kettős illesztés")

        self.window.columnconfigure(0, weight=1, minsize=75)
        self.window.rowconfigure(0, weight=1, minsize=50)

        frame = tk.Frame(
            master=self.window,
            #relief=tk.RAISED,
            borderwidth=0
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Label(master=frame, text="Kettős illesztés:")
        label.pack(padx=5, pady=5)


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Spline", command = lambda: self.do_dualfit("spline"))
        label.pack(padx=5, pady=5)


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="Exponenciális", command = lambda: self.do_dualfit("exp"))
        label.pack(padx=5, pady=5)


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=2, padx=5, pady=5)
        label = tk.Button(master=frame, text="Kihagyás", command = self.parentfunc)
        label.pack(padx=5, pady=5)

        self.window.mainloop()


    def do_dualfit(self, method):
        FHeval.dualfit(self.active_measurement, method, self.dualfitlimit)
        if(self.autoshow):
            self.show(self.active_measurement)
        self.parentfunc()


    def selecteloszakaszwindow(self, parent):
        self.parentfunc = parent
        self.finishfunction = parent
        if(self.active_measurement.bExp):
            self.finishfunction = self.dualfitwindow
        self.evaltarget = FHeval.fitbase
        self.rangeSelectorMainWindow("Előszakasz illesztése")

    def selectutoszakaszwindow(self, parent):
        self.parentfunc = parent
        self.finishfunction = self.dualfitwindow
        self.evaltarget = FHeval.fitexp
        self.rangeSelectorMainWindow("Utószakasz illesztése")


    def selectintegralwindow(self, parent):
        self.parentfunc = parent
        self.finishfunction = parent
        self.evaltarget = FHeval.integrate
        self.rangeSelectorMainWindow("Integrál számítása")

    def calculateTs(self):
        #print("Pillanat türelmet...")
        FHeval.getTsOptimized(self.active_measurement)
        if(self.autoshow):
            self.show(self.active_measurement)

    def selectfoszakaszwindow(self, parent):
        self.parentfunc = parent
        self.finishfunction = parent
        self.evaltarget = FHeval.fitmaincorrected
        self.rangeSelectorMainWindow("Főszakasz illesztése")


    def rangeSelectorMainWindow(self, title):
        self.pushcall(self.rangeSelectorMainWindow)

        for widget in self.window.winfo_children():
            widget.destroy()

        self.window.title(title)

        self.window.columnconfigure(0, weight=1, minsize=75)
        self.window.rowconfigure(0, weight=1, minsize=50)

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Vissza", command = lambda: self.cancelrangeselect(self.parentfunc))
        label.pack(padx=5, pady=5)


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=1, padx=5, pady=5)
        label = tk.Label(master=frame, text="Alsó határ: <dupla kattintás az ábrára>", )
        label.pack(padx=5, pady=5)



        self.aBounds = []
        self.bDrawRangeSelectorGuideLine = False
        self.show(self.active_measurement, bKeepZoom=True)

        self.rig_for_input(self.rangeSelectorSecondRangeWindow)
        self.window.mainloop()


    def rig_for_input(self, targetf):
         self.cid = self.figure.canvas.mpl_connect('button_press_event', self.onclick)
         self.boundstarget = targetf

    def cancelrangeselect(self, function):
        self.parentfunc = None
        self.evaltarget = None
        self.bDrawRangeSelectorGuideLine = False
        self.show(self.active_measurement)
        self.backfromrangeselect(function)

    def backfromrangeselect(self, function):
        self.stop_input()
        function()

    def stop_input(self):
        self.figure.canvas.mpl_disconnect(self.cid)

    def onclick(self,event):
        #print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
        #  ('double' if event.dblclick else 'single', event.button,
        #   event.x, event.y, event.xdata, event.ydata))

        if(event.dblclick or event.button == 2):
            self.figure.canvas.mpl_disconnect(self.cid)
            self.aBounds.append(event.xdata)
            self.boundstarget(event.xdata, event.ydata)
            return True
        return False
    

    def rangeSelectorSecondRangeWindow(self, xdata, ydata):
        #self.pushcall(self.rangeSelectorSecondRangeWindow)

        for widget in self.window.winfo_children():
            widget.destroy()

        self.window.title("Előszakasz illesztése")


        self.window.columnconfigure(0, weight=1, minsize=75)
        self.window.rowconfigure(0, weight=1, minsize=50)

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Vissza", command = lambda: self.cancelrangeselect(self.parentfunc))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=1, padx=5, pady=5)
        label = tk.Label(master=frame, text="Alsó határ: "+str(self.aBounds[0]), )
        label.pack(padx=5, pady=5)


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=0, column=2, padx=5, pady=5)
        label = tk.Button(master=frame, text="(Módosít)", command = lambda: self.backfromrangeselect(self.rangeSelectorMainWindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        label = tk.Label(master=frame, text="Felső határ: <dupla kattintás az ábrára>", )
        label.pack(padx=5, pady=5)

        self.bDrawRangeSelectorGuideLine = True
        self.rangeSelectorGuideLinex = self.aBounds[0]
        if(self.autoshow):
            self.show(self.active_measurement, bKeepZoom=True)

        self.rig_for_input(self.rangeSelector2Finish)
        self.window.mainloop()



    def rangeSelector2Finish(self, xdata, ydata):
        self.bDrawRangeSelectorGuideLine = False
        self.evaltarget(self.active_measurement, self.aBounds[0], self.aBounds[1])
        if(self.autoshow):
            self.show(self.active_measurement)
        self.finishfunction()

