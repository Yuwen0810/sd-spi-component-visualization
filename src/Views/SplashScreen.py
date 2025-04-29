# Logger
import logging
logger = logging.getLogger(__name__)

# Built-in Imports

# Data Science and Third Party Imports

# Machine Learning Imports

# PyQt Imports
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt6.QtWidgets import QSplashScreen

# User Imports

# This file defines a custom splash screen class for the application.
# The splash screen is displayed during the application startup process.

# Import necessary PyQt modules for GUI rendering and painting

class SplashScreen:
    def __init__(self, title="Application Launching", message="Please wait while the system starts...", min_width=300, min_height=80):
        # Initialize fonts for the title and message
        title_font = QtGui.QFont("Arial", 11, QtGui.QFont.Weight.Bold)
        message_font = QtGui.QFont("Arial", 10)

        # Calculate bounding rectangles for text to determine splash screen dimensions
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

        # Create a pixmap for the splash screen and draw the border and text
        splash_pix = QPixmap(splash_width, splash_height)
        splash_pix.fill(Qt.GlobalColor.white)

        # 設定 DPI 比例，避免在 Retina/高解析螢幕模糊
        # splash_pix.setDevicePixelRatio(QtGui.QGuiApplication.primaryScreen().devicePixelRatio())

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

        # Initialize the QSplashScreen with the created pixmap
        self.splash = QSplashScreen(splash_pix)

    def show(self):
        """Show the splash screen."""
        self.splash.show()

    def finish(self, window):
        """Close the splash screen and transfer control to the main window."""
        self.splash.finish(window)
