# Built-in Imports
from typing import TYPE_CHECKING
from collections import Counter

import numpy as np
# Data Science and Third Party Imports

# Machine Learning Imports

# PyQt Imports
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QSpinBox, QColorDialog

from src.Configs import UiConfigs
from src.Utils.QtUtils import SignalBlocker
from src.Utils.SystemVariable import SystemVariable
# User Imports
from src.Views.QtDesigner.Ui_SettingDialog import Ui_SettingDialog
from src.Models.DataClasses.CanvasConfig import CanvasConfig


# Logger
import logging
logger = logging.getLogger(__name__)


class SettingDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.system_variable: SystemVariable = SystemVariable()

        # Set up UI, reusing UI components from CreateNewProjectDialog
        self.ui = Ui_SettingDialog()
        self.ui.setupUi(self)

        # Demo settings
        self.edge = 500
        self.margin = 10
        self.edge_center = self.edge // 2

        # Draw Demo Image
        self.demo_image = np.full((self.edge, self.edge, 3), 255, dtype=np.uint8)
        self.ui.graphicsView.imshow(self.demo_image)

        # re-render timer
        self._render_timer = QTimer()
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._render_demo)
        self._start_render_timer_func = lambda: self._render_timer.start(50)

    def connect_signals(self):
        # Signal
        self.ui.groupBoxFixedSize.toggled.connect(lambda checked: self.ui.groupBoxAutoCrop.setChecked(not checked))
        self.ui.groupBoxAutoCrop.toggled.connect(lambda checked: self.ui.groupBoxFixedSize.setChecked(not checked))
        self.ui.pushButtonReset.clicked.connect(self.reset)
        self.ui.pushButtonBackgroundColor.clicked.connect(self.on_background_color_clicked)
        self.system_variable.CANVAS_COLOR_DIALOG_TEMP.connect(
            lambda color: self.ui.pushButtonBackgroundColor.setStyleSheet(f"background-color: {color};")
        )

        # Signal - Re-render
        self.ui.groupBoxAutoCrop.toggled.connect(lambda checked: self._start_render_timer_func() if checked else None)
        self.ui.groupBoxFixedSize.toggled.connect(lambda checked: self._start_render_timer_func() if checked else None)
        self.ui.spinBoxMaxSideLength.valueChanged.connect(self._start_render_timer_func)
        self.ui.spinBoxSizeX.valueChanged.connect(self._start_render_timer_func)
        self.ui.spinBoxSizeY.valueChanged.connect(self._start_render_timer_func)
        self.ui.spinBoxMargin.valueChanged.connect(self._start_render_timer_func)
        self.system_variable.CANVAS_COLOR_DIALOG_TEMP.connect(lambda *args: self._start_render_timer_func())

    def exec_with_params(self, canvas_config: "CanvasConfig") -> CanvasConfig | None:
        # canvas config -> set ui

        # Initial UI setup
        self.adjustSize()
        self.setFixedSize(self.size())

        # Set the default values
        self.system_variable.CANVAS_COLOR_DIALOG_TEMP.set_value(self.rgb_to_hex(canvas_config.background_color))
        self._initial_ui(canvas_config)
        self._render_demo()

        # Execute the dialog (Modal)
        if super().exec() == QDialog.DialogCode.Accepted:
            self.system_variable.CANVAS_COLOR.set_value(self.system_variable.CANVAS_COLOR_DIALOG_TEMP.get_value())
            return self.export_canvas_config()
        else:
            logger.warning(f"Setting dialog was canceled")
            return None

    def _initial_ui(self, canvas_config: "CanvasConfig"):
        with SignalBlocker(
    self.ui.spinBoxMaxSideLength, self.ui.spinBoxSizeX, self.ui.spinBoxSizeY,
            self.ui.spinBoxMargin, self.ui.spinBoxComponentRadius,
            self.ui.groupBoxAutoCrop, self.ui.groupBoxFixedSize
        ):
            self.ui.spinBoxMaxSideLength.setValue(max(canvas_config.canvas_size[:2]))
            self.ui.spinBoxSizeX.setValue(canvas_config.canvas_size[1])
            self.ui.spinBoxSizeY.setValue(canvas_config.canvas_size[0])
            self.ui.spinBoxMargin.setValue(canvas_config.margin)
            self.ui.spinBoxComponentRadius.setValue(canvas_config.component_radius)
            self.ui.groupBoxAutoCrop.setChecked(canvas_config.canvas_mode == "auto")
            self.ui.groupBoxFixedSize.setChecked(canvas_config.canvas_mode == "fixed")

    def _render_demo(self):
        self.ui.graphicsView.clear_layers()

        if self.ui.groupBoxAutoCrop.isChecked():
            canvas_h = canvas_w = self.ui.spinBoxMaxSideLength.value()
            outline_type = "rect-dash"
        elif self.ui.groupBoxFixedSize.isChecked():
            canvas_h, canvas_w = self.ui.spinBoxSizeY.value(), self.ui.spinBoxSizeX.value()
            outline_type = "rect"
        else:
            logger.error("Canvas size is not set")
            return

        canvas_margin = self.ui.spinBoxMargin.value()
        logger.warning(f"{self.system_variable.CANVAS_COLOR_DIALOG_TEMP.get_value() = }")
        canvas_background = self.system_variable.CANVAS_COLOR_DIALOG_TEMP.get_value()
        canvas_comp_radius = self.ui.spinBoxComponentRadius.value()

        # Canvas -> demo
        scale = (self.edge - 2 * self.margin) / max(canvas_h, canvas_w)
        canvas_h = int(canvas_h * scale)
        canvas_w = int(canvas_w * scale)
        canvas_margin = int(canvas_margin * scale)
        canvas_x1 = self.edge_center - canvas_w // 2
        canvas_y1 = self.edge_center - canvas_h // 2
        canvas_x2 = self.edge_center + canvas_w // 2
        canvas_y2 = self.edge_center + canvas_h // 2

        self.ui.graphicsView.add_items_to_layer(
            "canvas",
            {outline_type: [
                ((canvas_x1, canvas_y1, canvas_x2, canvas_y2), "outline"),
            ]},
            color="#000000", width=1,
        )
        self.ui.graphicsView.add_items_to_layer(
            "canvas",
            {"rect": [
                ((canvas_x1 + canvas_margin, canvas_y1 + canvas_margin, canvas_x2 - canvas_margin, canvas_y2 - canvas_margin), "fill-bound"),
            ]},
            color="#ff00ff", width=1,
        )
        self.ui.graphicsView.add_items_to_layer(
            "canvas",
            {"rect-fill": [
                ((canvas_x1 + canvas_margin, canvas_y1 + canvas_margin, canvas_x2 - canvas_margin, canvas_y2 - canvas_margin), "fill"),
            ]},
            color=canvas_background,
        )

    def reset(self):
        self.ui.groupBoxAutoCrop.setChecked(UiConfigs.DEFAULT_GROUP_BOX_AUTO_CROP)
        self.ui.groupBoxFixedSize.setChecked(UiConfigs.DEFAULT_GROUP_BOX_FIXED_SIZE)
        self.ui.spinBoxSizeX.setValue(UiConfigs.DEFAULT_SPIN_BOX_SIZE_X)
        self.ui.spinBoxSizeY.setValue(UiConfigs.DEFAULT_SPIN_BOX_SIZE_Y)
        self.ui.spinBoxMaxSideLength.setValue(UiConfigs.DEFAULT_SPIN_BOX_MAX_SIDE_LENGTH)
        self.ui.spinBoxMargin.setValue(UiConfigs.DEFAULT_SPIN_BOX_MARGIN)
        self.ui.spinBoxComponentRadius.setValue(UiConfigs.DEFAULT_SPIN_BOX_COMPONENT_RADIUS)
        self.system_variable.CANVAS_COLOR_DIALOG_TEMP.set_value(UiConfigs.DEFAULT_CANVAS_COLOR)

    def on_background_color_clicked(self):
        # Open color dialog to select background color
        # Open color dialog
        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle("Select Background Color")
        color_dialog.setOptions(QColorDialog.ColorDialogOption.ShowAlphaChannel)
        color_dialog.setCurrentColor(QColor(self.system_variable.CANVAS_COLOR_DIALOG_TEMP.get_value()))
        color_dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)

        # Show the dialog and get the selected color
        if color_dialog.exec() == QDialog.DialogCode.Accepted:
            selected_color = color_dialog.selectedColor()
            self.system_variable.CANVAS_COLOR_DIALOG_TEMP.set_value(selected_color.name())

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """
        將類似 '#ffffff' 或 'ffffff' 的 16 進位顏色字串轉為 (r, g, b) 三元組。
        """
        # 去掉開頭的 '#'（若有的話）
        hex_color = hex_color.lstrip('#')
        # 確保長度是 6
        if len(hex_color) != 6:
            raise ValueError("輸入的顏色字串長度必須為 6（不含'#'）")
        # 分別取前、後兩位轉成整數
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)

    @staticmethod
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def export_canvas_config(self) -> CanvasConfig | None:
        if self.ui.groupBoxAutoCrop.isChecked():
            canvas_h = canvas_w = self.ui.spinBoxMaxSideLength.value()
        elif self.ui.groupBoxFixedSize.isChecked():
            canvas_h, canvas_w = self.ui.spinBoxSizeY.value(), self.ui.spinBoxSizeX.value()
        else:
            logger.error("Canvas size is not set")
            return None

        canvas_config = CanvasConfig(
            canvas_mode="auto" if self.ui.groupBoxAutoCrop.isChecked() else "fixed",
            canvas_size=(canvas_h, canvas_w, 3),
            margin=self.ui.spinBoxMargin.value(),
            background_color=self.hex_to_rgb(self.system_variable.CANVAS_COLOR_DIALOG_TEMP.get_value()),
            component_radius=self.ui.spinBoxComponentRadius.value(),
        )
        return canvas_config



