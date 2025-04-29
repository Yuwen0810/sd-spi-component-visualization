# Built-in Imports
import os
import sys
import cgitb
import traceback
from src.Utils import Log

# Data Science and Third Party Imports

# Machine Learning Imports

# PyQt Imports
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint, QSharedMemory, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QMainWindow, QSplitter, QSplashScreen

from src.Utils.QtUtils import SignalBlocker
# User Imports
from src.Utils.SystemVariable import SystemVariable, ObservableProperty
from src.Configs import QT_SETTINGS_PATH, UiConfigs
from src.Views.SettingDialog import SettingDialog

# Logger
import logging

from src.Views.SplashScreen import SplashScreen

logger = logging.getLogger(__name__)
cgitb.enable(format='text')


# TODO:
#   1. 載入預設資料但路徑不存在時，不會 Crash。但之後切換檔案有 Bug，Loading 很久


class MainWindow(QMainWindow):

    def __init__(self):
        from src.Views.QtDesigner.MainWindow import Ui_MainWindow
        from src.Controllers.MainController import MainController
        import src.Views.QtDesigner.IconsRc

        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Sync system variables with settings to maintain state across sessions
        self.system_variable: SystemVariable = SystemVariable()

        # Initialize the Main Controller
        self.setting_dialog: SettingDialog = SettingDialog()
        self.main_controller = MainController(self.ui, self.setting_dialog)

        # Resize and Move Event Timer
        self.window_change_timer = QtCore.QTimer()
        self.window_change_timer.setInterval(300)
        self.window_change_timer.setSingleShot(True)
        self.window_change_timer.timeout.connect(self.save_window_state)

        # Initialize the QSettings
        self.q_settings = QSettings(QT_SETTINGS_PATH, QSettings.Format.IniFormat)
        self.sync_widgets = (
            # (Widget, Default Value)
            (self.ui.lineEditFilePath, ""),
            (self.ui.pushButtonSelectSize, True),
            (self.ui.pushButtonSelectId, False),

            (self.setting_dialog.ui.groupBoxAutoCrop, UiConfigs.DEFAULT_GROUP_BOX_AUTO_CROP),
            (self.setting_dialog.ui.groupBoxFixedSize, UiConfigs.DEFAULT_GROUP_BOX_FIXED_SIZE),
            (self.setting_dialog.ui.spinBoxSizeX, UiConfigs.DEFAULT_SPIN_BOX_SIZE_X),
            (self.setting_dialog.ui.spinBoxSizeY, UiConfigs.DEFAULT_SPIN_BOX_SIZE_Y),
            (self.setting_dialog.ui.spinBoxMaxSideLength, UiConfigs.DEFAULT_SPIN_BOX_MAX_SIDE_LENGTH),
            (self.setting_dialog.ui.spinBoxMargin, UiConfigs.DEFAULT_SPIN_BOX_MARGIN),
            (self.setting_dialog.ui.spinBoxComponentRadius, UiConfigs.DEFAULT_SPIN_BOX_COMPONENT_RADIUS),
            (self.system_variable.CANVAS_COLOR, UiConfigs.DEFAULT_CANVAS_COLOR),
        )

        # Set the default input and output path
        for widget, default_val in self.sync_widgets:
            with SignalBlocker(widget):
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
                elif isinstance(widget, QtWidgets.QGroupBox) and widget.isCheckable():
                    widget.setChecked(self.q_settings.value(widget.objectName(), default_val, type=bool))
                elif isinstance(widget, ObservableProperty):
                    widget.set_value(self.q_settings.value(widget.objectName(), default_val))
                    widget.set_default_value(default_val)

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
            elif isinstance(widget, QtWidgets.QGroupBox) and widget.isCheckable():
                widget.toggled.connect(get_sync_callback(widget))
            elif isinstance(widget, ObservableProperty):
                widget.connect(get_sync_callback(widget))

        def get_splitter_move_callback(obj: QSplitter):
            return lambda: self.save_spitter_state(f"{obj.objectName()}_size", obj)

        # Monitor splitter changes
        for splitter in self.ui.centralwidget.findChildren(QSplitter):
            splitter.splitterMoved.connect(get_splitter_move_callback(splitter))

        # Restore window and splitter q_settings
        self.prev_window_size = self.q_settings.value("window_size", QSize(1000, 700))
        self.prev_window_position = self.q_settings.value("window_position", QPoint(100, 100))
        self.restore_window_state()

        # Connect signals
        self.setting_dialog.connect_signals()
        self.main_controller.connect_signals()

        # Run the UI setup after the main window is shown
        QTimer.singleShot(0, self.run_after_ui_ready)

    def save_spitter_state(self, key: str, splitter: QSplitter):
        self.q_settings.setValue(key, splitter.sizes())

    def restore_window_state(self):
        # Restore the window size, position, and splitter settings from saved state
        screen = QtWidgets.QApplication.primaryScreen()
        available_geometry = screen.availableGeometry()

        if not available_geometry.contains(self.prev_window_position):
            self.prev_window_position = available_geometry.center() - self.rect().center()

        self.resize(self.prev_window_size)
        self.move(self.prev_window_position)

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

    def run_after_ui_ready(self):
        self.setting_dialog.ui.pushButtonBackgroundColor.setStyleSheet(
            f"background-color: {self.system_variable.CANVAS_COLOR.get_value()};"
        )
        self.system_variable.CANVAS_COLOR_DIALOG_TEMP.set_value(self.system_variable.CANVAS_COLOR.get_value())
        self.main_controller.spi_visualization_controller.parse_spi_file(self.ui.lineEditFilePath.text())


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