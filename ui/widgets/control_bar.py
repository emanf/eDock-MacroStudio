from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDoubleSpinBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSpinBox


class ControlBar(QFrame):
    run_main_clicked = Signal()
    run_selected_clicked = Signal()
    pause_clicked = Signal()
    record_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Panel")
        self.build_ui()

    def build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        self.run_main_button = QPushButton("Run")
        self.run_main_button.setObjectName("Success")
        self.run_main_button.setMinimumWidth(80)
        self.run_main_button.clicked.connect(lambda: self.run_main_clicked.emit())

        self.run_button = QPushButton("Run Selected Macro")
        self.run_button.setObjectName("Accent")
        self.run_button.setMinimumWidth(150)
        self.run_button.clicked.connect(lambda: self.run_selected_clicked.emit())

        self.pause_button = QPushButton("Pause")
        self.pause_button.setObjectName("Warning")
        self.pause_button.clicked.connect(lambda: self.pause_clicked.emit())
        self.pause_button.setEnabled(False)

        self.record_button = QPushButton("Record")
        self.record_button.setObjectName("Primary")
        self.record_button.clicked.connect(lambda: self.record_clicked.emit())

        loop_label = QLabel("Loop")
        loop_label.setObjectName("Tiny")
        self.loop_input = QSpinBox()
        self.loop_input.setMinimum(1)
        self.loop_input.setMaximum(999999)
        self.loop_input.setValue(1)

        speed_label = QLabel("Speed")
        speed_label.setObjectName("Tiny")
        self.speed_input = QDoubleSpinBox()
        self.speed_input.setMinimum(0.05)
        self.speed_input.setMaximum(20)
        self.speed_input.setDecimals(2)
        self.speed_input.setSingleStep(0.25)
        self.speed_input.setValue(1)

        delay_label = QLabel("Delay ms")
        delay_label.setObjectName("Tiny")
        self.delay_input = QSpinBox()
        self.delay_input.setMinimum(0)
        self.delay_input.setMaximum(86400000)
        self.delay_input.setSingleStep(100)
        self.delay_input.setValue(0)

        max_depth_label = QLabel("Max Depth")
        max_depth_label.setObjectName("Tiny")
        self.max_depth_input = QSpinBox()
        self.max_depth_input.setMinimum(1)
        self.max_depth_input.setMaximum(999999)
        self.max_depth_input.setValue(10)

        layout.addWidget(self.run_main_button)
        layout.addWidget(self.run_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.record_button)
        layout.addSpacing(12)
        layout.addWidget(loop_label)
        layout.addWidget(self.loop_input)
        layout.addWidget(speed_label)
        layout.addWidget(self.speed_input)
        layout.addWidget(delay_label)
        layout.addWidget(self.delay_input)
        layout.addWidget(max_depth_label)
        layout.addWidget(self.max_depth_input)
        layout.addStretch()

    def loop_count(self):
        return self.loop_input.value()

    def speed(self):
        return self.speed_input.value()

    def delay_ms(self):
        return self.delay_input.value()

    def max_depth(self):
        return self.max_depth_input.value()

    def execution_data(self):
        return {
            "loop_count": self.loop_count(),
            "speed": self.speed(),
            "delay_ms": self.delay_ms(),
            "max_depth": self.max_depth(),
        }

    def set_execution_data(self, execution):
        execution = execution if isinstance(execution, dict) else {}
        self.loop_input.setValue(max(1, int(execution.get("loop_count", 1) or 1)))
        self.speed_input.setValue(max(0.05, float(execution.get("speed", 1.0) or 1.0)))
        self.delay_input.setValue(max(0, int(execution.get("delay_ms", 0) or 0)))
        self.max_depth_input.setValue(max(1, int(execution.get("max_depth", 10) or 10)))

    def set_pause_text(self, text):
        self.pause_button.setText(text)

    def set_mode(self, mode="idle"):
        if mode is True:
            mode = "running"
        elif mode is False or mode is None:
            mode = "idle"

        if mode == "main_running":
            self.run_main_button.setText("Stop")
            self.run_main_button.setObjectName("Danger")
            self.run_main_button.setEnabled(True)
            self.run_button.setText("Run Selected Macro")
            self.run_button.setObjectName("Accent")
            self.run_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.record_button.setText("Record")
            self.record_button.setObjectName("Primary")
            self.record_button.setEnabled(False)
        elif mode == "selected_running":
            self.run_button.setText("Stop")
            self.run_button.setObjectName("Danger")
            self.run_button.setEnabled(True)
            self.run_main_button.setText("Run")
            self.run_main_button.setObjectName("Success")
            self.run_main_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.record_button.setText("Record")
            self.record_button.setObjectName("Primary")
            self.record_button.setEnabled(False)
        elif mode == "recording":
            self.record_button.setText("Stop Recording")
            self.record_button.setObjectName("Danger")
            self.record_button.setEnabled(True)
            self.run_main_button.setText("Run")
            self.run_main_button.setObjectName("Success")
            self.run_main_button.setEnabled(False)
            self.run_button.setText("Run Selected Macro")
            self.run_button.setObjectName("Accent")
            self.run_button.setEnabled(False)
            self.pause_button.setText("Pause")
            self.pause_button.setEnabled(False)
            self.pause_button.setObjectName("Warning")
        else:
            self.run_main_button.setText("Run")
            self.run_main_button.setObjectName("Success")
            self.run_main_button.setEnabled(True)
            self.run_button.setText("Run Selected Macro")
            self.run_button.setObjectName("Accent")
            self.run_button.setEnabled(True)
            self.pause_button.setText("Pause")
            self.pause_button.setEnabled(False)
            self.pause_button.setObjectName("Warning")
            self.record_button.setText("Record")
            self.record_button.setObjectName("Primary")
            self.record_button.setEnabled(True)

        style = self.window().styleSheet() if self.window() else self.styleSheet()
        self.run_main_button.setStyleSheet(style)
        self.run_button.setStyleSheet(style)
        self.pause_button.setStyleSheet(style)
        self.record_button.setStyleSheet(style)
