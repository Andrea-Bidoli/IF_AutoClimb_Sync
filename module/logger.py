import logging
from colorama import Fore, Back, Style, init

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


class Logger(logging.Logger):
    def __init__(self, name: str, level: int = logging.DEBUG):
        super().__init__(name, level)
        self.propagate = False
        stream = logging.StreamHandler()
        file = logging.FileHandler(f"logs/{name}.log")
        self.file_reset()
        stream_formatter = ColorFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stream.setFormatter(stream_formatter)
        file.setFormatter(file_formatter)
        self.addHandler(stream)
        self.addHandler(file)

    def file_reset(self):
        open(f"logs/{self.name}.log", "w").close()


# Create logger
debug_logger = Logger("Debugger", logging.DEBUG)
logger = Logger("Autopilot", logging.INFO)
