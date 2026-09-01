from copy import deepcopy

from PySide6.QtCore import Signal, QSize, Qt, QPoint, QRect, QMimeData
from PySide6.QtGui import QAction, QDrag, QKeySequence, QPixmap, QPainter, QPen, QColor
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView, QMenu, QApplication

from .number_list_item import NumberListItem


class MacroList(QListWidget):
    item_edit_requested = Signal(int)
    macro_dropped = Signal(object, int)
    item_delete_requested = Signal(object)
    item_copy_requested = Signal(object)
    item_cut_requested = Signal(object)
    item_paste_requested = Signal(int)
    item_toggle_enabled_requested = Signal(int)
    undo_requested = Signal()
    redo_requested = Signal()
    history_state_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items_data = []
        self.registry = None
        self.external_drop_row = None
        self.play_mode = False
        self.highlighted_step_index = -1
        self._history_locked = False

        self.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDragDropOverwriteMode(False)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)

        self.setSpacing(2)
        self.setUniformItemSizes(True)
        self.apply_macro_style()

    def apply_macro_style(self):
        selected_color = "#e87868" if self.play_mode else "#26272d"
        accent_color = "#e87868" if self.play_mode else "#d9b45b"

        self.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}

            QListWidget::item {{
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid transparent;
                border-radius: 8px;
                color: #f0f0f2;
            }}

            QListWidget::item:hover {{
                background-color: rgba(255, 255, 255, 0.08);
            }}

            QListWidget::item:selected {{
                background-color: {selected_color};
                border: 1px solid #2f3036;
                border-left: 3px solid {accent_color};
                color: #ffffff;
            }}
        """)

    def set_play_mode(self, enabled):
        self.play_mode = bool(enabled)
        self.setDragEnabled(not self.play_mode)
        if not self.play_mode:
            self.clear_highlight()
        self.apply_macro_style()

    def capture_state(self):
        return {
            "items_data": deepcopy(self.items_data),
            "current_row": self.currentRow(),
            "highlighted_step_index": self.highlighted_step_index,
        }

    def apply_state(self, state):
        if not state:
            return
        self._history_locked = True
        try:
            self.items_data = deepcopy(state["items_data"])
            self.highlighted_step_index = state.get("highlighted_step_index", -1)
            self.external_drop_row = None
            self.refresh(restore_scroll=True)

            current_row = state.get("current_row", -1)
            if self.count() > 0 and current_row >= 0:
                self.setCurrentRow(min(current_row, self.count() - 1))
            else:
                self.setCurrentRow(-1)
        finally:
            self._history_locked = False

    def set_macro_items(self, items, registry):
        self.items_data = list(items or [])
        self.registry = registry
        self.highlighted_step_index = -1
        self.refresh()

    def item_state(self, item_data):
        command_id = str(getattr(item_data, "command_id", "") or "")
        enabled = bool(getattr(item_data, "enabled", True))

        if self.registry is None:
            return {
                "command": None,
                "enabled": enabled,
                "unknown": True,
                "unsupported": False,
                "invalid": True,
            }

        command = self.registry.get(command_id)
        unknown = command is None
        unsupported = False

        if command is not None and hasattr(command, "is_supported_os"):
            unsupported = not command.is_supported_os()

        return {
            "command": command,
            "enabled": enabled,
            "unknown": unknown,
            "unsupported": unsupported,
            "invalid": unknown or unsupported,
        }

    def item_display_text(self, item_data):
        state = self.item_state(item_data)
        command = state["command"]

        if command is None:
            command_id = str(getattr(item_data, "command_id", "") or "").strip() or "unknown"
            return f"{command_id} (Unknown)"

        text = self.registry.command_display_text(item_data)
        if state["unsupported"]:
            return f"{text} (Unsupported OS)"

        return text

    def row_is_invalid(self, row):
        item_data = self.get_item_at(row)
        if item_data is None:
            return False
        return self.item_state(item_data)["invalid"]

    def refresh(self, restore_scroll=False):
        v_bar = self.verticalScrollBar()
        old_scroll = v_bar.value()
        current_row = self.currentRow()

        self.clear()

        if self.registry is None:
            return

        for index, item_data in enumerate(self.items_data):
            text = self.item_display_text(item_data)
            state = self.item_state(item_data)

            item = QListWidgetItem()
            item.setSizeHint(QSize(100, 48))
            item.setData(1000, item_data)

            widget = NumberListItem(index + 1, text, self)
            widget.set_running(index == self.highlighted_step_index)
            widget.set_disabled_state((not state["enabled"]) or state["invalid"])

            tooltip_lines = []

            if state["unknown"]:
                tooltip_lines.append("Unknown command")
            elif state["unsupported"]:
                tooltip_lines.append("Unsupported on this operating system")

            if not state["enabled"]:
                tooltip_lines.append("Disabled")

            if tooltip_lines:
                item.setToolTip(" | ".join(tooltip_lines))
                widget.setToolTip(" | ".join(tooltip_lines))
            else:
                item.setToolTip("")
                widget.setToolTip("")

            self.addItem(item)
            self.setItemWidget(item, widget)

        if self.highlighted_step_index >= 0 and self.highlighted_step_index < self.count():
            self.setCurrentRow(self.highlighted_step_index)
        elif self.count() > 0 and current_row >= 0:
            self.setCurrentRow(min(current_row, self.count() - 1))

        if restore_scroll:
            v_bar.setValue(old_scroll)

    def selected_rows(self):
        rows = [self.row(item) for item in self.selectedItems()]
        rows = [row for row in rows if row >= 0]
        return sorted(set(rows))

    def _select_range(self, start_row, count):
        self.clearSelection()
        first = max(0, start_row)
        last = max(-1, min(start_row + count - 1, self.count() - 1))

        for row in range(first, last + 1):
            item = self.item(row)
            if item is not None:
                item.setSelected(True)

        self.setCurrentRow(last)

    def mousePressEvent(self, event):
        if self.play_mode:
            event.ignore()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.play_mode:
            event.ignore()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.play_mode:
            event.ignore()
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        if self.play_mode:
            event.ignore()
            return
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if self.play_mode:
            event.ignore()
            return

        if event.matches(QKeySequence.StandardKey.Undo):
            self.undo_requested.emit()
            event.accept()
            return

        if event.matches(QKeySequence.StandardKey.Redo):
            self.redo_requested.emit()
            event.accept()
            return

        if event.matches(QKeySequence.StandardKey.Copy):
            selected_rows = self.selected_rows()
            if selected_rows:
                self.item_copy_requested.emit(selected_rows)
            event.accept()
            return

        if event.matches(QKeySequence.StandardKey.Cut):
            selected_rows = self.selected_rows()
            if selected_rows:
                self.item_cut_requested.emit(selected_rows)
            event.accept()
            return

        if event.matches(QKeySequence.StandardKey.Paste):
            row = self.currentRow()
            if row < 0:
                row = len(self.items_data)
            self.item_paste_requested.emit(row)
            event.accept()
            return

        super().keyPressEvent(event)

    def startDrag(self, supported_actions):
        if self.play_mode:
            return

        if not QApplication.mouseButtons() & Qt.MouseButton.LeftButton:
            return

        rows = self.selected_rows()

        if not rows:
            item = self.currentItem()
            if item is not None:
                rows = [self.row(item)]

        rows = [
            row
            for row in rows
            if row >= 0 and not self.row_is_invalid(row)
        ]

        if not rows:
            return

        mime_data = QMimeData()
        mime_data.setData(
            "application/x-emanf-macro-row",
            ",".join(str(row) for row in rows).encode("utf-8"),
        )

        drag = QDrag(self)
        drag.setMimeData(mime_data)

        drag_rect = QRect()

        for row in rows:
            drag_rect = drag_rect.united(self.visualItemRect(self.item(row)))

        if not drag_rect.isValid():
            return

        source_pixmap = self.viewport().grab(drag_rect)

        drag_pixmap = QPixmap(source_pixmap.size())
        drag_pixmap.fill(Qt.transparent)

        painter = QPainter(drag_pixmap)
        painter.setOpacity(0.5)
        painter.drawPixmap(0, 0, source_pixmap)
        painter.end()

        drag.setPixmap(drag_pixmap)
        drag.setHotSpot(QPoint(12, min(24, drag_rect.height() // 2)))
        drag.exec(Qt.CopyAction | Qt.MoveAction, Qt.MoveAction)

    def dragEnterEvent(self, event):
        if self.play_mode:
            event.ignore()
            return

        if event.mimeData().hasFormat("application/x-emanf-macro-command-id"):
            event.setDropAction(Qt.CopyAction)
            event.accept()
            return

        if event.mimeData().hasFormat("application/x-emanf-macro-row"):
            if event.keyboardModifiers() & Qt.ControlModifier:
                event.setDropAction(Qt.CopyAction)
            else:
                event.setDropAction(Qt.MoveAction)
            event.accept()
            return

        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self.play_mode:
            event.ignore()
            return

        if event.mimeData().hasFormat("application/x-emanf-macro-command-id"):
            self.external_drop_row = self.drop_row_from_event(event)
            self.viewport().update()
            event.setDropAction(Qt.CopyAction)
            event.accept()
            return

        if event.mimeData().hasFormat("application/x-emanf-macro-row"):
            self.external_drop_row = self.drop_row_from_event(event)
            self.viewport().update()
            if event.keyboardModifiers() & Qt.ControlModifier:
                event.setDropAction(Qt.CopyAction)
            else:
                event.setDropAction(Qt.MoveAction)
            event.accept()
            return

        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self.external_drop_row = None
        self.viewport().update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        if self.play_mode:
            event.ignore()
            return

        if event.mimeData().hasFormat("application/x-emanf-macro-command-id"):
            command_id = bytes(event.mimeData().data("application/x-emanf-macro-command-id")).decode("utf-8").strip()
            row = self.drop_row_from_event(event)
            self.external_drop_row = None
            self.viewport().update()
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.macro_dropped.emit(command_id, row)
            return

        if event.mimeData().hasFormat("application/x-emanf-macro-row"):
            source_row_text = bytes(event.mimeData().data("application/x-emanf-macro-row")).decode("utf-8").strip()

            try:
                source_rows = sorted(set(int(part) for part in source_row_text.split(",")))
            except Exception:
                self.external_drop_row = None
                self.viewport().update()
                event.ignore()
                return

            row = self.drop_row_from_event(event)
            copy_mode = bool(event.keyboardModifiers() & Qt.ControlModifier)

            self.external_drop_row = None
            self.viewport().update()

            source_rows = [
                source_row
                for source_row in source_rows
                if 0 <= source_row < len(self.items_data)
                and not self.row_is_invalid(source_row)
            ]

            if not source_rows:
                event.ignore()
                return

            if copy_mode:
                self.history_state_requested.emit()
                insert_row = max(0, min(row, len(self.items_data)))
                copied_items = [deepcopy(self.items_data[source_row]) for source_row in source_rows]

                for offset, copied_item in enumerate(copied_items):
                    self.items_data.insert(insert_row + offset, copied_item)

                self.refresh(restore_scroll=True)
                self._select_range(insert_row, len(copied_items))
                self.history_state_requested.emit()
                event.setDropAction(Qt.CopyAction)
                event.accept()
                return

            contiguous = source_rows == list(range(source_rows[0], source_rows[0] + len(source_rows)))

            if contiguous and source_rows[0] <= row <= source_rows[-1] + 1:
                event.setDropAction(Qt.MoveAction)
                event.accept()
                return

            self.history_state_requested.emit()
            moved_items = [self.items_data[source_row] for source_row in source_rows]
            insert_row = row - sum(1 for source_row in source_rows if source_row < row)

            for source_row in reversed(source_rows):
                self.items_data.pop(source_row)

            insert_row = max(0, min(insert_row, len(self.items_data)))

            for offset, moved_item in enumerate(moved_items):
                self.items_data.insert(insert_row + offset, moved_item)

            self.refresh(restore_scroll=True)
            self._select_range(insert_row, len(moved_items))
            self.history_state_requested.emit()
            event.setDropAction(Qt.MoveAction)
            event.accept()
            return

        self.external_drop_row = None
        self.viewport().update()
        super().dropEvent(event)
        self.history_state_requested.emit()
        self._sync_items_data_from_view()
        self.refresh(restore_scroll=True)
        self.history_state_requested.emit()

    def contextMenuEvent(self, event):
        if self.play_mode:
            return

        item = self.itemAt(event.pos())

        if item is not None:
            if not item.isSelected():
                self.setCurrentItem(item)
            row = self.row(item)
        else:
            self.clearSelection()
            self.setCurrentRow(-1)
            row = -1

        selected_rows = self.selected_rows()
        single_row = selected_rows[0] if len(selected_rows) == 1 else row
        single_item = self.get_item_at(single_row) if single_row >= 0 else None
        single_state = self.item_state(single_item) if single_item is not None else None

        menu = QMenu(self)

        edit_action = QAction("Edit", self)
        toggle_enabled_action = QAction("Disable", self)
        undo_action = QAction("Undo", self)
        redo_action = QAction("Redo", self)
        copy_action = QAction("copy", self)
        cut_action = QAction("cut", self)
        paste_action = QAction("paste", self)
        delete_action = QAction("delete", self)

        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_action.setEnabled(len(selected_rows) == 1 and single_state is not None and not single_state["invalid"])
        copy_action.setEnabled(len(selected_rows) > 0)
        cut_action.setEnabled(len(selected_rows) > 0)
        delete_action.setEnabled(len(selected_rows) > 0)
        toggle_enabled_action.setEnabled(len(selected_rows) == 1 and single_item is not None)

        can_undo = False
        can_redo = False
        parent_window = self.window()
        if parent_window is not None and hasattr(parent_window, "get_macro_history_availability"):
            can_undo, can_redo = parent_window.get_macro_history_availability()

        undo_action.setEnabled(can_undo)
        redo_action.setEnabled(can_redo)

        if single_item is not None and not getattr(single_item, "enabled", True):
            toggle_enabled_action.setText("Enable")
        else:
            toggle_enabled_action.setText("Disable")

        edit_row = selected_rows[0] if len(selected_rows) == 1 else row
        paste_row = row

        edit_action.triggered.connect(lambda: self.item_edit_requested.emit(edit_row))
        toggle_enabled_action.triggered.connect(lambda: self.item_toggle_enabled_requested.emit(single_row))
        undo_action.triggered.connect(self.undo_requested.emit)
        redo_action.triggered.connect(self.redo_requested.emit)
        copy_action.triggered.connect(lambda: self.item_copy_requested.emit(selected_rows))
        cut_action.triggered.connect(lambda: self.item_cut_requested.emit(selected_rows))
        paste_action.triggered.connect(lambda: self.item_paste_requested.emit(paste_row))
        delete_action.triggered.connect(lambda: self.item_delete_requested.emit(selected_rows))

        menu.addAction(edit_action)
        menu.addAction(toggle_enabled_action)
        menu.addSeparator()
        menu.addAction(undo_action)
        menu.addAction(redo_action)
        menu.addSeparator()
        menu.addAction(copy_action)
        menu.addAction(cut_action)
        menu.addAction(paste_action)
        menu.addSeparator()
        menu.addAction(delete_action)

        menu.exec(event.globalPos())

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.external_drop_row is None:
            return

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#ffffff"), 2))

        row = max(0, min(self.external_drop_row, self.count()))

        if self.count() == 0:
            y = 8
        elif row <= 0:
            rect = self.visualItemRect(self.item(0))
            y = max(2, rect.top() + 1)
        elif row >= self.count():
            rect = self.visualItemRect(self.item(self.count() - 1))
            y = min(self.viewport().height() - 2, rect.bottom() + 3)
        else:
            rect = self.visualItemRect(self.item(row))
            y = max(2, rect.top() - 3)

        painter.drawLine(8, y, self.viewport().width() - 8, y)
        painter.end()

    def drop_row_from_event(self, event):
        try:
            position = event.position().toPoint()
        except Exception:
            position = event.pos()

        if self.count() == 0:
            return 0

        for row in range(self.count()):
            rect = self.visualItemRect(self.item(row))
            if position.y() <= rect.center().y():
                return row

        return self.count()

    def _sync_items_data_from_view(self):
        reordered_items = []

        for row in range(self.count()):
            item = self.item(row)
            reordered_items.append(item.data(1000))

        self.items_data = reordered_items

    def add_macro_item(self, item, registry):
        self.registry = registry
        self.items_data.append(item)
        self.refresh(restore_scroll=True)
        if self.count() > 0:
            self.setCurrentRow(self.count() - 1)

    def insert_macro_item(self, index, item, registry):
        self.registry = registry
        index = max(0, min(index, len(self.items_data)))
        self.items_data.insert(index, item)
        self.refresh(restore_scroll=True)
        self.setCurrentRow(index)

    def update_macro_item(self, index, item, registry):
        if index < 0 or index >= len(self.items_data):
            return False
        self.registry = registry
        self.items_data[index] = item
        self.refresh(restore_scroll=True)
        self.setCurrentRow(index)
        return True

    def remove_current(self, registry):
        rows = self.selected_rows()
        if not rows:
            row = self.currentRow()
            rows = [row] if 0 <= row < len(self.items_data) else []

        if not rows:
            return False

        self.registry = registry
        removed = False
        next_row = rows[0]

        for row in sorted(rows, reverse=True):
            if row < 0 or row >= len(self.items_data):
                continue
            self.items_data.pop(row)
            removed = True

        if not removed:
            return False

        self.refresh(restore_scroll=True)
        if self.count() > 0:
            self.setCurrentRow(min(next_row, self.count() - 1))
        return True

    def remove_row_at(self, row, registry):
        if row < 0 or row >= len(self.items_data):
            return False
        self.registry = registry
        self.items_data.pop(row)
        self.refresh(restore_scroll=True)
        if self.count() > 0:
            self.setCurrentRow(min(row, self.count() - 1))
        return True

    def remove_rows_at(self, rows, registry):
        rows = sorted(set(int(row) for row in rows if 0 <= int(row) < len(self.items_data)), reverse=True)
        if not rows:
            return False

        self.registry = registry
        next_row = min(rows)

        for row in rows:
            self.items_data.pop(row)

        self.refresh(restore_scroll=True)
        if self.count() > 0:
            self.setCurrentRow(min(next_row, self.count() - 1))
        return True

    def get_item_at(self, row):
        if row < 0 or row >= len(self.items_data):
            return None
        return self.items_data[row]

    def get_items_at(self, rows):
        items = []
        for row in sorted(set(rows)):
            if row < 0 or row >= len(self.items_data):
                continue
            items.append(self.items_data[row])
        return items

    def move_current_up(self, registry):
        row = self.currentRow()
        if row <= 0 or row >= len(self.items_data):
            return False
        self.registry = registry
        self.items_data[row - 1], self.items_data[row] = self.items_data[row], self.items_data[row - 1]
        self.refresh(restore_scroll=True)
        self.setCurrentRow(row - 1)
        return True

    def move_current_down(self, registry):
        row = self.currentRow()
        if row < 0 or row >= len(self.items_data) - 1:
            return False
        self.registry = registry
        self.items_data[row + 1], self.items_data[row] = self.items_data[row], self.items_data[row + 1]
        self.refresh(restore_scroll=True)
        self.setCurrentRow(row + 1)
        return True

    def set_item_running(self, row, enabled):
        if row < 0 or row >= self.count():
            return
        item = self.item(row)
        if item is None:
            return
        widget = self.itemWidget(item)
        if widget is not None and hasattr(widget, "set_running"):
            widget.set_running(enabled)

    def highlight_step(self, index):
        if index < 0 or index >= self.count():
            return

        if self.highlighted_step_index >= 0 and self.highlighted_step_index != index:
            self.set_item_running(self.highlighted_step_index, False)

        self.highlighted_step_index = index
        self.set_item_running(index, True)
        self.setCurrentRow(index)

        item = self.item(index)
        if item is not None:
            self.scrollToItem(item)

    def clear_highlight(self):
        if self.highlighted_step_index >= 0:
            self.set_item_running(self.highlighted_step_index, False)

        self.highlighted_step_index = -1
        self.clearSelection()
        self.setCurrentRow(-1)

    def on_item_double_clicked(self, item):
        if item is None:
            return

        row = self.row(item)
        if self.row_is_invalid(row):
            return

        self.item_edit_requested.emit(row)
