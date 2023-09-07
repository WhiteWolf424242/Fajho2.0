# -*- coding: utf-8 -*-
import os
import tkinter as tk
import FHutil
import matplotlib.pyplot as plt
plt.ion()
plt.rcParams["savefig.format"] = "pdf"
plt.rcParams['keymap.back'].remove('left')
plt.rcParams['keymap.forward'].remove('right')
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
    evalcall = None
    active_measurement = None
    rangewindowtitle = ""
    figure = None
    cid = None
    kid = None
    bCRigged = False
    bKRigged = False
    bModifying = False
    ccloseid = None
    boundstarget = None
    parentfunc = None
    evaltarget = None
    finishfunction = None
    numberofranges = 2

    aBounds = []
    rangeSelectorGuideLines = [False, False, False]
    rangeSelectorGhosts = [False, False, False]
    active_index = -1
    previous_index = -1
    modifybuffer = -1

    dualfitlimit = "fixed"

    figtitle = ""
    grid = True
    bLegend = False
    scaletodata = True
    autoshow = True
    bAutoZoom = False

    colors = {}
    colors["data"] = "blue"
    colors["base"] = "dimgrey"
    colors["main"] = "darkorange"
    colors["exp"] = "crimson"
    colors["T*"] = "green"


    def __init__(self):
        self.mainwindow()


    def pushcall(self, function):
        self.prevcall = self.currentcall
        self.currentcall = function

    def pushindex(self, new_index):
        self.previous_index = self.active_index
        self.active_index = new_index

    def mainwindow(self):
        self.pushcall(self.mainwindow)

        if self.window == None: 
            self.window = tk.Tk()
            self.window.geometry('%dx%d+%d+%d' % (740, 400, 0, 0))
            self.window.configure(bg='black')

        for widget in self.window.winfo_children():
            widget.destroy()

        self.window.title("Fajhő kiértékelő 2.0")

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=0,
            bg = "black"
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Label(master=frame, text="Mérés betöltése:", bg = "black")
        label.pack(padx=5, pady=5)

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg="#000042"
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Beállítások", bg="#00008B", command=self.optionswindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        bCalibFound = os.path.exists(".fh_config")   #FIXME na ezt most hogy deritjuk fel?


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = "#3b3b3e" if bCalibFound else "#004200"
        )
        frame.grid(row=1, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Kalibráció", bg = "#3b3b3e" if bCalibFound else "#006400", command=lambda: self.newfilewindow("Vízérték mérés", self.calibwindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = "#004200" if bCalibFound else "#3b3b3e"
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="Beejtés", bg = "#006400" if bCalibFound else "#3b3b3e", command=lambda: self.newfilewindow("Beejtéses mérés", self.beejteswindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = "#004200" if bCalibFound else "#3b3b3e"
        )
        frame.grid(row=1, column=2, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ráfűtés", bg = "#006400" if bCalibFound else "#3b3b3e", command=lambda: self.newfilewindow("Ráfűtéses mérés", self.futeswindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])



        if(self.active_measurement):
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1,
                bg = "#800080"
            )
            frame.grid(row=2, column=0, padx=5, pady=5)
            label = tk.Button(master=frame, text="Előzőt folytat", bg = "#8B008B", command=self.evalcall)
            label.pack(padx=5, pady=5)
            label_ttp = ListboxToolTip(label, ["Hello", "world"])






        self.window.columnconfigure([0,1,2,3,4], weight=1, minsize=75)
        self.window.rowconfigure([0,1,2,3,4], weight=1, minsize=50)

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.window.mainloop()



    def newfilewindow(self, mtype, command):
        for widget in self.window.winfo_children():
            widget.destroy()

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=0,
            bg = "black"
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Label(master=frame, text=mtype+" megnyitása... (másik ablak)", bg = "black")
        label.pack(padx=5, pady=5)

        temp = FHutil.new()
        if(temp):
            self.active_measurement = temp
            self.show(self.active_measurement)
            self.setfigtitle("","Figure 1")
            if(not self.active_measurement.bCalib and command != self.calibwindow):
                print("Vigyázat: még hiányoznak a kalibrációs adatok! Először a vízérték mérést értékeld ki!")
            command()
        else:
            self.currentcall()







    def framecolor(self, condition):
        return "#004200" if condition else "#3b3b3e"
    def buttoncolor(self, condition):
        return "#006400" if condition else "#3b3b3e"



    def optionswindow(self, bPushcall=True):
        if(bPushcall):
            self.pushcall(self.optionswindow)

        for widget in self.window.winfo_children():
            widget.destroy()

        self.window.title("Beállítások")

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = "#800080"
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Vissza", bg = "#8B008B", command = self.prevcall)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        '''
        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg="#000080"
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ábrázol", bg="#0000CD", command=lambda: self.show(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])
        '''

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(self.bLegend)
        )
        frame.grid(row=0, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="Legend: be" if self.bLegend else "Legend: ki", bg = self.buttoncolor(self.bLegend), command = self.toggleLegend)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(self.bAutoZoom)
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="AutoZoom: be" if self.bAutoZoom else "AutoZoom: ki", bg = self.buttoncolor(self.bAutoZoom), command = self.toggleAutoZoom)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        self.window.mainloop()

    def toggleLegend(self):
        self.bLegend = not self.bLegend
        self.show(self.active_measurement)
        self.optionswindow(bPushcall=False)


    def toggleAutoZoom(self):
        self.bAutoZoom = not self.bAutoZoom
        self.optionswindow(bPushcall=False)

    def calibwindow(self):
        self.pushcall(self.calibwindow)
        self.evalcall = self.calibwindow

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
            borderwidth=1,
            bg = "#800080"
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Vissza", bg = "#8B008B", command = self.mainwindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg="#000080"
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ábrázol", bg="#0000CD", command=lambda: self.show(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg="#000042"
        )
        frame.grid(row=1, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Beállítások", bg="#00008B", command=self.optionswindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bBase)
        )
        frame.grid(row=0, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="1) Előszakasz illesztése" if not self.active_measurement.bBase else "1) Előszakasz módosítása", bg = self.buttoncolor(not self.active_measurement.bBase), command = lambda: self.selecteloszakaszwindow(self.calibwindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bExp and self.active_measurement.bBase)
        )
        frame.grid(row=1, column=1, padx=5, pady=5)

        if(self.active_measurement.bBase):
            label = tk.Button(master=frame, text="2) Utószakasz illesztése" if not self.active_measurement.bExp else "2) Utószakasz módosítása", bg = self.buttoncolor(not self.active_measurement.bExp and self.active_measurement.bBase), command = lambda: self.selectutoszakaszwindow(self.calibwindow))
        else:
            label = tk.Label(master=frame, text="2) Utószakasz illesztése", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bTs and self.active_measurement.bExp)
        )
        frame.grid(row=2, column=1, padx=5, pady=5)
        if(self.active_measurement.bExp):
            label = tk.Button(master=frame, text="3) Korrigált hőmérséklet számolása", bg = self.buttoncolor(not self.active_measurement.bTs and self.active_measurement.bExp), command = lambda: self.calculateTs(self.calibwindow))
        else:
            label = tk.Label(master=frame, text="3) Korrigált hőmérséklet számolása", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bMainCorrected and self.active_measurement.bTs)
        )
        frame.grid(row=3, column=1, padx=5, pady=5)
        if(self.active_measurement.bTs):
            label = tk.Button(master=frame, text="4) Főszakasz illesztése" if not self.active_measurement.bMainCorrected else "4) Főszakasz módosítása", bg = self.buttoncolor(not self.active_measurement.bMainCorrected and self.active_measurement.bTs), command = lambda: self.selectfoszakaszwindow(self.calibwindow))
        else:
            label = tk.Label(master=frame, text="4) Főszakasz illesztése", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(self.active_measurement.bMainCorrected)
        )
        frame.grid(row=4, column=1, padx=5, pady=5)
        if(self.active_measurement.bMainCorrected):
            label = tk.Button(master=frame, text="5) Cp, alfa számolása", bg = self.buttoncolor(self.active_measurement.bMainCorrected), command = lambda: FHeval.calib(self.active_measurement))
        else:
            label = tk.Label(master=frame, text="5) Cp, alfa számolása", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])



        self.window.columnconfigure([0,1,2,3,4,5], weight=1, minsize=75)
        self.window.rowconfigure([0,1,2,3,4,5], weight=1, minsize=50)

        self.window.mainloop()



    def futeswindow(self):
        self.pushcall(self.futeswindow)
        self.evalcall = self.futeswindow

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
            borderwidth=1,
            bg = "#800080"
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Vissza", bg = "#8B008B", command = self.mainwindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg="#000080"
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ábrázol", bg="#0000CD", command=lambda: self.show(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg="#000042"
        )
        frame.grid(row=1, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Beállítások", bg="#00008B", command=self.optionswindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bBase)
        )
        frame.grid(row=0, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="1) Előszakasz illesztése" if not self.active_measurement.bBase else "1) Előszakasz módosítása", bg = self.buttoncolor(not self.active_measurement.bBase), command = lambda: self.selecteloszakaszwindow(self.futeswindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bExp and self.active_measurement.bBase)
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        if(self.active_measurement.bBase):
            label = tk.Button(master=frame, text="2) Utószakasz illesztése" if not self.active_measurement.bExp else "2) Utószakasz módosítása", bg = self.buttoncolor(not self.active_measurement.bExp and self.active_measurement.bBase), command = lambda: self.selectutoszakaszwindow(self.futeswindow))
        else:
            label = tk.Label(master=frame, text="2) Utószakasz illesztése", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bTs and self.active_measurement.bExp)
        )
        frame.grid(row=2, column=1, padx=5, pady=5)
        if(self.active_measurement.bExp):
            label = tk.Button(master=frame, text="3) Korrigált hőmérséklet számolása", bg = self.buttoncolor(not self.active_measurement.bTs and self.active_measurement.bExp), command = lambda: self.calculateTs(self.futeswindow))
        else:
            label = tk.Label(master=frame, text="3) Korrigált hőmérséklet számolása", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bMainCorrected and self.active_measurement.bTs)
        )
        frame.grid(row=3, column=1, padx=5, pady=5)
        if(self.active_measurement.bTs):
            label = tk.Button(master=frame, text="4) Főszakasz illesztése" if not self.active_measurement.bMainCorrected else "4) Főszakasz módosítása", bg = self.buttoncolor(not self.active_measurement.bMainCorrected and self.active_measurement.bTs), command = lambda: self.selectfoszakaszwindow(self.futeswindow))
        else:
            label = tk.Label(master=frame, text="4) Főszakasz illesztése", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(self.active_measurement.bMainCorrected)
        )
        frame.grid(row=4, column=1, padx=5, pady=5)
        if(self.active_measurement.bMainCorrected):
            label = tk.Button(master=frame, text="5) Hőkapacitás számolása", bg = self.buttoncolor(self.active_measurement.bMainCorrected), command = lambda: FHeval.rafut(self.active_measurement))
        else:
            label = tk.Label(master=frame, text="5) Hőkapacitás számolása", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])



        self.window.columnconfigure([0,1,2,3,4,5], weight=1, minsize=75)
        self.window.rowconfigure([0,1,2,3,4,5], weight=1, minsize=50)

        self.window.mainloop()



    def beejteswindow(self, setfigtitle = True):
        self.pushcall(self.beejteswindow)
        self.evalcall = self.beejteswindow

        if(not self.active_measurement):
            print("Error <FHdisplay.beejteswindow>: No active measurement")
            self.prevcall()


        for widget in self.window.winfo_children():
            widget.destroy()
        self.window.title("Beejtés kiértékelése")

        if(setfigtitle):
            self.setfigtitle("Fajhő mérése beejtéssel", "beejtes_abra")

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = "#800080"
        )
        frame.grid(row=0, column=0, padx=5, pady=5)
        label = tk.Button(master=frame, text="Vissza", bg = "#8B008B", command = self.mainwindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg="#000042"
        )
        frame.grid(row=1, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Beállítások", bg="#00008B", command=self.optionswindow)
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg="#000080"
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Ábrázol", bg="#0000CD", command=lambda: self.show(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bBase)
        )
        frame.grid(row=0, column=1, padx=5, pady=5)
        label = tk.Button(master=frame, text="1) Előszakasz illesztése" if not self.active_measurement.bBase else "1) Előszakasz módosítása", bg = self.buttoncolor(not self.active_measurement.bBase), command = lambda: self.selecteloszakaszwindow(self.beejteswindow))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])

        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bExp and self.active_measurement.bBase)
        )
        frame.grid(row=1, column=1, padx=5, pady=5)
        if(self.active_measurement.bBase):
            label = tk.Button(master=frame, text="2) Utószakasz illesztése" if not self.active_measurement.bExp else "2) Utószakasz módosítása", bg = self.buttoncolor(not self.active_measurement.bExp and self.active_measurement.bBase), command = lambda: self.selectutoszakaszwindow(self.beejteswindow))
        else:
            label = tk.Label(master=frame, text="2) Utószakasz illesztése", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(not self.active_measurement.bTs and self.active_measurement.bExp)
        )
        frame.grid(row=2, column=1, padx=5, pady=5)
        if(self.active_measurement.bExp):
            label = tk.Button(master=frame, text="3) Korrigált hőmérséklet számolása", bg = self.buttoncolor(not self.active_measurement.bTs and self.active_measurement.bExp), command = lambda: self.calculateTs(self.beejteswindow))
        else:
            label = tk.Label(master=frame, text="3) Korrigált hőmérséklet számolása", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(self.active_measurement.bExp)
        )
        frame.grid(row=3, column=1, padx=5, pady=5)
        if(self.active_measurement.bExp):
            label = tk.Button(master=frame, text="4) Integrálás", bg = self.buttoncolor(self.active_measurement.bExp), command = lambda: self.selectintegralwindow(self.beejteswindow) )
        else:
            label = tk.Label(master=frame, text="4) Integrálás", bg = "#3b3b3e")
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg = self.framecolor(self.active_measurement.bExp)
        )
        frame.grid(row=4, column=1, padx=5, pady=5)
        if(self.active_measurement.bExp):
            label = tk.Button(master=frame, text="5) Variált határú integrálás", bg = self.buttoncolor(self.active_measurement.bExp), command = lambda: self.selectSIwindow(lambda: self.beejteswindow(False)) )
        else:
            label = tk.Label(master=frame, text="5) Variált határú integrálás", bg = "#3b3b3e")
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

        #current_xlim = plt.gca().get_xlim()
        #current_ylim = plt.gca().get_ylim()

        if(bKeepZoom):
            plt.gca().lines = []
        else:
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

        colors = ["#FF00FF","#FF1493","#4B0082"]
        for i in range(len(self.rangeSelectorGuideLines)):
            xs = self.rangeSelectorGuideLines[i]
            if xs:
                plt.axvline(x = xs, color = colors[i], alpha = 0.8, linestyle = (0, (1, 1)))
        for xs in self.rangeSelectorGhosts:
            if xs:
                plt.axvline(x = xs, color = 'grey', alpha = 0.56, linestyle = (0, (1, 1)))



        if(self.scaletodata):
            plt.xlim(auto_xlim)
            plt.ylim(auto_ylim)


        if(self.bLegend):
            plt.legend()


        plt.title(self.figtitle)

        #if(bKeepZoom):
        #    plt.gca().set_xlim(current_xlim)
        #    plt.gca().set_ylim(current_ylim)
        plt.show(block=False)
        return




    def setfigtitle(self, title, wintitle):
        self.figtitle = title 
        self.show(self.active_measurement)
        self.figure.canvas.manager.set_window_title(wintitle)



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
        self.numberofranges = 2
        self.parentfunc = parent
        self.finishfunction = parent
        if(self.active_measurement.bExp):
            self.finishfunction = self.dualfitwindow
        self.evaltarget = FHeval.fitbase
        self.rangewindowtitle = "Előszakasz illesztése"

        if(self.bAutoZoom):
            FHutil.autozoom(plt, self.active_measurement, "base")
        self.rangeSelectorMainWindow()

    def selectutoszakaszwindow(self, parent):
        self.numberofranges = 2
        self.parentfunc = parent
        self.finishfunction = self.dualfitwindow
        self.evaltarget = FHeval.fitexp
        self.rangewindowtitle = "Utószakasz illesztése"

        if(self.bAutoZoom):
            FHutil.autozoom(plt, self.active_measurement, "exp")
        self.rangeSelectorMainWindow()


    def selectintegralwindow(self, parent):
        self.numberofranges = 2
        self.parentfunc = parent
        self.finishfunction = parent
        self.evaltarget = FHeval.integrate
        self.rangewindowtitle = "Integrál számítása"
        if(self.bAutoZoom):
            FHutil.autozoom(plt, self.active_measurement, "int")
        self.rangeSelectorMainWindow()


    def selectSIwindow(self, parent):
        self.numberofranges = 3
        self.parentfunc = parent
        self.finishfunction = self.drawSI
        self.evaltarget = FHeval.serialintegrateOptimized
        self.rangewindowtitle = "Integrál számítása"
        if(self.bAutoZoom):
            FHutil.autozoom(plt, self.active_measurement, "int")
        self.rangeSelectorMainWindow()

    def drawSI(self, uplims, cms, command):
        plt.clf()
        plt.plot(uplims,cms)
        plt.xlabel("Integrál felső határa (s)")
        plt.ylabel(r'$C_{m}$ $(J/K)$')
        plt.title("Variált felső határú integrálás")
        command()


    def calculateTs(self, parent):
        FHeval.getTsOptimized(self.active_measurement)
        if(self.autoshow):
            self.show(self.active_measurement)
        parent()  # needed to refresh and unlock next step button

    def selectfoszakaszwindow(self, parent):
        self.numberofranges = 2
        self.parentfunc = parent
        self.finishfunction = parent
        self.evaltarget = FHeval.fitmaincorrected
        self.rangewindowtitle = "Főszakasz illesztése"

        if(self.bAutoZoom):
            FHutil.autozoom(plt, self.active_measurement, "main")
        self.rangeSelectorMainWindow()


    def rig_for_input(self, targetf, active_index):
        self.pushindex(active_index)
        self.boundstarget = targetf
        if(not self.bCRigged):
            self.cid = self.figure.canvas.mpl_connect('button_press_event', self.onclick)
        self.bCrigged = True
        self.rig_arrows()

    def rig_arrows(self):
        if(not self.bKRigged):
            self.kid = self.figure.canvas.mpl_connect('key_press_event', self.on_press)
        self.bKRigged = True




    def modifyRangeSelect(self, new_targetf, new_index):
        self.pushindex(new_index)
        self.boundstarget = new_targetf

        self.modifybuffer = self.aBounds[new_index]
        self.aBounds[new_index] = False
        self.rangeSelectorGhosts[new_index] = self.rangeSelectorGuideLines[new_index]
        self.rangeSelectorGuideLines[new_index] = False

        self.bModifying = True
        self.show(self.active_measurement, True)
        self.updateRangeSelectorMainWindow()


    def cancelModify(self):
        self.aBounds[self.active_index] = self.modifybuffer
        self.rangeSelectorGhosts[self.active_index] = False
        self.rangeSelectorGuideLines[self.active_index] = self.modifybuffer
        self.modifybuffer = -1
        self.bModifying = False
        self.updateRangeSelectorMainWindow()


    def cancelrangeselect(self, function):
        self.parentfunc = None
        self.evaltarget = None
        self.rangeSelectorGuideLines = [False, False, False]
        self.rangeSelectorGhosts = [False, False, False]
        self.show(self.active_measurement)
        self.backfromrangeselect(function)

    def backfromrangeselect(self, function):
        self.stop_input()
        function()

    def stop_input(self):
        if(self.bCRigged):
            self.figure.canvas.mpl_disconnect(self.cid)
        if(self.bKRigged):
            self.figure.canvas.mpl_disconnect(self.kid)
        self.bCRigged = False
        self.bKRigged = False

    def onclick(self,event):
        #print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
        #  ('double' if event.dblclick else 'single', event.button,
        #   event.x, event.y, event.xdata, event.ydata))


        if(event.dblclick or event.button == 2):
            if(self.active_index == 0 and self.aBounds[1]):
                if(self.aBounds[1] < event.xdata):
                    print("A magas határ nem lehet kisebb az alacsonynál!")
                    return False 

            if(self.active_index == 1):
                if(self.aBounds[0] > event.xdata):
                    print("A magas határ nem lehet kisebb az alacsonynál!")
                    return False 
                if(self.aBounds[2]):
                    if(self.aBounds[2] < event.xdata):
                        print("A felső magas határ nem lehet kisebb az alacsonyabbnál!")
                        return False 

            if(self.active_index == 2):
                if(self.aBounds[1] > event.xdata):
                    print("A felső magas határ nem lehet kisebb az alacsonyabbnál!")
                    return False

            self.bModifying = False
            self.stop_input()
            self.aBounds[self.active_index] = event.xdata
            self.rangeSelectorGuideLines[self.active_index] = event.xdata
            self.rangeSelectorGhosts[self.active_index] = False

            self.boundstarget()
            return True
        return False
    
    def on_press(self,event):
        if self.bModifying:
            return False

        if self.previous_index <= 1 and self.aBounds[self.previous_index + 1]:
            if event.key == 'right' and self.aBounds[self.previous_index] + 0.5 > self.aBounds[self.previous_index + 1]:
                return False

        if self.previous_index >= 1 and self.aBounds[self.previous_index - 1]:
            if event.key == 'left' and self.aBounds[self.previous_index] - 0.5 < self.aBounds[self.previous_index - 1]:
                return False


        if event.key == 'right':
            self.aBounds[self.previous_index] += 0.5
            self.rangeSelectorGuideLines[self.previous_index] += 0.5
            self.show(self.active_measurement, True)
            

            colors = ["#FF00FF","#FF1493","#4B0082"]
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1, 
                bg = colors[self.previous_index]
            )
            frame.grid(row=self.previous_index, column=1, padx=5, pady=5)
            texts = ["Alsó határ: ", "Felső határ: " if self.numberofranges == 2 else "Felső határ 1: ", "Felső határ 2: "]  
            label = tk.Label(master=frame, text=texts[self.previous_index]+str(self.aBounds[self.previous_index]), bg = colors[self.previous_index])
            label.pack(padx=5, pady=5)

            return True
        elif event.key == 'left':
            # FIXME ezzel se lehessen 0 ala vinni!!!!
            self.aBounds[self.previous_index] -= 0.5
            self.rangeSelectorGuideLines[self.previous_index] -= 0.5
            self.show(self.active_measurement, True)

            colors = ["#FF00FF","#FF1493","#4B0082"]
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1, 
                bg = colors[self.previous_index]
            )
            frame.grid(row=self.previous_index, column=1, padx=5, pady=5)
            texts = ["Alsó határ: ", "Felső határ: " if self.numberofranges == 2 else "Felső határ 1: ", "Felső határ 2: "]  
            label = tk.Label(master=frame, text=texts[self.previous_index]+str(self.aBounds[self.previous_index]), bg = colors[self.previous_index])
            label.pack(padx=5, pady=5)

            return True
        return False
        




    def rangeSelectorMainWindow(self):
        self.pushcall(self.rangeSelectorMainWindow)

        self.bCRigged = False
        self.bKRigged = False
        self.bModifying = False
        self.aBounds = [False, False, False]
        self.rangeSelectorGuideLines = [False, False, False]
        self.rangeSelectorGhosts = [False, False, False]
        self.updateRangeSelectorMainWindow()

    def updateRangeSelectorMainWindow(self):
        for widget in self.window.winfo_children():
            widget.destroy()

        self.window.title(self.rangewindowtitle)

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


        if(not self.aBounds[0]):
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1,
                bg = self.framecolor(True)
            )
            frame.grid(row=0, column=1, padx=5, pady=5)
            label = tk.Label(master=frame, text="Alsó határ: <ábrán dupla katt>", bg = self.framecolor(True))
            label.pack(padx=5, pady=5)

            self.rig_for_input(self.updateRangeSelectorMainWindow, 0)

            if(self.bModifying):
                frame = tk.Frame(
                    master=self.window,
                    relief=tk.RAISED,
                    borderwidth=1
                )
                frame.grid(row=0, column=2, padx=5, pady=5)
                label = tk.Button(master=frame, text="(Mégse módosít)", command = self.cancelModify)
                label.pack(padx=5, pady=5)
                label_ttp = ListboxToolTip(label, ["Hello", "world"])
        else:
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1,
                bg = "#FF00FF"
            )
            frame.grid(row=0, column=1, padx=5, pady=5)
            label = tk.Label(master=frame, text="Alsó határ: "+str(self.aBounds[0]), bg = "#FF00FF")
            label.pack(padx=5, pady=5)


            if(not self.bModifying):
                frame = tk.Frame(
                    master=self.window,
                    relief=tk.RAISED,
                    borderwidth=1
                )
                frame.grid(row=0, column=2, padx=5, pady=5)
                label = tk.Button(master=frame, text="(Módosít)", command = lambda: self.modifyRangeSelect(self.updateRangeSelectorMainWindow, 0)) # FIXME
                label.pack(padx=5, pady=5)
                label_ttp = ListboxToolTip(label, ["Hello", "world"])

        if(not self.aBounds[1] and self.aBounds[0]):
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1,
                bg = self.framecolor(True)
            )
            frame.grid(row=1, column=1, padx=5, pady=5)
            label = tk.Label(master=frame, text="Felső határ: <ábrán dupla katt>", bg = self.framecolor(True))
            label.pack(padx=5, pady=5)    

            self.rig_for_input(self.updateRangeSelectorMainWindow, 1)

            if(self.bModifying):
                frame = tk.Frame(
                    master=self.window,
                    relief=tk.RAISED,
                    borderwidth=1
                )
                frame.grid(row=1, column=2, padx=5, pady=5)
                label = tk.Button(master=frame, text="(Mégse módosít)", command = self.cancelModify)
                label.pack(padx=5, pady=5)
                label_ttp = ListboxToolTip(label, ["Hello", "world"])
        elif(self.aBounds[1]):
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1,
                bg = "#FF1493"
            )
            frame.grid(row=1, column=1, padx=5, pady=5)
            label = tk.Label(master=frame, text="Felső határ: "+str(self.aBounds[1]) if self.numberofranges == 2 else "Felső határ 1: "+str(self.aBounds[1]), bg = "#FF1493")   # FIXME csak akkor 1 ha 3 hataros van
            label.pack(padx=5, pady=5)


            if(not self.bModifying):
                frame = tk.Frame(
                    master=self.window,
                    relief=tk.RAISED,
                    borderwidth=1
                )
                frame.grid(row=1, column=2, padx=5, pady=5)
                label = tk.Button(master=frame, text="(Módosít)", command = lambda: self.modifyRangeSelect(self.updateRangeSelectorMainWindow, 1))
                label.pack(padx=5, pady=5)
                label_ttp = ListboxToolTip(label, ["Hello", "world"])

        if(not self.aBounds[2] and self.aBounds[1] and self.numberofranges == 3):
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1,
                bg = self.framecolor(True)
            )
            frame.grid(row=2, column=1, padx=5, pady=5)
            label = tk.Label(master=frame, text="Felső határ 2: <ábrán dupla katt>", bg = self.framecolor(True))
            label.pack(padx=5, pady=5)


            self.rig_for_input(self.updateRangeSelectorMainWindow, 2)
            if(self.bModifying):
                frame = tk.Frame(
                    master=self.window,
                    relief=tk.RAISED,
                    borderwidth=1
                )
                frame.grid(row=2, column=2, padx=5, pady=5)
                label = tk.Button(master=frame, text="(Mégse módosít)", command = self.cancelModify)
                label.pack(padx=5, pady=5)
                label_ttp = ListboxToolTip(label, ["Hello", "world"])
        elif(self.aBounds[2]):
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1,
                bg = "#4B0082"
            )
            frame.grid(row=2, column=1, padx=5, pady=5)
            label = tk.Label(master=frame, text="Felső határ 2: "+str(self.aBounds[2]), bg = "#4B0082")
            label.pack(padx=5, pady=5)

            if(not self.bModifying):
                frame = tk.Frame(
                    master=self.window,
                    relief=tk.RAISED,
                    borderwidth=1
                )
                frame.grid(row=2, column=2, padx=5, pady=5)
                label = tk.Button(master=frame, text="(Módosít)", command = lambda: self.modifyRangeSelect(self.updateRangeSelectorMainWindow, 2))
                label.pack(padx=5, pady=5)
                label_ttp = ListboxToolTip(label, ["Hello", "world"])


        frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1,
            bg="#000080"
        )
        frame.grid(row=0, column=3, padx=5, pady=5)
        label = tk.Button(master=frame, text="Zoom reset", bg="#0000CD", command=lambda: self.show(self.active_measurement))
        label.pack(padx=5, pady=5)
        label_ttp = ListboxToolTip(label, ["Hello", "world"])


        if(not self.bModifying and (self.aBounds[2] > 1 or (self.aBounds[1] > 1 and self.numberofranges == 2))):
            frame = tk.Frame(
                master=self.window,
                relief=tk.RAISED,
                borderwidth=1,
                bg = self.framecolor(True)
            )
            frame.grid(row=3, column=1, padx=5, pady=5)
            label = tk.Button(master=frame, text=self.rangewindowtitle, bg = self.buttoncolor(True), command = self.rangeSelectorFinish)
            label.pack(padx=5, pady=5)

            self.pushindex(self.numberofranges)
            self.rig_arrows()

        

        self.window.columnconfigure([0,1,2,3], weight=1, minsize=75)
        self.window.rowconfigure([0,1,2,3], weight=1, minsize=50)
        self.window.columnconfigure(1, weight=4, minsize=200)

        self.show(self.active_measurement, bKeepZoom=True)
        self.window.mainloop()



    def rangeSelectorFinish(self):
        self.stop_input()
        self.rangeSelectorGuideLines = [False, False, False]
        self.rangeSelectorGhosts = [False, False, False]
        if(self.numberofranges == 2):
            self.evaltarget(self.active_measurement, self.aBounds[0], self.aBounds[1])
            self.show(self.active_measurement)
            self.finishfunction()
        else:
            uplims, cms = self.evaltarget(self.active_measurement, self.aBounds[0], self.aBounds[1], self.aBounds[2])
            self.show(self.active_measurement)
            if(uplims and cms):
                self.finishfunction(uplims, cms, self.parentfunc)






