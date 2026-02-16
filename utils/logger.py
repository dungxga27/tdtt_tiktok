from utils.colors import Color
from datetime import datetime

def log_info(message):
    print(f"{Color.BRIGHT_GREEN}[INFO]{Color.RESET} {message}")


def log_error(message):
    print(f"{Color.BRIGHT_RED}[ERROR]{Color.RESET} {message}")


def log_warning(message):
    print(f"{Color.BRIGHT_YELLOW}[WARNING]{Color.RESET} {message}")