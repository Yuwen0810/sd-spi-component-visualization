# src/Utils/Log.py
import logging
import os
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter

from src.Configs import LOGGER_PATH

# 確保 logs 資料夾存在
os.makedirs('logs', exist_ok=True)

# 彩色格式器 (Console 用)
color_formatter = ColoredFormatter(
    '%(log_color)s[%(asctime)s] %(levelname)s %(name)s:\t%(message)s',
    datefmt='%H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)

# 普通格式器 (File 用)
file_formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s %(name)s:\t%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(color_formatter)

# Rotating File Handler
file_handler = RotatingFileHandler(
    mode='a',
    filename=f'{LOGGER_PATH}/app.log',     # 檔案路徑
    maxBytes=20*1024*1024,        # 最大 5MB
    backupCount=3,               # 保留 3 個備份 (app.log.1, app.log.2 ...)
    encoding='utf-8'
)
file_handler.setFormatter(file_formatter)

# 設定 root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# 防止重複加 handler
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

logger.propagate = False
