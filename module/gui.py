from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox


class Gui(Tk):
    def __init__(self, screenName = None, baseName = None, className = "Tk", useTk = True, sync = False, use = None):
        super().__init__(screenName, baseName, className, useTk, sync, use)
        self.title("Autopilot")
        self.geometry("800x1080")
        
        self.mainloop()



if __name__ == "__main__":
    Gui()