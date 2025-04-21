from dataclasses import dataclass

from queue import Queue
from typing import TYPE_CHECKING

# Import necessary libraries
from PyQt6.QtCore import QThread, pyqtSignal

from src.Models.Components.SpiComponentManager import SpiComponentManager

if TYPE_CHECKING:
    from src.Models.DataClasses.SpiComponent import SpiComponent
    from src.Models.DataClasses.CanvasConfig import CanvasConfig


@dataclass
class UpdateComponentTask:
    spi_component_manager: SpiComponentManager
    canvas_config: "CanvasConfig"

class UpdateComponentThread(QThread):

    update_progress_signal = pyqtSignal(int)
    update_progress_desc_signal = pyqtSignal(str)

    task_queue = Queue()

    def __init__(self):
        super().__init__()
        self.is_running = False  # Initially not running

    def add_task(self, spi_component_manager: SpiComponentManager, canvas_config: "CanvasConfig"):
        task = UpdateComponentTask(spi_component_manager, canvas_config)
        if task not in self.task_queue.queue:
            self.task_queue.put(task)  # Put the dataclass object into the queue

        if not self.is_running:
            self.is_running = True
            self.start()

    def run(self):
        while not self.task_queue.empty():
            task: UpdateComponentTask = self.task_queue.get()
            self.processing(task.spi_component_manager, task.canvas_config)
            self.task_queue.task_done()

        self.is_running = False

    def processing(self, spi_component_manager: SpiComponentManager, canvas_config: "CanvasConfig"):

        scaling_ratio = canvas_config.scaling_ratio
        offset_y, offset_x = canvas_config.offset_to_center
        x_min = canvas_config.component_x_min
        y_min = canvas_config.component_y_min
        margin = canvas_config.margin

        self.update_progress_desc_signal.emit("Updating components")
        component: "SpiComponent"
        for i, component in enumerate(spi_component_manager):
            if i % 10 == 0:
                self.update_progress_desc_signal.emit(f"Updating components ({i/len(spi_component_manager):.1%})")

            component.canvas_pos_x = int((component.pos_x - x_min) * scaling_ratio + margin + offset_x)
            component.canvas_pos_y = int((component.pos_y - y_min) * scaling_ratio + margin + offset_y)
