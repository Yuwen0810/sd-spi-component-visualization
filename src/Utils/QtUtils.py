# Built-in Imports
import os
import sys
from typing import Callable, Any

# Data Science and Third Party Imports

# Machine Learning Imports

# PyQt Imports
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFont
from PyQt6.QtWidgets import QApplication, QMessageBox

# User Imports


def create_letter_icon(letter, font_family, color, border: bool = True, save_path: str = "", size: tuple = None):
    # Create a blank pixmap
    if size:
        pixmap = QPixmap(*size)
    else:
        pixmap = QPixmap(256, 256)

    # Fill the background color (e.g., white for JPG)
    pixmap.fill(Qt.GlobalColor.white)

    # Create a painter and set the font
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Set font properties
    font = QFont(font_family, 128)
    painter.setFont(font)

    # Set the color for the text
    painter.setPen(color)

    # Draw the text, center-aligned
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)

    # Draw the square border if needed
    if border:
        painter.setPen(Qt.GlobalColor.black)  # Set the border color
        painter.drawRect(0, 0, pixmap.width() - 1, pixmap.height() - 1)  # Draw the border

    # End painting
    painter.end()

    # Save the image if a path is provided
    if save_path:
        os.makedirs(save_path, exist_ok=True)
        pixmap.save(f"{save_path}/{letter}.jpg")

    return QIcon(pixmap)

def show_info_message(message: str, title: str = "Information"):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Information)  # 設定圖示（可用：Information, Warning, Critical, Question）
    msg_box.setText(message)
    msg_box.setWindowTitle(title)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()


class SignalBlocker:
    def __init__(self, *widgets):
        self.widgets = widgets

    def __enter__(self):
        for widget in self.widgets:
            widget.blockSignals(True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for widget in self.widgets:
            widget.blockSignals(False)


class UpdateTimerManager:
    def __init__(self, interval: int = 300):
        self.interval = interval
        self.timers = {}

    def start_timer(self, timer_key: Any, callbacks: Callable | list[Callable], update_key: str, update_val: Any):
        if not isinstance(callbacks, list):
            callbacks = [callbacks]

        if timer_key in self.timers:
            self.timers[timer_key]["timer"].start(self.interval)
            self.timers[timer_key]["updates"][update_key] = update_val
        else:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.execute_callbacks(timer_key))
            self.timers[timer_key] = {
                "timer": timer,
                "callbacks": callbacks,
                "updates": {update_key: update_val},
            }
            timer.start(self.interval)

    def execute_callbacks(self, timer_key: Any):
        if timer_key in self.timers:
            updates = self.timers[timer_key]["updates"]
            for callback in self.timers[timer_key]["callbacks"]:
                callback(updates)
            del self.timers[timer_key]

class CallTimerManager:
    def __init__(self, interval: int = 300):
        self.interval = interval
        self.timers = {}

    def start_timer(self, timer_key: Any, callbacks: Callable | list[Callable]):
        if not isinstance(callbacks, list):
            callbacks = [callbacks]

        if timer_key in self.timers:
            self.timers[timer_key]["timer"].start(self.interval)
        else:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self.execute_callbacks(timer_key))
            self.timers[timer_key] = {
                "timer": timer,
                "callbacks": callbacks,
            }
            timer.start(self.interval)

    def execute_callbacks(self, timer_key: Any):
        if timer_key in self.timers:
            for callback in self.timers[timer_key]["callbacks"]:
                callback()
            del self.timers[timer_key]
