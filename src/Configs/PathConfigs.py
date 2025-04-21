import os
import sys

APP_NAME = "APP_NAME"  # Replace with your application name

# Choose the appropriate path based on the execution environment
if getattr(sys, 'frozen', False):
    # When packaged as an exe, editable files are placed in APPDATA
    SYSTEM_DIR = sys._MEIPASS
    APPDATA_DIR = os.path.join(os.environ.get('APPDATA', ''), APP_NAME)

else:
    # In the development environment, all files use the same base path
    SYSTEM_DIR = os.getcwd()
    APPDATA_DIR = os.path.join(os.getcwd(), ".local-appdata")

# Directory Paths
LOGGER_PATH = os.path.join(APPDATA_DIR, "log")

# File Paths
QT_SETTINGS_PATH = os.path.join(APPDATA_DIR, "settings.ini")

if not os.path.exists(APPDATA_DIR):
    os.makedirs(APPDATA_DIR)

