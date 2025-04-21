# Built-in Imports
import hashlib
import math
from collections import defaultdict
from typing import Union, Literal, Dict, List, Tuple, Optional, Any, Iterable

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

from src.Views.CustomWidgets.CustomGraphicsViewItems import CustomRectItem, CustomPathItem, CustomLineItem, \
    CustomEllipseItem, CustomTextItem

# Type Hints
DRAWING_TYPE_HINT = Literal["rect", "rect-fill", "line", "circle", "text", "rect-fill-hole", "triangle", "vline", "hline"]


class CustomGraphicsView(QGraphicsView):
    ZOOM_UNIT = 0.005

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)

        # Image related attributes
        self.image: Optional[np.ndarray] = None
        self.pixmap = None
        self._scale_value: float = 1.0
        self.h: int = 0
        self.w: int = 0

        self.setScene(QGraphicsScene())
        self.image_item = QGraphicsPixmapItem()
        self.scene().addItem(self.image_item)

        # Initialize annotation layers
        self._layer_groups: Dict[str, QGraphicsItemGroup] = {}
        self._layer_sets = defaultdict(set)
        self._init_annotation_layers()

        # Initialize drawing variables
        self.left_drawing = False
        self.right_drawing = False
        self.start_point = (0, 0)
        self.end_point = (0, 0)

        # Initialize floating controls
        self._init_floating_controls()

    def _init_annotation_layers(self) -> None:
        """Initialize annotation layer groups."""
        self._register_annotation_layer("c", z_priority=0)

    def _register_annotation_layer(
        self,
        layer_name: str,
        z_priority: int
    ) -> None:
        """Register an annotation layer and set its Z-order."""
        layer_group = QGraphicsItemGroup()
        layer_group.setZValue(z_priority)
        self.scene().addItem(layer_group)
        self._layer_groups[layer_name] = layer_group

    def _clear_layer_items(self, layer_name: str) -> None:
        """Clear all annotation items in the specified layer."""
        layer_group = self._layer_groups.get(layer_name)
        if layer_group is None:
            raise ValueError(f"Invalid layer: {layer_name}")
        for item in layer_group.childItems():
            layer_group.removeFromGroup(item)
            self.scene().removeItem(item)

    @property
    def layer_names(self) -> list[str]:
        """回傳目前所有 layer 的名稱（key）"""
        return list(self._layer_groups.keys())

    @property
    def layer_count(self) -> int:
        """回傳目前 layer 的數量"""
        return len(self._layer_groups)

    def clear_layers(self):
        """清除所有圖層與其物件，保留影像"""
        for group in self._layer_groups.values():
            for item in group.childItems():
                group.removeFromGroup(item)
                self.scene().removeItem(item)
            self.scene().removeItem(group)
        self._layer_groups.clear()

    def clear_all(self):
        """清除所有圖層與影像"""
        self.scene().clear()
        self._layer_groups.clear()
        self.image_item = QGraphicsPixmapItem()
        self.scene().addItem(self.image_item)

    def register_layer_set(self, key: str, layer_name: str) -> None:
        """Register a layer set with the given key."""
        self._layer_sets[key].add(layer_name)

    def iter_layer_set(self, key: str) -> Iterable[str]:
        """Iterate over the layer set with the given key."""
        return iter(self._layer_sets.get(key, []))

    def add_items_to_layer(
        self,
        layer_name: str,
        shapes: Dict[DRAWING_TYPE_HINT, list[Tuple[Any, str]]],  # 每筆 shape 對應一個 obj_id
        color: Union[str, QColor],
        opacity: float = 1.0,
        width: float = 2,
        font_size: int = 12,
        h_align: str = "left",
        v_align: str = "top",
    ) -> None:
        if not shapes:
            return

        # Preprocess color if needed; use layer base color if color is not provided.
        if isinstance(color, str) and color.startswith("#"):
            color = QColor(color)

        # 自動註冊 layer
        layer_group = self._layer_groups.get(layer_name)
        if layer_group is None:
            z_priority = len(self._layer_groups)
            self._register_annotation_layer(layer_name, z_priority=z_priority)
            layer_group = self._layer_groups[layer_name]

        # 先收集所有 obj_id，從畫面上移除同名物件
        incoming_obj_ids = set()
        for shape_list in shapes.values():
            for _, obj_id in shape_list:
                incoming_obj_ids.add(obj_id)

        for item in list(layer_group.childItems()):
            if getattr(item, "obj_id", None) in incoming_obj_ids:
                layer_group.removeFromGroup(item)
                self.scene().removeItem(item)

        # 畫圖形
        for (x1, y1, x2, y2), obj_id in shapes.get("rect", []):
            x, y = min(x1, x2), min(y1, y2)
            w, h = abs(x2 - x1), abs(y2 - y1)
            item = CustomRectItem(x, y, w, h, base_color=color, obj_id=obj_id)
            item.setPen(QPen(color, width))
            item.setOpacity(opacity)
            layer_group.addToGroup(item)

        # rect-fill
        for (x1, y1, x2, y2), obj_id in shapes.get("rect-fill", []):
            x, y = min(x1, x2), min(y1, y2)
            w, h = abs(x2 - x1), abs(y2 - y1)
            item = CustomRectItem(x, y, w, h, base_color=color, obj_id=obj_id)
            item.setBrush(QBrush(color, Qt.BrushStyle.SolidPattern))
            item.setOpacity(opacity)
            layer_group.addToGroup(item)

        for (x1, y1, x2, y2, holes), obj_id in shapes.get("rect-fill-hole", []):
            path = QPainterPath()
            path.addRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
            for hx1, hy1, hx2, hy2 in holes:
                hole = QPainterPath()
                hole.addRect(min(hx1, hx2), min(hy1, hy2), abs(hx2 - hx1), abs(hy2 - hy1))
                path = path.subtracted(hole)
            item = CustomPathItem(path, base_color=color, obj_id=obj_id)
            item.setBrush(QBrush(color, Qt.BrushStyle.SolidPattern))
            item.setOpacity(opacity)
            layer_group.addToGroup(item)

        for (x1, y1, x2, y2, x3, y3), obj_id in shapes.get("triangle", []):
            path = QPainterPath()
            path.moveTo(x1, y1)
            path.lineTo(x2, y2)
            path.lineTo(x3, y3)
            path.closeSubpath()
            item = CustomPathItem(path, base_color=color, obj_id=obj_id)
            item.setPen(QPen(color, width))
            item.setBrush(QBrush(color, Qt.BrushStyle.SolidPattern))
            item.setOpacity(opacity)
            layer_group.addToGroup(item)

        for (x1, y1, x2, y2), obj_id in shapes.get("line", []):
            item = CustomLineItem(x1, y1, x2, y2, base_color=color, obj_id=obj_id)
            item.setPen(QPen(color, width))
            item.setOpacity(opacity)
            layer_group.addToGroup(item)

        for x, obj_id in shapes.get("vline", []):
            item = CustomLineItem(x, 0, x, self.h, base_color=color, obj_id=obj_id)
            item.setPen(QPen(color, width))
            item.setOpacity(opacity)
            layer_group.addToGroup(item)

        for y, obj_id in shapes.get("hline", []):
            item = CustomLineItem(0, y, self.w, y, base_color=color, obj_id=obj_id)
            item.setPen(QPen(color, width))
            item.setOpacity(opacity)
            layer_group.addToGroup(item)

        for (cx, cy, r), obj_id in shapes.get("circle", []):
            item = CustomEllipseItem(cx - r, cy - r, 2 * r, 2 * r, base_color=color, obj_id=obj_id)
            item.setPen(QPen(color, width))
            item.setBrush(color)
            item.setOpacity(opacity)
            layer_group.addToGroup(item)

        for (x, y, txt), obj_id in shapes.get("text", []):
            item = CustomTextItem(txt, base_color=color, obj_id=obj_id)
            font = QFont()
            font.setPointSize(font_size)
            item.setFont(font)
            item.setDefaultTextColor(color)
            item.setOpacity(opacity)
            br = item.boundingRect()
            item.setX(x - (br.width() / 2 if h_align == "center" else br.width() if h_align == "right" else 0))
            item.setY(y - (br.height() / 2 if v_align == "middle" else br.height() if v_align == "bottom" else 0))
            layer_group.addToGroup(item)

    def set_layer_highlight(self, layer_name: str, highlight: bool):
        """Set the highlight state of the specified layer."""
        layer_group = self._layer_groups.get(layer_name)
        if layer_group is None:
            raise ValueError(f"Invalid layer: {layer_name}")
        for item in layer_group.childItems():
            item.set_highlight(highlight)

    def set_layer_visibility(self, layer_name: str, visible: bool):
        """Set the visibility of the specified layer."""
        layer_group = self._layer_groups.get(layer_name)
        if layer_group is None:
            raise ValueError(f"Invalid layer: {layer_name}")
        layer_group.setVisible(visible)

    def set_object_visibility(self, obj_id: str, visible: bool):
        """根據 obj_id 設定個別圖層物件的可見性"""
        for layer_group in self._layer_groups.values():
            for item in layer_group.childItems():
                if getattr(item, "obj_id", None) == obj_id:
                    item.setVisible(visible)

    @property
    def scale_value(self):
        """Get the current scale value."""
        return self._scale_value

    @scale_value.setter
    def scale_value(self, value):
        """Set the scale value and update the view."""
        if value != self._scale_value and value >= 0.005:
            self._scale_value = value
            self.resetTransform()
            self.scale(self._scale_value, self._scale_value)
            self.update()

    def showEvent(self, event):
        """Handle show event: fit image to view and adjust floating controls."""
        super().showEvent(event)
        self.fit_to_view()
        self.adjust_floating_widget()

    def resizeEvent(self, event):
        """Handle resize event: adjust floating controls and refit image if in fit mode."""
        super().resizeEvent(event)
        self.adjust_floating_widget()
        if self.pushButtonFitSize.isChecked():
            self.fit_to_view()

    def _init_floating_controls(self):
        """Initialize floating control widgets."""
        self.floating_widget = QWidget(self)
        self.floating_widget.setObjectName("floating_widget")
        self.floating_widget.setStyleSheet("""
            #floating_widget {background-color: transparent; border: none;} 
            .QPushButton {border: 1px solid rgb(220, 220, 220); background-color: rgba(240, 240, 240, 1); padding: 4px;} 
            .QPushButton::hover {background-color: rgba(231, 233, 255, 1);} 
            .QPushButton::checked {background-color: rgba(220, 230, 242, 1);}
        """)
        layout = QHBoxLayout(self.floating_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.pushButtonFitSize = QPushButton()
        self.pushButtonFitSize.setCheckable(True)
        self.pushButtonFitSize.setChecked(True)
        self.pushButtonFitSize.setIcon(QIcon(":/icons/feather-white/maximize.svg"))
        self.pushButtonZoomIn = QPushButton()
        self.pushButtonZoomIn.setIcon(QIcon(":/icons/feather-white/zoom-in.svg"))
        self.pushButtonZoomOut = QPushButton()
        self.pushButtonZoomOut.setIcon(QIcon(":/icons/feather-white/zoom-out.svg"))

        for btn in [self.pushButtonFitSize, self.pushButtonZoomIn, self.pushButtonZoomOut]:
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setFixedSize(30, 30)
            layout.addWidget(btn)

        self.pushButtonFitSize.clicked.connect(self.fit_to_view)
        self.pushButtonZoomIn.clicked.connect(self.zoom_in)
        self.pushButtonZoomOut.clicked.connect(self.zoom_out)
        self.adjust_floating_widget()

    def adjust_floating_widget(self):
        """Adjust the position of the floating widget."""
        if hasattr(self, 'floating_widget'):
            self.floating_widget.move(10, 10)

    def fit_to_view(self):
        """Fit the image to the view."""
        if self.image is not None:
            view_rect = self.viewport().rect()
            img_rect = self.pixmap.rect()
            width_ratio = view_rect.width() / img_rect.width()
            height_ratio = view_rect.height() / img_rect.height()
            scale_value = min(width_ratio, height_ratio)
            self.scale_value = int(scale_value // self.ZOOM_UNIT) * self.ZOOM_UNIT

    def imshow(
        self, image: Optional[np.ndarray],
        normal_rois: Optional[np.ndarray] = None,
        tumor_rois: Optional[np.ndarray] = None,
    ):
        """Display the image and update ROI annotations."""
        if image is None:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            # If the image is None, clear the image
            self.image = None
            self.pixmap = None
            self.h, self.w = 0, 0
            self.image_item.setPixmap(QPixmap())  # Clear the image
            self.setSceneRect(0, 0, 0, 0)

        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            # Update the image and pixmap
            self.image = image.copy()
            self.pixmap = self.__numpy_to_pixmap(image)
            self.h, self.w = image.shape[:2]
            self.image_item.setPixmap(self.pixmap)

            # Reset the scene rect to match the new image size
            self.setSceneRect(0, 0, self.w, self.h)

            # Fit the image to the view
            if self.pushButtonFitSize.isChecked():
                self.fit_to_view()

    @staticmethod
    def __numpy_to_pixmap(np_image: np.ndarray) -> QPixmap:
        """Convert a numpy array to a QPixmap."""
        np_image = np_image.astype(np.uint8)
        if np_image.ndim == 2:
            qformat = QImage.Format.Format_Indexed8
        elif np_image.shape[2] == 3:
            qformat = QImage.Format.Format_BGR888
        elif np_image.shape[2] == 4:
            qformat = QImage.Format.Format_RGBA8888
        else:
            raise ValueError(f"Unsupported shape: {np_image.shape}")
        img = QImage(np_image.data, np_image.shape[1], np_image.shape[0], np_image.strides[0], qformat)
        return QPixmap.fromImage(img)

    def __copy_image(self):
        """Copy the current image to the clipboard."""
        if self.image is not None:
            QApplication.clipboard().setPixmap(self.image_item.pixmap())

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel event for zooming."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            event.accept()
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def zoom_in(self):
        """Zoom in the view."""
        self.pushButtonFitSize.setChecked(False)
        unit = self.ZOOM_UNIT
        cur = self.scale_value
        if abs(cur / unit - round(cur / unit)) < 1e-6:
            new = cur + unit
        else:
            new = math.ceil(cur / unit) * unit
        self.scale_value = new

    def zoom_out(self):
        """Zoom out the view."""
        self.pushButtonFitSize.setChecked(False)
        unit = self.ZOOM_UNIT
        cur = self.scale_value
        if abs(cur / unit - round(cur / unit)) < 1e-6:
            new = cur - unit
        else:
            new = math.floor(cur / unit) * unit
        self.scale_value = new

    def reset_size(self):
        """Reset the view to default scale."""
        self.scale_value = 1.0

    def __get_image_pos(self, event: QMouseEvent) -> Tuple[int, int]:
        """Get the image position from the mouse event."""
        view_pos = event.pos()
        scene_pos = self.mapToScene(view_pos)
        x, y = int(scene_pos.x()), int(scene_pos.y())
        if self.w > 0 and self.h > 0:
            x = min(max(x, 0), self.w - 1)
            y = min(max(y, 0), self.h - 1)
        return x, y

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move event."""
        x, y = self.__get_image_pos(event)
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        """Handle paint event to draw scale information."""
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = f"Scale: {self.scale_value:.2f}x"
        rect = painter.boundingRect(self.viewport().rect(), Qt.AlignmentFlag.AlignRight, text)
        rect.moveBottomRight(self.viewport().rect().bottomRight() - QPoint(10, 10))
        painter.fillRect(rect.adjusted(-2, -2, 2, 2), Qt.GlobalColor.white)
        painter.drawText(rect, Qt.AlignmentFlag.AlignRight, text)