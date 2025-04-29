import os
import sys
from pathlib import Path

APP_NAME = "SPI Component Visualization"  # Replace with your application name

# Choose the appropriate path based on the execution environment
if getattr(sys, 'frozen', False):
    # When packaged as an exe, editable files are placed in APPDATA
    SYSTEM_DIR = sys._MEIPASS
    APPDATA_DIR = os.path.join(os.environ.get('APPDATA', ''), APP_NAME)
else:
    # In the development environment, all files use the same base path
    SYSTEM_DIR = os.getcwd()
    APPDATA_DIR = os.path.join(os.getcwd(), ".local_app_data")


# Directory Paths
LOGGER_PATH = os.path.join(APPDATA_DIR, "log")

# File Paths
QT_SETTINGS_PATH = os.path.join(APPDATA_DIR, "settings.ini")

for key, val in list(globals().items()):
    if (
        key.isupper()
        and isinstance(val, str)
        and val.startswith((SYSTEM_DIR, APPDATA_DIR))
        and not os.path.exists(val)
        and not Path(val).suffix
    ):
    # if key.isupper() and isinstance(val, str) and val.startswith((f"{SYSTEM_DIR}", f"{APPDATA_DIR}")) and not os.path.exists(val):
        os.makedirs(val, exist_ok=True)
