import logging
import os
import threading
from logging.handlers import RotatingFileHandler
from src.Configs import LOGGER_PATH


class Logger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, log_file=f"{LOGGER_PATH}/gui.log", log_level=logging.DEBUG):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(Logger, cls).__new__(cls)
                    cls._instance._initialize(log_file, log_level)
        return cls._instance

    def _initialize(self, log_file, log_level):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.logger = logging.getLogger("AppLogger")
        self.logger.setLevel(log_level)

        if not self.logger.hasHandlers():  # 避免重複加 handler
            # 改成使用 RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                mode='a',
                maxBytes=20 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.info("-" * 50)

    def get_logger(self):
        return self.logger