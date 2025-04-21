# Built-in Imports

# Data Science and Third Party Imports

# Machine Learning Imports

# PyQt Imports

# User Imports
from src.Models.Enums.ControllerEnum import ControllerEnum
from src.Models.Enums.EventEnum import EventEnum

from src.Views.QtDesigner.MainWindow import Ui_MainWindow
from src.Views.SubViews.SpiVisualizationSubView import SpiVisualizationSubView
from src.Controllers.SpiVisualizationController import SpiVisualizationController


class MainController:

    def __init__(self, ui: Ui_MainWindow, *args, **kwargs):

        self.ui: Ui_MainWindow = ui

        # View initialization
        self.spi_visualization_subview = SpiVisualizationSubView(self.ui)

        # Controller initialization
        self.spi_visualization_controller = SpiVisualizationController(self, self.spi_visualization_subview)

    def notify(self, sender: ControllerEnum, event: EventEnum, **kwargs):
        print(f"[MainController Notify]: {sender}, {event}")
        match sender:

            case ControllerEnum.MainController:
                ...

            case ControllerEnum.SpiVisualizationController:
                ...

            case _:
                raise ValueError("Sender is not valid.")


