import curses
from .FlightPlan import IFFPL, Fix
from .aircraft import Aircraft, Autopilot
from .database import database, retrive_airplane

class App:
    def __init__(self, fpl: IFFPL, aircraft: Aircraft=None, autopilot: Autopilot=None) -> None:
        self.screen = None
        self.perf_db = {
            "V1": "",
            "VR": "",
            "V2": "",
            "Cruise Spd": "",
            "FLEX": "",
            "Flaps": "",
            "Trim": "",
        }
        self.pages = ("PERF", "FPL", "DEP", "ARR")
        self.dep_db = {}
        self.arr_db = {}
        self.fpl_db = {"fpl":fpl, "page": 0}
        self.aircraft_db = aircraft
        self.autopilot_db = autopilot

        self.input_str = ""

        curses.wrapper(self.setup_screen)

    def perf_page(self):
        self.FMC_win.clear()
        height, width  = self.FMC_win.getmaxyx()
        self.FMC_win.addstr(0, width//2 - 5, "Perf Page")
        for i, (key, value) in enumerate(self.perf_db.items(), start=0):
            cursor = ">" if i == self.selected_UpDown else " "
            self.FMC_win.addstr(i+1, 0, f"{cursor}{key}: {value}")
        self.FMC_win.addnstr(height-1, 0, "Input: " + self.input_str, width)
        self.FMC_win.refresh()

    def dep_page(self):
        self.FMC_win.clear()
        height, width  = self.FMC_win.getmaxyx()
        self.FMC_win.addstr(0, width//2 - 4, "Dep Page")

        self.FMC_win.addnstr(height-1, 0, "Input: " + self.input_str, width)
        self.FMC_win.refresh()
        
    def arr_page(self):
        self.FMC_win.clear()
        height, width  = self.FMC_win.getmaxyx()
        self.FMC_win.addstr(0, width//2 - 4, "Arr Page")

        self.FMC_win.addnstr(height-1, 0, "Input: " + self.input_str, width)
        self.FMC_win.refresh()

    def fpl_page(self):
        self.FMC_win.clear()
        height, width  = self.FMC_win.getmaxyx()
        page = self.fpl_db["page"]
        fpl: IFFPL = self.fpl_db["fpl"]
        start_index = page*(height-2)
        end_index = start_index + height-2
        self.FMC_win.addstr(0, width//2 - 5, "FPL Page")
        self.FMC_win.addnstr(height-1, 0, "Input: " + self.input_str, width)

        for i, fix in enumerate(fpl[start_index:end_index], start=0):
            cursor = ">" if i == self.selected_UpDown else " "
            self.FMC_win.addstr(i+1, 0, f"{cursor}{fix.name}")
        
        self.FMC_win.refresh()
        
        
        
    def setup_screen(self, stdscr: curses.window):
        # setup the main window
        self.screen = stdscr
        curses.curs_set(False)
        self.screen.nodelay(True)
        self.screen.clear()
        self.height, self.width = self.screen.getmaxyx()
        # create 2 windows and a vertical line as separator
        self.FMC_win = curses.newwin(self.height, self.width//2, 0, 0)
        self.win2 = curses.newwin(self.height, self.width//2-1, 0, self.width//2+1)
        self.screen.vline(0, self.width//2, curses.ACS_VLINE, self.height)
        # setup the 2 windows
        self.FMC_win.clear()
        self.win2.clear()
        self.FMC_win.refresh()
        self.win2.refresh()
        self.screen.refresh()
        # start main loop of application
        self.selected_UpDown = 0
        self.selected_RightLeft = 0
        self.main_loop()
        
    def update_ui(self):
        # update all the windows and the vertical line to new size
        self.height, self.width = self.screen.getmaxyx()
        self.FMC_win.resize(self.height, self.width//2)
        self.win2.resize(self.height, self.width//2-1)
        self.screen.vline(0, self.width//2, curses.ACS_VLINE, self.height)

        self.FMC_win.refresh()
        self.win2.refresh()
        self.screen.refresh()
    
    def main_loop(self):
        while True:
            new_height, new_width = self.screen.getmaxyx()
            if (new_height, new_width) != (self.height, self.width):
                self.update_ui()

            db = getattr(self, f"{self.pages[self.selected_RightLeft].lower()}_db")
            getattr(self, f"{self.pages[self.selected_RightLeft].lower()}_page")()

            key = self.screen.getch()
            match key:
                case 27: # Escape key
                    break
                
                case curses.KEY_DOWN: # Down arrow
                    # TODO: Fix that when selected_UpDown is 0, it should go to the prev page
                    # problem could be when using len(db["fpl"]) instead of len(height-2)
                    if self.pages[self.selected_RightLeft] == "FPL":
                        self.selected_UpDown = (self.selected_UpDown + 1) % (self.height-2)
                        if self.selected_UpDown == self.height-1:
                            self.fpl_db["page"] += 1
                            self.selected_UpDown = 0
                    else:
                        self.selected_UpDown = (self.selected_UpDown + 1) % len(db)
                
                case curses.KEY_UP: # Up arrow
                    # TODO: Fix that when selected_UpDown is 0, it should go to the prev page
                    # problem could be when using len(db["fpl"]) instead of len(height-2)
                    if self.pages[self.selected_RightLeft] == "FPL":
                        self.selected_UpDown = (self.selected_UpDown - 1) % (self.height-2)
                        if self.selected_UpDown == self.height-1:
                            self.fpl_db["page"] -= 1
                            self.selected_UpDown = self.height-2
                    else:
                        self.selected_UpDown = (self.selected_UpDown - 1) % len(db)
                
                case curses.KEY_LEFT: # Left arrow
                    self.selected_RightLeft = (self.selected_RightLeft - 1) % len(self.pages)
                    self.selected_UpDown = 0
                
                case curses.KEY_RIGHT: # Right arrow
                    self.selected_RightLeft = (self.selected_RightLeft + 1) % len(self.pages)
                    self.selected_UpDown = 0

                case val if val in range(32, 127): # printable characters
                    self.input_str += chr(val)
                
                case 8 | 127 | curses.KEY_BACKSPACE: # Backspace
                    self.input_str = self.input_str[:-1]
                
                case 10: # Enter
                    if self.input_str.lower() in ("exit", "quit"):
                        break
                    if self.selected_RightLeft != 1:
                        db_key = list(db.keys())[self.selected_UpDown]
                        db[db_key] = self.input_str
                        self.input_str = ""

            self.screen.refresh()



def main(stdscr: curses.window) -> None:
    stdscr.clear()
    stdscr.refresh()
    height, width = stdscr.getmaxyx()
    left_window = curses.newwin(height, width//2, 0, 0)
    right_window = curses.newwin(height, width//2-1, 0, width//2+1)
    stdscr.nodelay(False)
    curses.curs_set(False)
    
    database = {
        "V1":"",
        "VR":"",
        "V2":"",
    }
    
    database_keys = list(database.keys())
    
    selected = 1
    input_str = ""

    left_window.clear()
    right_window.clear()
    left_window.refresh()
    right_window.refresh()
    
    while True:
        left_window.clear()

        left_window.addstr(0, 0, "Left window")
        right_window.addstr(0, 0, "Right window")
        stdscr.vline(0, width//2, "|", height)
        
        # Draw database
        for i, (key, value) in enumerate(database.items(), start=0):
            marker = ">" if i == selected else " "
            left_window.addstr(i+1, 0, f"{marker}{key}: {value}")
        
        left_window.addstr(height-1, 0, "Input: " + input_str)
        
        left_window.refresh()
        right_window.refresh()
        stdscr.refresh()

        key = stdscr.getch()
        if key == ord("q") or key == 27:
            break
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(database)
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(database)
        elif key == 10: # Enter
            if input_str and input_str.isdigit():
                value = int(input_str)
                match selected:
                    case 0:
                        database[database_keys[selected]] = value
                    case 1:
                        if value < database["V1"]:
                            right_window.addstr(1, 0, "VR must be greater than V1\n")
                        else:
                            database[database_keys[selected]] = value
                    case 2:
                        if value < database["VR"]:
                            right_window.addstr(1, 0, "V2 must be greater than VR\n")
                        else:
                            database[database_keys[selected]] = value
                input_str = ""
                right_window.refresh()
        elif key in (127, 8, curses.KEY_BACKSPACE): # Backspace
            input_str = input_str[:-1]
        elif key in range(32, 127):
            input_str += chr(key)



if __name__ == "__main__":
    # curses.wrapper(main)
    App()