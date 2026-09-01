from PySide6.QtCore import Signal, QSize, Qt, QPoint, QMimeData
from PySide6.QtGui import QAction, QDrag, QPainter, QPen, QColor, QPixmap
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView, QMenu, QApplication


MACRO_INDEX_ROLE = 1000
ADD_BUTTON_ROLE = 1001
MAIN_ITEM_ROLE = 1002
RUNNING_ROLE = 1003


class MacroTabs(QListWidget):
    macro_selected = Signal(int)
    macro_new_requested = Signal()
    macro_new_here_requested = Signal(int)
    macro_edit_requested = Signal(int)
    macro_copy_requested = Signal(int)
    macro_cut_requested = Signal(int)
    macro_paste_requested = Signal(int)
    macro_delete_requested = Signal(int)
    macro_save_requested = Signal(int)
    macro_reordered = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.external_drop_row = None
        self.play_mode = False
        self.has_macro_clipboard = False
        self.add_pressed = False
        self.add_press_pos = QPoint()
        self.running_rows = set()

        self.setSpacing(4)
        self.setUniformItemSizes(False)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDragDropOverwriteMode(False)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.currentItemChanged.connect(self.on_current_item_changed)
        self.apply_style()

    def apply_style(self):
        selected_color = "#e87868" if self.play_mode else "#26272d"

        self.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}

            QListWidget::item {{
                background-color: #121214;
                border: 1px solid #232428;
                border-radius: 8px;
                padding: 8px;
                color: #d6d6db;
            }}

            QListWidget::item:hover {{
                background-color: #1a1b1e;
                border: 1px solid #2f3036;
            }}

            QListWidget::item:selected {{
                background-color: {selected_color};
                border: 1px solid {selected_color};
                color: white;
            }}
        """)
        self.update_item_styles()

    def update_item_styles(self):
        for row in range(self.count()):
            item = self.item(row)
            if item is None:
                continue

            if self.is_add_item(item):
                item.setBackground(QColor("#121214"))
                item.setForeground(QColor("#d6d6db"))
                continue

            is_running = bool(item.data(RUNNING_ROLE))

            if is_running:
                item.setBackground(QColor("#2f3036" if self.play_mode else "#2f3036"))
                item.setForeground(QColor("#ffffff"))
                continue

            if bool(item.data(MAIN_ITEM_ROLE)):
                item.setBackground(QColor("#0d0d0f"))
                item.setForeground(QColor("#f0f0f2"))
            else:
                item.setBackground(QColor("#121214"))
                item.setForeground(QColor("#d6d6db"))

    def set_play_mode(self, enabled):
        self.play_mode = bool(enabled)
        self.setDragEnabled(not self.play_mode)
        if not self.play_mode:
            self.running_rows.clear()
            for row in range(self.count()):
                item = self.item(row)
                if item is not None:
                    item.setData(RUNNING_ROLE, False)
        self.apply_style()

    def set_macro_clipboard_available(self, available):
        self.has_macro_clipboard = bool(available)

    def macro_clipboard_available(self):
        if self.has_macro_clipboard:
            return True

        window = self.window()
        if window is None:
            return False

        return getattr(window, "macro_clipboard_group", None) is not None

    def set_macros(self, macros, active_index=0):
        self.blockSignals(True)
        self.clear()
        self.add_pressed = False
        self.external_drop_row = None

        for index, macro in enumerate(macros or []):
            title = str(getattr(macro, "title", "") or getattr(macro, "name", "") or "Untitled").strip()
            item = QListWidgetItem(title)
            item.setSizeHint(QSize(0, 36))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setData(MACRO_INDEX_ROLE, index)
            item.setData(ADD_BUTTON_ROLE, False)
            item.setData(MAIN_ITEM_ROLE, index == 0)
            item.setData(RUNNING_ROLE, index in self.running_rows)

            if index == 0:
                item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
            else:
                item.setFlags(item.flags() | Qt.ItemIsDragEnabled)

            self.addItem(item)

        add_item = QListWidgetItem("+")
        add_item.setSizeHint(QSize(0, 36))
        add_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        add_item.setData(MACRO_INDEX_ROLE, -1)
        add_item.setData(ADD_BUTTON_ROLE, True)
        add_item.setData(MAIN_ITEM_ROLE, False)
        add_item.setData(RUNNING_ROLE, False)
        add_item.setFlags(Qt.ItemIsEnabled)
        self.addItem(add_item)

        if self.macro_count() > 0:
            self.setCurrentRow(max(0, min(int(active_index or 0), self.macro_count() - 1)))
        elif self.count() > 0 and bool(self.item(0).data(ADD_BUTTON_ROLE)):
            self.setCurrentRow(-1)

        self.blockSignals(False)
        self.apply_style()
        self.viewport().update()

    def macro_count(self):
        count = self.count()
        if count <= 0:
            return 0

        last_item = self.item(count - 1)
        if last_item is not None and bool(last_item.data(ADD_BUTTON_ROLE)):
            return count - 1

        return count

    def is_add_item(self, item):
        return item is not None and bool(item.data(ADD_BUTTON_ROLE))

    def highlight_macro_group(self, index, active=True):
        try:
            index = int(index)
        except Exception:
            return

        if index < 0 or index >= self.macro_count():
            return

        if active:
            self.running_rows.add(index)
            self.blockSignals(True)
            self.setCurrentRow(index)
            self.blockSignals(False)
        else:
            self.running_rows.discard(index)

        item = self.item(index)
        if item is not None:
            item.setData(RUNNING_ROLE, active)
        self.apply_style()
        self.viewport().update()

    def clear_macro_group_highlights(self):
        self.running_rows.clear()
        for row in range(self.macro_count()):
            item = self.item(row)
            if item is not None:
                item.setData(RUNNING_ROLE, False)
        self.apply_style()
        self.viewport().update()

    def on_current_item_changed(self, current, previous):
        if current is None:
            return

        if self.is_add_item(current):
            if previous is not None and not self.is_add_item(previous):
                self.blockSignals(True)
                self.setCurrentItem(previous)
                self.blockSignals(False)
            else:
                self.blockSignals(True)
                self.clearSelection()
                self.setCurrentRow(-1)
                self.blockSignals(False)
            return

        row = self.row(current)
        self.macro_selected.emit(row)

    def mousePressEvent(self, event):
        if self.play_mode:
            event.ignore()
            return

        self.add_pressed = False
        self.add_press_pos = QPoint()

        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if self.is_add_item(item):
                self.add_pressed = True
                self.add_press_pos = event.pos()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.play_mode:
            event.ignore()
            return

        if self.add_pressed:
            if (event.pos() - self.add_press_pos).manhattanLength() >= QApplication.startDragDistance():
                self.add_pressed = False
                event.accept()
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.play_mode:
            event.ignore()
            return

        if event.button() == Qt.MouseButton.LeftButton and self.add_pressed:
            self.add_pressed = False
            item = self.itemAt(event.pos())
            if self.is_add_item(item) and not self.play_mode:
                self.macro_new_requested.emit()
                event.accept()
            return

        self.add_pressed = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.play_mode:
            event.ignore()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if self.play_mode:
            event.ignore()
            return

        if event.key() == Qt.Key_Delete:
            item = self.currentItem()
            if item is not None and not self.is_add_item(item):
                row = self.row(item)
                if row > 0 and row < self.macro_count():
                    self.macro_delete_requested.emit(row)
                    event.accept()
                    return

        super().keyPressEvent(event)

    def startDrag(self, supported_actions):
        if self.play_mode:
            return

        self.add_pressed = False

        if not QApplication.mouseButtons() & Qt.MouseButton.LeftButton:
            return

        item = self.currentItem()
        if item is None or self.is_add_item(item):
            return

        row = self.row(item)
        if row == 0:
            return

        if row < 0 or row >= self.macro_count():
            return

        mime_data = QMimeData()
        mime_data.setData("application/x-emanf-macro-tab-row", str(row).encode("utf-8"))

        drag = QDrag(self)
        drag.setMimeData(mime_data)

        item_rect = self.visualItemRect(item)
        if item_rect.isValid():
            source_pixmap = self.viewport().grab(item_rect)
            drag_pixmap = QPixmap(source_pixmap.size())
            drag_pixmap.fill(Qt.transparent)

            painter = QPainter(drag_pixmap)
            painter.setOpacity(0.7)
            painter.drawPixmap(0, 0, source_pixmap)
            painter.end()

            drag.setPixmap(drag_pixmap)
            drag.setHotSpot(QPoint(12, item_rect.height() // 2))

        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            drag.exec(Qt.CopyAction | Qt.MoveAction, Qt.CopyAction)
        else:
            drag.exec(Qt.MoveAction)

        self.external_drop_row = None
        self.viewport().update()

    def dragEnterEvent(self, event):
        if self.play_mode:
            event.ignore()
            return

        if event.mimeData().hasFormat("application/x-emanf-macro-tab-row"):
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

        if event.mimeData().hasFormat("application/x-emanf-macro-tab-row"):
            proposed_drop_row = self.drop_row_from_event(event)
            if proposed_drop_row <= 0:
                self.external_drop_row = None
            else:
                self.external_drop_row = proposed_drop_row

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

        if event.mimeData().hasFormat("application/x-emanf-macro-tab-row"):
            source_row_text = bytes(event.mimeData().data("application/x-emanf-macro-tab-row")).decode("utf-8").strip()

            try:
                source_row = int(source_row_text)
            except Exception:
                self.external_drop_row = None
                self.viewport().update()
                event.ignore()
                return

            row = self.drop_row_from_event(event)
            copy_mode = bool(event.keyboardModifiers() & Qt.ControlModifier)

            self.external_drop_row = None
            self.viewport().update()

            if row <= 0:
                event.ignore()
                return

            if source_row <= 0 or source_row >= self.macro_count():
                event.ignore()
                return

            if copy_mode:
                self.macro_copy_requested.emit(source_row)
                paste_row = row - 1
                self.macro_paste_requested.emit(paste_row)
                event.setDropAction(Qt.CopyAction)
                event.accept()
                return

            if source_row == row or source_row + 1 == row:
                event.setDropAction(Qt.MoveAction)
                event.accept()
                return

            self.macro_reordered.emit(source_row, row)
            event.setDropAction(Qt.MoveAction)
            event.accept()
            return

        self.external_drop_row = None
        self.viewport().update()
        super().dropEvent(event)

    def contextMenuEvent(self, event):
        if self.play_mode:
            return

        item = self.itemAt(event.pos())
        is_add = self.is_add_item(item)

        current_item_row = self.row(item) if item is not None and not is_add else -1

        if item is not None and not is_add:
            self.setCurrentItem(item)
        elif item is None:
            self.clearSelection()
            self.setCurrentRow(-1)

        menu = QMenu(self)

        new_here_action = QAction("New Macro Here", self)
        save_action = QAction("Save Macro Group", self)
        copy_action = QAction("Copy", self)
        cut_action = QAction("Cut", self)
        paste_action = QAction("Paste", self)
        delete_action = QAction("Delete", self)

        is_main_macro_selected = current_item_row == 0

        new_here_action.setEnabled(True)
        save_action.setEnabled(current_item_row >= 0)
        copy_action.setEnabled(current_item_row >= 0)
        cut_action.setEnabled(current_item_row >= 0 and not is_main_macro_selected)
        paste_action.setEnabled(self.macro_clipboard_available())
        delete_action.setEnabled(current_item_row >= 0 and not is_main_macro_selected)

        new_here_index = current_item_row + 1 if current_item_row >= 0 else self.macro_count()
        new_here_index = max(1, new_here_index) if self.macro_count() > 0 else 0

        paste_index = current_item_row + 1 if current_item_row >= 0 else self.macro_count()
        paste_index = max(1, paste_index) if self.macro_count() > 0 else 0

        new_here_action.triggered.connect(lambda: self.macro_new_here_requested.emit(new_here_index))
        save_action.triggered.connect(lambda: self.macro_save_requested.emit(current_item_row))
        copy_action.triggered.connect(lambda: self.macro_copy_requested.emit(current_item_row))
        cut_action.triggered.connect(lambda: self.macro_cut_requested.emit(current_item_row))
        paste_action.triggered.connect(lambda: self.macro_paste_requested.emit(paste_index))
        delete_action.triggered.connect(lambda: self.macro_delete_requested.emit(current_item_row))

        menu.addAction(new_here_action)
        menu.addSeparator()
        menu.addAction(save_action)
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

        if self.external_drop_row <= 0:
            return

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#ffffff"), 2))

        row = max(1, min(self.external_drop_row, self.macro_count()))

        if self.macro_count() == 0:
            y = 8
        elif row >= self.macro_count():
            rect = self.visualItemRect(self.item(self.macro_count() - 1))
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

        macro_count = self.macro_count()

        if macro_count == 0:
            return 0

        for row in range(macro_count):
            rect = self.visualItemRect(self.item(row))
            if position.y() <= rect.center().y():
                return row

        return macro_count
