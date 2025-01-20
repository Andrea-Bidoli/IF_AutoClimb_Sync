from colorama import Fore, Back, Style, init
from pathlib import Path
import logging

init(autoreset=True)



class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Back.RED + Fore.WHITE,
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, Style.RESET_ALL)
        message = super().format(record)
        return f"{log_color}{message}{Style.RESET_ALL}"

class Filter(logging.Filter):
    def __init__(self, name = "", debug = False):
        super().__init__(name)
        self.debug = debug
    def toggle_debug(self):
        self.debug = not self.debug
    def filter(self, record):
        if not self.debug:
            return record.levelno != logging.DEBUG
        else:
            return True
    
class Logger(logging.Logger):
    def toggle_debug(self):
        self._filter.toggle_debug()
    def __init__(self, name: str, level: int = logging.INFO):
        super().__init__(name, level)
        self.propagate = False
        self.stream_handler = logging.StreamHandler()
        stream_formatter = ColorFormatter(
            "{asctime} - {name} - {funcName!r}: {message}",
            datefmt="%Y-%m-%d %H:%M:%S",
            style="{"
        )
        self.stream_handler.setFormatter(stream_formatter)
        self._filter = Filter(name, False)
        self.stream_handler.addFilter(self._filter)
        self.addHandler(self.stream_handler)

        log_dir = Path("./logs")
        if not log_dir.is_dir():
            log_dir.mkdir()
        file = logging.FileHandler(f"logs/{name}.log")
        self.file_reset()
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file.setFormatter(file_formatter)
        self.addHandler(file)

    def file_reset(self):
        open(f"logs/{self.name}.log", "w").close()





# Create logger
debug_logger = Logger("Debugger", logging.DEBUG)
logger = Logger("Autopilot", logging.INFO)
    
