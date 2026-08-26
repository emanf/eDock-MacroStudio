from PySide6.QtCore import Signal, QSize, Qt, QPoint, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QListWidget,
    QListWidgetItem,
    QStyledItemDelegate,
)

from core.rendering.material_icons import MaterialIcons

from .icon_list_item import IconListItem


COMMAND_ROLE = 1000
SECTION_ROLE = 1001
DEFAULT_SECTION_TITLE = "Other"


class CommandListDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.data(SECTION_ROLE):
            painter.save()

            font = option.font
            font.setBold(True)
            font.setPointSize(9)

            painter.setFont(font)
            painter.setPen(QColor(244, 244, 245, 148))
            painter.drawText(
                option.rect.adjusted(8, 4, -8, -2),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(index.data(Qt.ItemDataRole.DisplayRole) or ""),
            )

            painter.restore()
            return

        super().paint(painter, option, index)


class CommandList(QListWidget):
    command_selected = Signal(object)
    command_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.loaded_font_family = MaterialIcons.ensure_font()
        self.setItemDelegate(CommandListDelegate(self))
        self.setSpacing(2)
        self.setUniformItemSizes(False)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setDefaultDropAction(Qt.CopyAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }

            QListWidget::item {
                background-color: rgba(255, 255, 255, 0.04);
                border-radius: 8px;
            }

            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }

            QListWidget::item:selected {
                background-color: #3b82f6;
            }
        """)

        self.itemClicked.connect(self.on_item_clicked)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)

    def set_commands(self, commands):
        self.clear()

        if not commands:
            return

        commands = [
            command for command in commands
            if not bool(getattr(command, "hidden", False))
        ]

        if not commands:
            return

        has_sections = any(
            str(getattr(command, "section", "") or "").strip()
            for command in commands
        )

        if not has_sections:
            for command in sorted(commands, key=self.command_sort_key):
                self.add_command(command)
            return

        grouped_commands = {}

        for command in commands:
            section = str(getattr(command, "section", "") or "").strip()

            if not section:
                section = DEFAULT_SECTION_TITLE

            grouped_commands.setdefault(section, []).append(command)

        ordered_sections = sorted(
            grouped_commands.keys(),
            key=lambda section: (
                section == DEFAULT_SECTION_TITLE,
                section.casefold(),
            ),
        )

        for section in ordered_sections:
            self.add_section(section)

            for command in sorted(
                grouped_commands[section],
                key=self.command_sort_key,
            ):
                self.add_command(command)

    def command_sort_key(self, command):
        sort_value = getattr(command, "sort", 0)

        if isinstance(sort_value, bool) or not isinstance(sort_value, (int, float)):
            sort_value = 0

        title = str(getattr(command, "title", "Untitled") or "Untitled")

        return sort_value, title.casefold()

    def add_section(self, title):
        item = QListWidgetItem(str(title))
        item.setSizeHint(QSize(100, 28))
        item.setData(SECTION_ROLE, True)
        item.setData(COMMAND_ROLE, None)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setToolTip("")

        self.addItem(item)

    def add_command(self, command):
        icon_key = getattr(command, "icon", "extension")
        is_supported = True

        if hasattr(command, "is_supported_os"):
            is_supported = command.is_supported_os()

        item = QListWidgetItem()
        item.setSizeHint(QSize(100, 48))
        item.setData(COMMAND_ROLE, command)
        item.setData(SECTION_ROLE, False)

        title = getattr(command, "title", "Untitled")

        if not is_supported:
            title = f"{title} (Unsupported)"
            item.setFlags(
                item.flags()
                & ~Qt.ItemFlag.ItemIsEnabled
                & ~Qt.ItemFlag.ItemIsSelectable
                & ~Qt.ItemFlag.ItemIsDragEnabled
            )
            item.setToolTip(
                f"{getattr(command, 'description', '')} "
                "(Not supported on this platform)"
            )
        else:
            item.setToolTip(str(getattr(command, "description", "")))

        self.addItem(item)

        widget = IconListItem(
            icon_key,
            title,
            self.loaded_font_family,
            self,
        )

        if not is_supported:
            widget.set_disabled_state(True)
            widget.setEnabled(False)

        self.setItemWidget(item, widget)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())

        if item is not None and (
            item.data(SECTION_ROLE)
            or not (item.flags() & Qt.ItemFlag.ItemIsEnabled)
        ):
            self.clearSelection()
            self.setCurrentItem(None)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        item = self.itemAt(event.pos())

        if item is not None and (
            item.data(SECTION_ROLE)
            or not (item.flags() & Qt.ItemFlag.ItemIsEnabled)
        ):
            return

        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())

        if item is not None and (
            item.data(SECTION_ROLE)
            or not (item.flags() & Qt.ItemFlag.ItemIsEnabled)
        ):
            return

        super().mouseDoubleClickEvent(event)

    def startDrag(self, supported_actions):
        item = self.itemAt(
            self.viewport().mapFromGlobal(self.cursor().pos())
        )

        if item is None or item.data(SECTION_ROLE) or not (
            item.flags() & Qt.ItemFlag.ItemIsEnabled
        ):
            return

        current_item = self.currentItem()

        if current_item is None or current_item.data(SECTION_ROLE) or not (
            current_item.flags() & Qt.ItemFlag.ItemIsEnabled
        ):
            return

        if item != current_item:
            return

        command = current_item.data(COMMAND_ROLE)

        if command is None:
            return

        command_id = getattr(command, "id", None)

        if not command_id:
            return

        mime_data = QMimeData()
        mime_data.setData(
            "application/x-emanf-macro-command-id",
            str(command_id).encode("utf-8"),
        )
        mime_data.setText(str(command_id))

        drag = QDrag(self)
        drag.setMimeData(mime_data)

        item_rect = self.visualItemRect(current_item)

        if item_rect.isValid():
            source_pixmap = self.viewport().grab(item_rect)

            drag_pixmap = QPixmap(source_pixmap.size())
            drag_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(drag_pixmap)
            painter.setOpacity(0.5)
            painter.drawPixmap(0, 0, source_pixmap)
            painter.end()

            drag.setPixmap(drag_pixmap)
            drag.setHotSpot(QPoint(12, item_rect.height() // 2))

        drag.exec(Qt.DropAction.CopyAction)

    def on_item_clicked(self, item):
        if item is None or item.data(SECTION_ROLE) or not (
            item.flags() & Qt.ItemFlag.ItemIsEnabled
        ):
            return

        command = item.data(COMMAND_ROLE)

        if command:
            self.command_selected.emit(command)

    def on_item_double_clicked(self, item):
        if item is None or item.data(SECTION_ROLE) or not (
            item.flags() & Qt.ItemFlag.ItemIsEnabled
        ):
            return

        command = item.data(COMMAND_ROLE)

        if command:
            self.command_requested.emit(getattr(command, "id", None))
