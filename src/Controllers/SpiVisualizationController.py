# Built-in Imports
import os.path
from typing import TYPE_CHECKING
import numpy as np
from PyQt6.QtWidgets import QPushButton

from src.Models.Components.SpiComponentManager import SpiComponentManager
from src.Models.DataClasses.CanvasConfig import CanvasConfig
from src.Models.Threads.ParseSpiFileThread import ParseSpiFileThread
from src.Models.Threads.UpdateComponentThread import UpdateComponentThread
from src.Configs import COMPONENT_COLORS
from src.Utils.SystemVariable import SystemVariable
from src.Views.SettingDialog import SettingDialog

# Data Science and Third Party Imports

# Machine Learning Imports

# PyQt Imports

# User Imports

# Logger
import logging
logger = logging.getLogger(__name__)

# Type Checking
if TYPE_CHECKING:
    from src.Views.SubViews.SpiVisualizationSubView import SpiVisualizationSubView
    from src.Controllers.MainController import MainController


class SpiVisualizationController:
    
    def __init__(self, mediator: "MainController", ui: "SpiVisualizationSubView", setting_dialog: SettingDialog):
        self.mediator = mediator
        self._ui: SpiVisualizationSubView = ui
        self._setting_dialog: SettingDialog = setting_dialog
        self._system_variable: SystemVariable = SystemVariable()

        # self.canvas_config = None
        self.canvas_config = CanvasConfig()

        # Spi Component Manager
        self._spi_component_manager = SpiComponentManager()

        # thread
        self._parse_spi_file_thread = ParseSpiFileThread()
        self._update_component_thread = UpdateComponentThread()

    def connect_signals(self):
        # Parse SPI file thread
        self._parse_spi_file_thread.update_progress_desc_signal.connect(self._ui.statusBar.showMessage)
        self._parse_spi_file_thread.next_step_signal.connect(
            lambda: self._update_component_thread.add_task(self._spi_component_manager, self.canvas_config)
        )
        self._parse_spi_file_thread.started.connect(lambda: self._ui.frameWorkspace.setEnabled(False))
        self._parse_spi_file_thread.finished.connect(lambda: self._ui.statusBar.showMessage("Done !"))

        # Update Component thread
        self._update_component_thread.update_progress_desc_signal.connect(self._ui.statusBar.showMessage)
        self._update_component_thread.started.connect(lambda: self._ui.frameWorkspace.setEnabled(False))
        self._update_component_thread.finished.connect(lambda: self._ui.statusBar.showMessage("Done !"))
        self._update_component_thread.finished.connect(self._on_parse_spi_file_finished)
        self._update_component_thread.finished.connect(lambda: self._ui.frameWorkspace.setEnabled(True))

        # Signal
        self._ui.lineEditFilePath.textChanged.connect(self.parse_spi_file)
        self._ui.treeWidgetSelectSize.toggle_changed_signal.connect(self._on_size_tree_widget_toggle_changed)
        self._ui.treeWidgetSelectSize.select_changed_signal.connect(self._on_size_tree_widget_select_changed)
        self._ui.treeWidgetSelectId.toggle_changed_signal.connect(self._on_id_tree_widget_toggle_changed)
        self._ui.treeWidgetSelectId.select_changed_signal.connect(self._on_id_tree_widget_select_changed)
        self._ui.selectionModeButtonGroup.buttonToggled.connect(self.on_selection_mode_changed)
        self._ui.actionSetCanvas.triggered.connect(self.on_set_canvas_clicked)

        self._ui.comboBoxLineId.currentTextChanged.connect(self._on_combobox_changed)
        self._ui.comboboxPanelId.currentTextChanged.connect(self._on_combobox_changed)

    def _on_parse_spi_file_finished(self):
        # Render Tree UI (Component Size)
        component_size_structure = self._spi_component_manager.get_component_size_structure()
        self._ui.treeWidgetSelectSize.clear()
        self._ui.treeWidgetSelectSize.populate(component_size_structure)

        # Render Tree UI (Component Id)
        component_id_structure = self._spi_component_manager.get_component_id_structure()
        self._ui.treeWidgetSelectId.clear()
        self._ui.treeWidgetSelectId.populate(component_id_structure)

        # Render All Components
        self._render_all_components()

    def _render_all_components(self):
        logger.info("Rendering all components...")
        self._ui.graphicsView.clear_all()
        self._ui.graphicsView.imshow(np.full(
            self.canvas_config.canvas_size, self.canvas_config.background_color[::-1], dtype=np.uint8
        ))

        # Render project related params
        self._ui.labelIdno.setText(f"{self._spi_component_manager.get_idno()}")
        self._ui.labelProduct.setText(f"{self._spi_component_manager.get_product_name()}")
        self._ui.comboBoxLineId.clear()
        self._ui.comboboxPanelId.clear()
        self._ui.comboBoxLineId.addItems(self._spi_component_manager.get_line_id_list() + ["All"])
        self._ui.comboboxPanelId.addItems(self._spi_component_manager.get_panel_id_list() + ["All"])

        # Render All Components by Type and Id
        type_visibility = self._ui.pushButtonSelectSize.isChecked()
        id_visibility = self._ui.pushButtonSelectId.isChecked()
        cur_line_id = self._ui.comboBoxLineId.currentText()
        cur_panel_id = self._ui.comboboxPanelId.currentText()

        # Render All Components by Type
        layer_info = {}
        for component_type, size, components in self._spi_component_manager.iter_components_by_size():
            for component in components:
                layer_name = f"{component_type}_{size}_{component.lineid}_{component.panel_id}"
                if layer_name not in layer_info:
                    layer_info[layer_name] = {
                        "layer_info": {
                            "layer_name": layer_name,
                            "component_type": component_type,
                            "component_id": None,
                            "component_size": size,
                            "line_id": component.lineid,
                            "panel_id": component.panel_id,
                        },
                        "shapes": {"circle": []},
                        "color": COMPONENT_COLORS.get(component_type, "#000000"),
                        "visible": (
                            type_visibility
                            and (cur_line_id == component.lineid or cur_line_id == "All")
                            and (cur_panel_id == component.panel_id or cur_panel_id == "All")
                        ),
                    }

                layer_info[layer_name]["shapes"]["circle"].append(
                    ((component.canvas_pos_x, component.canvas_pos_y, self.canvas_config.component_radius), component.pad_id)
                )

        for layer_name, kwargs in layer_info.items():
            visibility = kwargs.pop("visible", True)
            self._ui.graphicsView.add_items_to_layer(layer_name, **kwargs)
            self._ui.graphicsView.set_layer_visibility(layer_name, visibility)

        # Render All Components by Id
        layer_info = {}
        for component_type, component_id, components in self._spi_component_manager.iter_components_by_id():
            for component in components:
                layer_name = f"{component_type}_{component_id}_{component.lineid}_{component.panel_id}"
                if layer_name not in layer_info:
                    layer_info[layer_name] = {
                        "layer_info": {
                            "layer_name": layer_name,
                            "component_type": component_type,
                            "component_id": component_id,
                            "component_size": None,
                            "line_id": component.lineid,
                            "panel_id": component.panel_id,
                        },
                        "shapes": {"circle": []},
                        "color": COMPONENT_COLORS.get(component_type, "#000000"),
                        "visible": (
                            id_visibility
                            and (cur_line_id == component.lineid or cur_line_id == "All")
                            and (cur_panel_id == component.panel_id or cur_panel_id == "All")
                        ),
                    }

                layer_info[layer_name]["shapes"]["circle"].append(
                    ((component.canvas_pos_x, component.canvas_pos_y, self.canvas_config.component_radius), component.pad_id)
                )

        for layer_name, kwargs in layer_info.items():
            visibility = kwargs.pop("visible", True)
            self._ui.graphicsView.add_items_to_layer(layer_name, **kwargs)
            self._ui.graphicsView.set_layer_visibility(layer_name, visibility)

        self._ui.graphicsView.layer_info_flush()

    def _on_size_tree_widget_toggle_changed(self, turned_on: list[str], turned_off: list[str]):
        for type_size in turned_on:
            component_type, component_size = type_size.split("_")
            self._ui.graphicsView.set_layer_visibility_with_condition({
                "component_type": component_type,
                "component_size": component_size,
                **self._get_combobox_conditions(),
            }, True)

        for type_size in turned_off:
            component_type, component_size = type_size.split("_")
            self._ui.graphicsView.set_layer_visibility_with_condition({
                "component_type": component_type,
                "component_size": component_size,
                **self._get_combobox_conditions(),
            }, False)

    def _on_size_tree_widget_select_changed(self, added: list[str], removed: list[str]):
        for type_size in added:
            component_type, component_size = type_size.split("_")
            self._ui.graphicsView.set_layer_highlight_with_condition({
                "component_type": component_type,
                "component_size": component_size,
                **self._get_combobox_conditions(),
            }, True)
        for type_size in removed:
            component_type, component_size = type_size.split("_")
            self._ui.graphicsView.set_layer_highlight_with_condition({
                "component_type": component_type,
                "component_size": component_size,
                **self._get_combobox_conditions(),
            }, False)

    def _on_id_tree_widget_toggle_changed(self, turned_on: list[str], turned_off: list[str]):
        for type_id in turned_on:
            component_type, component_id = type_id.split("_")
            self._ui.graphicsView.set_layer_visibility_with_condition({
                "component_type": component_type,
                "component_id": component_id,
                **self._get_combobox_conditions(),
            }, True)

        for type_id in turned_off:
            component_type, component_id = type_id.split("_")
            self._ui.graphicsView.set_layer_visibility_with_condition({
                "component_type": component_type,
                "component_id": component_id,
                **self._get_combobox_conditions(),
            }, False)

    def _on_id_tree_widget_select_changed(self, added: list[str], removed: list[str]):
        for type_id in added:
            component_type, component_id = type_id.split("_")
            self._ui.graphicsView.set_layer_highlight_with_condition({
                "component_type": component_type,
                "component_id": component_id,
                **self._get_combobox_conditions(),
            }, True)
        for type_id in removed:
            component_type, component_id = type_id.split("_")
            self._ui.graphicsView.set_layer_highlight_with_condition({
                "component_type": component_type,
                "component_id": component_id,
                **self._get_combobox_conditions(),
            }, False)

    def _re_render_graphics_view_by_size(self):
        for type_size, status in self._ui.treeWidgetSelectSize.get_all_item_check_status():
            component_type, component_size = type_size.split("_")
            self._ui.graphicsView.set_layer_visibility_with_condition({
                "component_type": component_type,
                "component_size": component_size,
                **self._get_combobox_conditions(),
            }, status)

    def _re_render_graphics_view_by_id(self):
        for type_id, status in self._ui.treeWidgetSelectId.get_all_item_check_status():
            component_type, component_id = type_id.split("_")
            self._ui.graphicsView.set_layer_visibility_with_condition({
                "component_type": component_type,
                "component_id": component_id,
                **self._get_combobox_conditions(),
            }, status)

    def _get_combobox_conditions(self):
        line_id = self._ui.comboBoxLineId.currentText()
        panel_id = self._ui.comboboxPanelId.currentText()
        return {
            "line_id": line_id if line_id != "All" else None,
            "panel_id": panel_id if panel_id != "All" else None,
        }

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
            self._ui.graphicsView.close_layer("component_size")
            self._ui.treeWidgetSelectId.clearSelection()
            self._re_render_graphics_view_by_id()
        elif button == self._ui.pushButtonSelectSize:
            self._ui.stackedWidgetSelectionMode.setCurrentWidget(self._ui.pageSelectSize)
            self._ui.graphicsView.close_layer("component_id")
            self._ui.treeWidgetSelectSize.clearSelection()
            self._re_render_graphics_view_by_size()
        else:
            raise ValueError("Invalid button clicked.")

    def _on_combobox_changed(self):
        if self._ui.pushButtonSelectSize.isChecked():
            self._ui.graphicsView.close_layer("component_size")
            self._re_render_graphics_view_by_size()
        elif self._ui.pushButtonSelectId.isChecked():
            self._ui.graphicsView.close_layer("component_id")
            self._re_render_graphics_view_by_id()
        else:
            raise ValueError("Invalid button clicked.")

    def parse_spi_file(self, path: str):
        if os.path.exists(path):
            self.canvas_config = self._setting_dialog.export_canvas_config()
            self._parse_spi_file_thread.add_task(path, self._spi_component_manager, self.canvas_config)

    def on_set_canvas_clicked(self):
        new_canvas_config = self._setting_dialog.exec_with_params(self.canvas_config)
        if new_canvas_config is None:
            return

        self._ui.graphicsView.setEnabled(False)
        run_mode = self.canvas_config.compare(new_canvas_config)
        self.canvas_config = new_canvas_config
        if run_mode == 1:
            self._parse_spi_file_thread.add_task(
                self._ui.lineEditFilePath.text(), self._spi_component_manager, self.canvas_config
            )
        elif run_mode == 2:
            self._render_all_components()
        elif run_mode == 3:
            self._ui.graphicsView.imshow(np.full(
                self.canvas_config.canvas_size, self.canvas_config.background_color[::-1], dtype=np.uint8
            ))
        self._ui.graphicsView.setEnabled(True)



if __name__ == '__main__':
    ...