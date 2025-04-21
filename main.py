# Built-in Imports
import os
import sys
import cgitb
import traceback

# Data Science and Third Party Imports

# Machine Learning Imports

# PyQt Imports
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint, QSharedMemory
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QMainWindow, QSplitter, QSplashScreen

# User Imports
from src.Models.Logger import Logger
from src.Views.QtDesigner.MainWindow import Ui_MainWindow
from src.Controllers.MainController import MainController
from src.Configs.PathConfigs import QT_SETTINGS_PATH
import src.Views.QtDesigner.IconsRc

cgitb.enable(format='text')
# logger = Logger().get_logger()
# logger.info("-" * 50)


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Resize and Move Event Timer
        self.window_change_timer = QtCore.QTimer()
        self.window_change_timer.setInterval(300)
        self.window_change_timer.setSingleShot(True)
        self.window_change_timer.timeout.connect(self.save_window_state)

        # Initialize the Main Controller
        self.main_controller = MainController(self.ui)

        # Initialize the QSettings
        self.q_settings = QSettings(QT_SETTINGS_PATH, QSettings.Format.IniFormat)
        self.sync_widgets = (
            # (Widget, Default Value)
            (self.ui.lineEditFilePath, ""),
            (self.ui.pushButtonSelectType, True),
            (self.ui.pushButtonSelectId, False),
        )

        # Set the default input and output path
        for widget, default_val in self.sync_widgets:
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(self.q_settings.value(widget.objectName(), default_val))
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.setCurrentIndex(int(self.q_settings.value(widget.objectName(), default_val)))
            elif isinstance(widget, QtWidgets.QSpinBox):
                widget.setValue(int(self.q_settings.value(widget.objectName(), default_val)))
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                widget.setValue(float(self.q_settings.value(widget.objectName(), default_val)))
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(self.q_settings.value(widget.objectName(), default_val, type=bool))
            elif isinstance(widget, QtWidgets.QRadioButton):
                widget.setChecked(self.q_settings.value(widget.objectName(), default_val, type=bool))
            elif isinstance(widget, QtWidgets.QPushButton) and widget.isCheckable():
                widget.setChecked(self.q_settings.value(widget.objectName(), default_val, type=bool))

        def get_sync_callback(q_widget):
            return lambda text: self.q_settings.setValue(q_widget.objectName(), text)

        # Connect sync widgets to q_settings
        for widget, _ in self.sync_widgets:
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.textChanged.connect(get_sync_callback(widget))
            elif isinstance(widget, QtWidgets.QComboBox):
                widget.currentIndexChanged.connect(get_sync_callback(widget))
            elif isinstance(widget, QtWidgets.QSpinBox):
                widget.valueChanged.connect(get_sync_callback(widget))
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                widget.valueChanged.connect(get_sync_callback(widget))
            elif isinstance(widget, QtWidgets.QCheckBox):
                widget.stateChanged.connect(get_sync_callback(widget))
            elif isinstance(widget, QtWidgets.QRadioButton):
                widget.toggled.connect(get_sync_callback(widget))
            elif isinstance(widget, QtWidgets.QPushButton) and widget.isCheckable():
                widget.toggled.connect(get_sync_callback(widget))

        def get_splitter_move_callback(obj: QSplitter):
            return lambda: self.save_spitter_state(f"{obj.objectName()}_size", obj)

        # Monitor splitter changes
        for splitter in self.ui.centralwidget.findChildren(QSplitter):
            splitter.splitterMoved.connect(get_splitter_move_callback(splitter))

        # Restore window and splitter q_settings
        self.prev_window_size = self.q_settings.value("window_size", QSize(1000, 700))
        self.prev_window_position = self.q_settings.value("window_position", QPoint(100, 100))
        self.restore_window_state()

    def save_spitter_state(self, key: str, splitter: QSplitter):
        self.q_settings.setValue(key, splitter.sizes())

    def restore_window_state(self):
        self.resize(self.prev_window_size)
        self.move(self.prev_window_position)

        # Restore splitter ratios
        for splitter in self.ui.centralwidget.findChildren(QSplitter):
            if sizes := self.q_settings.value(f"{splitter.objectName()}_size"):
                splitter.setSizes([int(size) for size in sizes])

    def save_window_state(self):
        if self.isMaximized():
            self.q_settings.setValue("is_maximized", True)
        else:
            self.q_settings.setValue("is_maximized", False)
            self.q_settings.setValue("window_size", self.size())
            self.q_settings.setValue("window_position", self.pos())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.window_change_timer.start()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.window_change_timer.start()

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.Type.WindowStateChange:
            self.window_change_timer.start()
        super().changeEvent(event)

    def keyPressEvent(self, event):
        ...


