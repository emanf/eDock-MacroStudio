from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

from core.rendering.material_icons import MaterialIcons

ICON_COLOR = "#c3c3ca"


def glyph(name, fallback=""):
    return MaterialIcons.glyph(name, fallback)


def paint_glyph(glyph_text, size, color):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    font = QFont(MaterialIcons.ensure_font())
    font.setPixelSize(int(size * 0.9))
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, glyph_text)
    painter.end()

    return pixmap


def icon(name, size=16, color=ICON_COLOR):
    return QIcon(paint_glyph(glyph(name), size, color))
