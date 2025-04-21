from dataclasses import dataclass
import os
import pandas as pd
import re
from dataclasses import fields

from queue import Queue
from typing import TYPE_CHECKING

# Import necessary libraries
from PyQt6.QtCore import QThread, pyqtSignal
from src.Models.DataClasses.SpiComponent import SpiComponent

if TYPE_CHECKING:
    from src.Models.DataClasses.CanvasConfig import CanvasConfig
    from src.Models.Components.SpiComponentManager import SpiComponentManager

@dataclass
class SpiFileTask:
    file_path: str
    spi_component_manager: "SpiComponentManager"
    canvas_config: "CanvasConfig"

class ParseSpiFileThread(QThread):

    update_progress_signal = pyqtSignal(int)
    update_progress_desc_signal = pyqtSignal(str)

    task_queue = Queue()

    def __init__(self):
        super().__init__()
        self.is_running = False  # Initially not running

    def add_task(self, file_path: str, spi_component_manager: "SpiComponentManager", canvas_config: "CanvasConfig"):
        task = SpiFileTask(file_path, spi_component_manager, canvas_config)
        if os.path.exists(file_path) and task not in self.task_queue.queue:
            self.task_queue.put(task)  # Enqueue the dataclass task object

        if not self.is_running:
            self.is_running = True
            self.start()

    def run(self):
        while not self.task_queue.empty():
            task: SpiFileTask = self.task_queue.get()
            self.processing(task.file_path, task.spi_component_manager, task.canvas_config)
            self.task_queue.task_done()

        self.is_running = False

    def processing(self, file_path: str, spi_component_manager: "SpiComponentManager", canvas_config: "CanvasConfig"):
        # Define proxy file path based on original file name
        proxy_file_path = os.path.splitext(file_path)[0] + '.parquet'
        proxy_loaded = False
        spi_component_cols = [col.name for col in fields(SpiComponent) if not col.name.startswith("canvas")]

        # Check if the proxy file already exists
        if os.path.exists(proxy_file_path):
            self.update_progress_desc_signal.emit(f"Loading proxy file: {proxy_file_path}")
            df = pd.read_parquet(proxy_file_path)
            # Ensure columns match exactly
            if set(df.columns) == set(spi_component_cols):
                proxy_loaded = True

        if not proxy_loaded:
            # Load original file according to its extension
            self.update_progress_desc_signal.emit(f"Loading original file: {file_path}")
            ext = os.path.splitext(file_path)[-1].lower()
            if ext == '.csv':
                df = pd.read_csv(file_path)
            elif ext == '.xlsx':
                df = pd.read_excel(file_path)
            elif ext == '.xls':
                df = pd.read_excel(file_path, engine='xlrd')
            else:
                raise ValueError("Unsupported file format")

            # Save the loaded DataFrame as a proxy file for future reuse
            self.update_progress_desc_signal.emit("Saving proxy file for future use")
            df.columns = [self.to_snake_case(col) for col in df.columns]
            df = df[spi_component_cols]
            df.to_parquet(proxy_file_path)

        # Update canvas configuration bounds
        self.update_progress_desc_signal.emit("Updating canvas config")
        x_min, y_min = df.loc[:, ["pos_x", "pos_y"]].min()
        x_max, y_max = df.loc[:, ["pos_x", "pos_y"]].max()

        canvas_config.component_x_min = x_min
        canvas_config.component_x_max = x_max
        canvas_config.component_y_min = y_min
        canvas_config.component_y_max = y_max

        # Instantiate SpiComponent objects from DataFrame rows
        self.update_progress_desc_signal.emit("Creating spi components")
        spi_component_manager.clear()
        for i, row in enumerate(df[spi_component_cols].to_dict(orient='records')):
            if i % 10 == 0:
                self.update_progress_desc_signal.emit(f"Creating spi components ({i / len(df):.1%})")

            spi_component_manager.add_component(SpiComponent(**row))

    @staticmethod
    def to_snake_case(s: str) -> str:
        if s in {"IDNO", "DID", "SKU", "FIDL", "MFGPN"}:
            res = s.lower()
        elif "ID" in s:
            res = s.replace("ID", "_id").lower()
        elif "BR" in s:
            res = s.replace("BR", "_br_").lower()
        elif "DB" in s:
            res = s.replace("DB", "_db_").lower()
        else:
            res = re.sub(r'(?<!^)([A-Z])', r'_\1', s).lower()

        return res.strip("_")
