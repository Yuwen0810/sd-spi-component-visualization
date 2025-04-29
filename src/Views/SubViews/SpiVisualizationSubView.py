# Built-in Imports
import os
from queue import Queue
from typing import Union

# Data Science and Third Party Imports
import numpy as np

# Machine Learning Imports

# PyQt Imports
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QMovie, QPixmap, QDragEnterEvent, QDragLeaveEvent, QAction
from PyQt6.QtWidgets import QGridLayout, QFrame, QPushButton, QLabel, QStackedWidget, QComboBox, QLineEdit, QTreeWidget, \
    QButtonGroup, QWidget, QFileDialog, QStatusBar

from src.Utils.SystemVariable import SystemVariable
from src.Views.CustomWidgets.CheckableTreeWidget import CheckableTreeWidget
from src.Views.CustomWidgets.CustomGraphicsView import CustomGraphicsView
# User Imports
from src.Views.QtDesigner.MainWindow import Ui_MainWindow

# Logger
import logging
logger = logging.getLogger(__name__)


class SpiVisualizationSubView:

    def __init__(self, ui: Ui_MainWindow):

        self.system_variable: SystemVariable = SystemVariable()

        self.statusBar: QStatusBar = ui.statusBar
        self.actionSetCanvas: QAction = ui.actionSetCanvas

        self.frameWindow: QFrame = ui.frameWindow
        self.frameWorkspace: QFrame = ui.frameWorkspace

        self.pushButtonLoadFile: QPushButton = ui.pushButtonLoadFile
        self.pushButtonOpenInExplorer: QPushButton = ui.pushButtonOpenInExplorer

        self.labelProduct: QLabel = ui.labelProduct
        self.labelIdno: QLabel = ui.labelIdno
        self.comboBoxLineId: QComboBox = ui.comboBoxLineId
        self.comboboxPanelId: QComboBox = ui.comboBoxPanelId
        self.pushButtonSelectId: QPushButton = ui.pushButtonSelectId
        self.pushButtonSelectSize: QPushButton = ui.pushButtonSelectSize
        self.selectionModeButtonGroup = QButtonGroup()
        self.selectionModeButtonGroup.addButton(self.pushButtonSelectId, 1)  # ID 1
        self.selectionModeButtonGroup.addButton(self.pushButtonSelectSize, 2)  # ID 2

        self.stackedWidgetSelectionMode: QStackedWidget = ui.stackedWidgetSelectionMode
        self.pageSelectSize: QWidget = ui.pageSelectSize
        self.pageSelectId: QWidget = ui.pageSelectId

        self.lineEditFilePath: QLineEdit = ui.lineEditFilePath
        self.treeWidgetSelectSize: CheckableTreeWidget = ui.treeWidgetSelectSize
        self.treeWidgetSelectId: CheckableTreeWidget = ui.treeWidgetSelectId

        self.graphicsView: CustomGraphicsView = ui.graphicsView

        ...

        # Signals and Slots
        self.pushButtonLoadFile.clicked.connect(self.on_load_input_file_clicked)
        self.pushButtonOpenInExplorer.clicked.connect(
            lambda: os.startfile(os.path.dirname(self.lineEditFilePath.text()))
        )

        # File Drag Event
        self.frameWindow.setAcceptDrops(True)  # Open When Model is Ready
        self.frameWindow.dragEnterEvent = self.file_drag_enter_event
        self.frameWindow.dropEvent = self.file_drop_event
        self.frameWindow.dragLeaveEvent = self.file_drag_leave_event

    def on_load_input_file_clicked(self):
        file_url, _ = QFileDialog.getOpenFileName(
            None,
            'Open File',
            self.lineEditFilePath.text(),
            'Supported Files (*.xlsx *.csv);;Excel Files (*xls *.xlsx);;Csv Files (*.csv)'
        )
        if file_url:
            self.lineEditFilePath.setText(file_url)

    def file_drag_enter_event(self, event: QDragEnterEvent):
        # Check if the dragged file extension is valid
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            file_extension = file_path.split('.')[-1].lower()

            # Set valid extensions
            valid_extensions = ['xlsx', 'csv']

            if file_extension in valid_extensions:
                self.frameWindow.setStyleSheet("#frameWindow {border: 2px solid blue;}")
            else:
                self.frameWindow.setStyleSheet("#frameWindow {border: 2px solid red;}")

            # Accept the event regardless of file type, so drop_event will be triggered
            event.accept()
        else:
            event.ignore()

    def file_drop_event(self, event):
        # Process the dropped file
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            file_extension = file_path.split('.')[-1].lower()
            valid_extensions = ['xlsx', 'csv']

            if file_extension in valid_extensions:
                # Only set the path if file type is valid
                self.lineEditFilePath.setText(file_path)

            # Clear the frame style in any case
            self.frameWindow.setStyleSheet("")
            event.accept()
        else:
            self.frameWindow.setStyleSheet("")
            event.ignore()

    def file_drag_leave_event(self, event: QDragLeaveEvent):
        self.frameWindow.setStyleSheet("")
        event.accept()


if __name__ == "__main__":
    ...
