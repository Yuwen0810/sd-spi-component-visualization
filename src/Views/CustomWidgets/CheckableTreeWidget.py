# Built-in Imports
import os
import sys
import cgitb
import traceback
from collections import defaultdict

# Data Science and Third Party Imports

# Machine Learning Imports

# PyQt Imports
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt, QSettings, QSize, QPoint, QSharedMemory, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap, QKeySequence, QShortcut
from PyQt6.QtWidgets import QMainWindow, QSplitter, QSplashScreen, QTreeWidget, QTreeWidgetItem

from src.Configs import COMPONENT_COLORS


# User Imports

# logger = Logger().get_logger()
# logger.info("-" * 50)



class CheckableTreeWidget(QTreeWidget):

    toggle_changed_signal = pyqtSignal(list, list)
    select_changed_signal = pyqtSignal(list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setColumnCount(3)
        self.setExpandsOnDoubleClick(False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.activated.connect(self.clearSelection)

        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(2, 30)

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

        # Toggle
        self._last_child_state: dict[str, Qt.CheckState] = {}
        self._children_items: list[QTreeWidgetItem] = []
        self._toggle_timer = QTimer(self)
        self._toggle_timer.setInterval(100)
        self._toggle_timer.setSingleShot(True)
        self._toggle_timer.timeout.connect(self._on_toggle_changed)
        self.itemChanged.connect(lambda: self._toggle_timer.start())

        # Selection
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)

        self.viewport().installEventFilter(self)

    def populate(self, item_counts: list[list[str, str, int]]):
        self.clear()
        self._last_child_state.clear()
        self._children_items.clear()

        # 建立最上層 <全部>
        self._root = QTreeWidgetItem(["All Components", "", ""])
        self._root.setFlags(
            self._root.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsAutoTristate
        )
        self._root.setCheckState(0, Qt.CheckState.Checked)
        self._root.setData(0, Qt.ItemDataRole.UserRole, "root")
        self.addTopLevelItem(self._root)

        grouped = defaultdict(list)
        for component_type, size, count in item_counts:
            grouped[component_type].append((size, count, QColor(COMPONENT_COLORS.get(component_type, "#000000"))))

        for parent_name, children in grouped.items():
            parent = QTreeWidgetItem([parent_name, "", ""])
            parent.setFlags(
                parent.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsAutoTristate
            )
            parent.setCheckState(0, Qt.CheckState.Checked)
            parent.setData(0, Qt.ItemDataRole.UserRole, parent_name)

            for child_suffix, count, color in children:
                full = f"{parent_name}_{child_suffix}"
                child = QTreeWidgetItem([child_suffix, f"{count:,}", ""])
                child.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                child.setForeground(1, QtGui.QBrush(QtGui.QColor("gray")))
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child.setCheckState(0, Qt.CheckState.Checked)
                child.setData(0, Qt.ItemDataRole.UserRole, full)
                child.setIcon(2, self._make_color_icon(color))
                self._last_child_state[full] = child.checkState(0)
                parent.addChild(child)
                self._children_items.append(child)

            self._root.addChild(parent)
            parent.setExpanded(True)

        self._root.setExpanded(True)

    def _make_color_icon(self, color: QColor) -> QtGui.QIcon:
        pixmap = QPixmap(24, 24)
        pixmap.fill(color)
        return QtGui.QIcon(pixmap)

    def _on_toggle_changed(self):
        last_check = set()
        last_uncheck = set()
        for name, state in self._last_child_state.items():
            if state == Qt.CheckState.Checked:
                last_check.add(name)
            else:
                last_uncheck.add(name)

        cur_check = set()
        cur_uncheck = set()
        for item in self._children_items:
            name = item.data(0, Qt.ItemDataRole.UserRole)
            self._last_child_state[name] = item.checkState(0)
            if item.checkState(0) == Qt.CheckState.Checked:
                cur_check.add(name)
            else:
                cur_uncheck.add(name)

        turned_on = cur_check - last_check
        turned_off = cur_uncheck - last_uncheck
        self.toggle_changed_signal.emit(list(turned_on), list(turned_off))

    def _on_selection_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        select_names = {
            self.itemFromIndex(idx).data(0, Qt.ItemDataRole.UserRole)
            for idx in selected.indexes()
            if idx.column() == 0 and idx.isValid()
        }
        deselect_names = {
            self.itemFromIndex(idx).data(0, Qt.ItemDataRole.UserRole)
            for idx in deselected.indexes()
            if idx.column() == 0 and idx.isValid()
        }

        select_names = {name for name in select_names if "_" in name}
        deselect_names = {name for name in deselect_names if "_" in name}

        self.select_changed_signal.emit(list(select_names), list(deselect_names))

    def get_all_item_check_status(self) -> list[list]:
        """
        Get all items check status.
        :return: list of [item_name, check_status]
        """
        item_check_status = []
        for i in range(self.topLevelItemCount()):
            root_item = self.topLevelItem(i)
            for j in range(root_item.childCount()):
                parent_item = root_item.child(j)
                for k in range(parent_item.childCount()):
                    child_item = parent_item.child(k)
                    item_check_status.append([child_item.data(0, Qt.ItemDataRole.UserRole), child_item.checkState(0) == Qt.CheckState.Checked])

        return item_check_status
