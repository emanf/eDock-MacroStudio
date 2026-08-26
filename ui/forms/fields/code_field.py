from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QColor, QFontDatabase, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QSizePolicy

from .text_area_field import TextAreaFieldHandler


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.rules = []
        self.triple_single = QRegularExpression("'''")
        self.triple_double = QRegularExpression('"""')

        self.keyword_format = self.create_format("#c678dd")
        self.builtin_format = self.create_format("#61afef")
        self.string_format = self.create_format("#98c379")
        self.comment_format = self.create_format("#7f848e")
        self.number_format = self.create_format("#d19a66")
        self.decorator_format = self.create_format("#56b6c2")
        self.operator_format = self.create_format("#e06c75")
        self.function_format = self.create_format("#e5c07b")

        keywords = [
            "False", "None", "True", "and", "as", "assert", "async", "await", "break",
            "class", "continue", "def", "del", "elif", "else", "except", "finally",
            "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
            "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
        ]

        builtins = [
            "abs", "all", "any", "bool", "dict", "enumerate", "float", "int", "len",
            "list", "max", "min", "print", "range", "round", "set", "str", "sum",
            "tuple", "type", "vars", "runtime", "helper", "ui", "result",
        ]

        for word in keywords:
            self.rules.append((QRegularExpression(r"\b" + word + r"\b"), self.keyword_format))

        for word in builtins:
            self.rules.append((QRegularExpression(r"\b" + word + r"\b"), self.builtin_format))

        self.rules.extend([
            (QRegularExpression(r"#[^\n]*"), self.comment_format),
            (QRegularExpression(r"@[A-Za-z_][A-Za-z0-9_]*"), self.decorator_format),
            (QRegularExpression(r"\b[0-9]+(?:\.[0-9]+)?\b"), self.number_format),
            (QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format),
            (QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format),
            (QRegularExpression(r"\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()"), self.function_format),
            (QRegularExpression(r"[\+\-\*/%=!<>\|\&\^\~]+"), self.operator_format),
        ])

    def create_format(self, color):
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        return text_format

    def highlightBlock(self, text):
        for pattern, text_format in self.rules:
            match_iterator = pattern.globalMatch(text)

            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), text_format)

        self.setCurrentBlockState(0)
        self.highlight_multiline(text, self.triple_single, 1)
        self.highlight_multiline(text, self.triple_double, 2)

    def highlight_multiline(self, text, delimiter, state):
        start_index = 0

        if self.previousBlockState() != state:
            match = delimiter.match(text)
            start_index = match.capturedStart() if match.hasMatch() else -1

        while start_index >= 0:
            match = delimiter.match(text, start_index + 3)
            end_index = match.capturedStart() if match.hasMatch() else -1

            if end_index >= 0:
                length = end_index - start_index + 3
                self.setFormat(start_index, length, self.string_format)
                next_match = delimiter.match(text, start_index + length)
                start_index = next_match.capturedStart() if next_match.hasMatch() else -1
            else:
                self.setCurrentBlockState(state)
                self.setFormat(start_index, len(text) - start_index, self.string_format)
                break


class PythonCodeEditor(QPlainTextEdit):
    indent_text = "    "

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText(self.indent_text)
            return

        if event.key() == Qt.Key.Key_Backtab:
            self.remove_indent()
            return

        super().keyPressEvent(event)

    def remove_indent(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
        selected_text = cursor.selectedText()

        if selected_text.startswith(self.indent_text):
            cursor.removeSelectedText()
            cursor.deleteChar()
            return

        if selected_text.startswith(" "):
            cursor.removeSelectedText()
            cursor.deleteChar()


class CodeFieldHandler(TextAreaFieldHandler):
    def create_widget(self, field, value, parent=None):
        widget = PythonCodeEditor(parent)
        widget.setPlaceholderText(str(field.get("place_holder", "") or ""))
        widget.setPlainText("" if value is None else str(value))
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        widget.setTabStopDistance(widget.fontMetrics().horizontalAdvance(" ") * 4)
        widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(int(field.get("font_size", 10) or 10))
        widget.setFont(font)

        line_count = self.get_line_count(field)
        height = self.calculate_height(widget, line_count)
        widget.setMinimumHeight(height)

        widget.highlighter = PythonSyntaxHighlighter(widget.document())

        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.textChanged.connect(lambda: callback(widget.toPlainText()))

    def get_value(self, field, widget):
        return widget.toPlainText()

    def set_value(self, field, widget, value):
        widget.setPlainText("" if value is None else str(value))
