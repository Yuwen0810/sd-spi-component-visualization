# Built-in Imports
import os
from dataclasses import dataclass
from glob import glob
from typing import TYPE_CHECKING
import numpy as np
from PyQt6.QtWidgets import QPushButton

from src.Models.Components.SpiComponentManager import SpiComponentManager
from src.Models.DataClasses.CanvasConfig import CanvasConfig
from src.Models.Threads.ParseSpiFileThread import ParseSpiFileThread
from src.Models.Threads.UpdateComponentThread import UpdateComponentThread
from src.Configs import COMPONENT_COLORS

# Data Science and Third Party Imports

# Machine Learning Imports

# PyQt Imports

# User Imports

# Type Checking
if TYPE_CHECKING:
    from src.Views.SubViews.SpiVisualizationSubView import SpiVisualizationSubView
    from src.Controllers.MainController import MainController



class SpiVisualizationController:
    
    def __init__(self, mediator: "MainController", ui: "SpiVisualizationSubView"):
        self.mediator = mediator
        self._ui: SpiVisualizationSubView = ui

        self.canvas_config = CanvasConfig()
        self.background_image = np.full(
            self.canvas_config.canvas_size, self.canvas_config.background_color, dtype=np.uint8
        )

        # Spi Component Manager
        self._spi_component_manager = SpiComponentManager()

        # Update component thread
        self._update_component_thread = UpdateComponentThread()
        self._update_component_thread.update_progress_desc_signal.connect(self._ui.statusBar.showMessage)
        self._update_component_thread.finished.connect(lambda: self._ui.statusBar.showMessage("Done !"))
        self._update_component_thread.finished.connect(self._on_parse_spi_file_finished)

        # Parse SPI file thread
        self._parse_spi_file_thread = ParseSpiFileThread()
        self._parse_spi_file_thread.update_progress_desc_signal.connect(self._ui.statusBar.showMessage)
        self._parse_spi_file_thread.finished.connect(lambda: self._ui.statusBar.showMessage("Done !"))
        self._parse_spi_file_thread.finished.connect(
            lambda: self._update_component_thread.add_task(self._spi_component_manager, self.canvas_config)
        )

        # Signal
        self._ui.lineEditFilePath.textChanged.connect(
            lambda text: self._parse_spi_file_thread.add_task(text, self._spi_component_manager, self.canvas_config)
        )
        self._ui.treeWidgetSelectType.toggle_changed_signal.connect(self._on_type_tree_widget_toggle_changed)
        self._ui.treeWidgetSelectType.select_changed_signal.connect(self._on_type_tree_widget_select_changed)
        self._ui.treeWidgetSelectId.toggle_changed_signal.connect(self._on_id_tree_widget_toggle_changed)
        self._ui.treeWidgetSelectId.select_changed_signal.connect(self._on_id_tree_widget_select_changed)
        self._ui.selectionModeButtonGroup.buttonToggled.connect(self.on_selection_mode_changed)

    def _on_parse_spi_file_finished(self):
        # Render Tree UI (Component Type)
        component_type_structure = self._spi_component_manager.get_component_type_structure()
        self._ui.treeWidgetSelectType.clear()
        self._ui.treeWidgetSelectType.populate(component_type_structure)

        # Render Tree UI (Component Id)
        component_id_structure = self._spi_component_manager.get_component_id_structure()
        self._ui.treeWidgetSelectId.clear()
        self._ui.treeWidgetSelectId.populate(component_id_structure)

        # Render All Components
        self._render_all_components()

    def _render_all_components(self):
        self._ui.graphicsView.clear_all()
        self._ui.graphicsView.imshow(self.background_image)
        type_visibility = self._ui.pushButtonSelectType.isChecked()
        id_visibility = self._ui.pushButtonSelectId.isChecked()

        for component_type, size, components in self._spi_component_manager.iter_components_by_type():
            layer_name = f"{component_type}_{size}"
            layer_color = COMPONENT_COLORS.get(component_type, "#000000")
            self._ui.graphicsView.add_items_to_layer(
                layer_name,
                {"circle": [
                    ((component.canvas_pos_x, component.canvas_pos_y, self.canvas_config.component_radius), component.pad_id)
                    for component in components
                ]},
                layer_color,
            )
            self._ui.graphicsView.register_layer_set("type", layer_name)
            self._ui.graphicsView.set_layer_visibility(layer_name, type_visibility)

        for component_type, component_id, components in self._spi_component_manager.iter_components_by_id():
            layer_name = f"{component_type}_{component_id}"
            layer_color = COMPONENT_COLORS.get(component_type, "#000000")
            self._ui.graphicsView.add_items_to_layer(
                layer_name,
                {"circle": [
                    ((component.canvas_pos_x, component.canvas_pos_y, self.canvas_config.component_radius), component.pad_id)
                    for component in components
                ]},
                layer_color,
            )
            self._ui.graphicsView.register_layer_set("id", layer_name)
            self._ui.graphicsView.set_layer_visibility(layer_name, id_visibility)

    def _on_type_tree_widget_toggle_changed(self, turned_on: list[str], turned_off: list[str]):
        for layer_name in turned_on:
            self._ui.graphicsView.set_layer_visibility(layer_name, True)
        for layer_name in turned_off:
            self._ui.graphicsView.set_layer_visibility(layer_name, False)

    def _on_type_tree_widget_select_changed(self, added: list[str], removed: list[str]):
        for layer_name in added:
            self._ui.graphicsView.set_layer_highlight(layer_name, True)
        for layer_name in removed:
            self._ui.graphicsView.set_layer_highlight(layer_name, False)

    def _on_id_tree_widget_toggle_changed(self, turned_on: list[str], turned_off: list[str]):
        for layer_name in turned_on:
            self._ui.graphicsView.set_layer_visibility(layer_name, True)
        for layer_name in turned_off:
            self._ui.graphicsView.set_layer_visibility(layer_name, False)

    def _on_id_tree_widget_select_changed(self, added: list[str], removed: list[str]):
        for layer_name in added:
            self._ui.graphicsView.set_layer_highlight(layer_name, True)
        for layer_name in removed:
            self._ui.graphicsView.set_layer_highlight(layer_name, False)

    def _re_render_graphics_view_by_type(self):
        for layer_name, status in self._ui.treeWidgetSelectType.get_all_item_check_status():
            self._ui.graphicsView.set_layer_visibility(layer_name, status)

    def _re_render_graphics_view_by_id(self):
        for layer_name, status in self._ui.treeWidgetSelectId.get_all_item_check_status():
            self._ui.graphicsView.set_layer_visibility(layer_name, status)

    def _close_layer_set(self, layer_set_name: str):
        for layer_name in self._ui.graphicsView.iter_layer_set(layer_set_name):
            self._ui.graphicsView.set_layer_visibility(layer_name, False)
            self._ui.graphicsView.set_layer_highlight(layer_name, False)

    def on_selection_mode_changed(self, button: QPushButton, checked: bool):
        """
        Slot to handle the selection mode change.
        :param button: The button that was toggled.
        :param checked: Whether the button is checked or not.
        """
        if not checked:
             return

        if button == self._ui.pushButtonSelectId:
            self._ui.stackedWidgetSelectionMode.setCurrentWidget(self._ui.pageSelectId)
            self._close_layer_set("type")
            self._re_render_graphics_view_by_id()
        elif button == self._ui.pushButtonSelectType:
            self._ui.stackedWidgetSelectionMode.setCurrentWidget(self._ui.pageSelectType)
            self._close_layer_set("id")
            self._re_render_graphics_view_by_type()
        else:
            raise ValueError("Invalid button clicked.")

if __name__ == '__main__':
    ...