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

# Create logger
debug_logger = logging.getLogger('Debugger')
logger = logging.getLogger('Autopilot')

# Set log level
logger.setLevel(logging.INFO)
debug_logger.setLevel(logging.DEBUG)

# Create handlers
stream = logging.StreamHandler()
file = logging.FileHandler('logs/autopilot.log')
debug_stream = logging.StreamHandler()
debug_file = logging.FileHandler('logs/Debug.log')

# Set log formatter
formatter = ColorFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
debug_formatter = ColorFormatter('%(asctime)s - %(name)s - %(message)s')
stream.setFormatter(formatter)
file.setFormatter(formatter)
debug_stream.setFormatter(debug_formatter)
debug_file.setFormatter(debug_formatter)

# Add handlers to logger
logger.addHandler(stream)
logger.addHandler(file)
debug_logger.addHandler(debug_stream)
debug_logger.addHandler(debug_file)

# reset log files
open('logs/autopilot.log', 'w').close()
open('logs/Debug.log', 'w').close()