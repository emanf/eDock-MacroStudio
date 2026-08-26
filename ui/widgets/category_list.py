from PySide6.QtCore import Signal, QSize
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from core.rendering.material_icons import MaterialIcons

from .icon_list_item import IconListItem


class CategoryList(QListWidget):
    category_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loaded_font_family = MaterialIcons.ensure_font()
        self.currentItemChanged.connect(self.on_current_item_changed)
        
        self.setSpacing(2)
        self.setUniformItemSizes(True)
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

    def set_categories(self, categories):
        self.clear()

        for category in categories or []:
            item = QListWidgetItem(self)
            item.setSizeHint(QSize(100, 48))
            item.setData(1000, category.id)

            widget = IconListItem(
                getattr(category, "icon", "extension"),
                getattr(category, "title", "Untitled"),
                self.loaded_font_family,
                self,
            )

            self.addItem(item)
            self.setItemWidget(item, widget)

        if self.count() > 0:
            self.setCurrentRow(0)

    def on_current_item_changed(self, current, previous):
        if current is None:
            return
        self.category_selected.emit(str(current.data(1000) or ""))