class SplashScreen:
    def __init__(self, title="Application Launching", message="Please wait while the system starts...", min_width=300, min_height=80):
        # Fonts for title and message
        title_font = QtGui.QFont("Arial", 11, QtGui.QFont.Weight.Bold)
        message_font = QtGui.QFont("Arial", 10)

        # Create a temporary painter to calculate text bounding rectangles
        temp_pixmap = QPixmap(1, 1)
        temp_painter = QPainter(temp_pixmap)

        # Calculate title bounding rectangle
        temp_painter.setFont(title_font)
        title_rect = temp_painter.boundingRect(0, 0, min_width, 0, Qt.AlignmentFlag.AlignHCenter, title)

        # Calculate message bounding rectangle
        temp_painter.setFont(message_font)
        message_rect = temp_painter.boundingRect(0, 0, min_width, 0, Qt.AlignmentFlag.AlignHCenter, message)

        temp_painter.end()

        # Calculate total dimensions
        padding = 20
        text_width = max(title_rect.width(), message_rect.width())
        text_height = title_rect.height() + message_rect.height() + padding  # Add padding between title and message

        # Ensure minimum dimensions
        splash_width = max(text_width + padding * 2, min_width)
        splash_height = max(text_height + padding * 2, min_height)

        # Create the splash screen pixmap
        splash_pix = QPixmap(splash_width, splash_height)
        splash_pix.fill(Qt.GlobalColor.white)

        # Draw the border and text
        painter = QPainter(splash_pix)
        pen = QPen(QColor("#d8d8d8"))  # Black border
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(splash_pix.rect().adjusted(0, 0, -1, -1))

        # Calculate vertical positions for title and message
        center_y = splash_height // 2
        title_y = center_y - (title_rect.height() // 2) - padding  # Adjust title slightly above center
        message_y = center_y + (message_rect.height() // 2)  # Adjust message slightly below center

        # Draw the title
        painter.setFont(title_font)
        painter.setPen(QColor("#000000"))  # Black color for title
        painter.drawText(
            splash_pix.rect().adjusted(0, title_y, 0, 0),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            title
        )

        # Draw the message
        painter.setFont(message_font)
        painter.setPen(QColor("#555555"))  # Dark gray color for message
        painter.drawText(
            splash_pix.rect().adjusted(0, message_y, 0, 0),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            message
        )

        painter.end()

        # Initialize the QSplashScreen
        self.splash = QSplashScreen(splash_pix)

    def show(self):
        """Show the splash screen."""
        self.splash.show()

    def finish(self, window):
        """Close the splash screen and transfer control to the main window."""
        self.splash.finish(window)



if __name__ == '__main__':
    # loop bug: https://github.com/ultralytics/ultralytics/issues/3997
    import multiprocessing
    multiprocessing.freeze_support()

    # Unique key for the application
    shared_memory_key = "SoftwareName"
    shared_memory = QSharedMemory(shared_memory_key)
    if not shared_memory.create(1):  # Try to create shared memory
        sys.exit(0)

    try:
        app = QtWidgets.QApplication(sys.argv)
        app.setStyle('windowsvista')

        splash = SplashScreen()
        splash.show()

        window = MainWindow()
        if window.q_settings.value("is_maximized", False, type=bool):
            window.showMaximized()
        else:
            window.show()
        splash.finish(window)

        sys.exit(app.exec())

    except Exception as e:
        error_msg = f"An error occurred:\n\n{str(e)}\n\n{traceback.format_exc()}"
        sys.exit(1)