# Built-in Imports
import hashlib
import math
from typing import Union, Literal, Dict, List, Tuple, Optional, Any

# Data Science and Third Party Imports
import numpy as np

# Machine Learning Imports

# PyQt Imports
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRectF
from PyQt6.QtWidgets import (
    QGraphicsView, QMenu, QApplication, QGraphicsPixmapItem, QGraphicsScene, QGraphicsItemGroup,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsTextItem, QWidget, QHBoxLayout, QPushButton,
    QGraphicsPathItem
)
from PyQt6.QtGui import QImage, QPixmap, QWheelEvent, QPainter, QPen, QMouseEvent, QColor, QBrush, QIcon, QPainterPath, QFont


class CustomGraphicsItemMixin:
    def init_custom(self, base_color, obj_id):
        self.obj_id = obj_id
        self.highlight = False
        self.base_color = base_color

    def set_highlight(self, highlight: bool):
        self.highlight = highlight
        color = QColor("white") if highlight else self.base_color

        if isinstance(self, (QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPathItem, QGraphicsLineItem)):
            self.setPen(QPen(color, self.pen().width()))
            if hasattr(self, "setBrush"):
                self.setBrush(QBrush(color))
        elif isinstance(self, QGraphicsTextItem):
            self.setDefaultTextColor(color)

class CustomRectItem(QGraphicsRectItem, CustomGraphicsItemMixin):
    def __init__(self, x, y, w, h, base_color, obj_id):
        super().__init__(x, y, w, h)
        self.init_custom(base_color, obj_id)

class CustomEllipseItem(QGraphicsEllipseItem, CustomGraphicsItemMixin):
    def __init__(self, x, y, w, h, base_color, obj_id):
        super().__init__(x, y, w, h)
        self.init_custom(base_color, obj_id)

class CustomLineItem(QGraphicsLineItem, CustomGraphicsItemMixin):
    def __init__(self, x1, y1, x2, y2, base_color, obj_id):
        super().__init__(x1, y1, x2, y2)
        self.init_custom(base_color, obj_id)

class CustomPathItem(QGraphicsPathItem, CustomGraphicsItemMixin):
    def __init__(self, path: QPainterPath, base_color, obj_id):
        super().__init__(path)
        self.init_custom(base_color, obj_id)

class CustomTextItem(QGraphicsTextItem, CustomGraphicsItemMixin):
    def __init__(self, text, base_color, obj_id):
        super().__init__(text)
        self.init_custom(base_color, obj_id)
