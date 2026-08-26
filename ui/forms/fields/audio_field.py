import base64
import json
import os
import sys
import tempfile
import time
from io import BytesIO
from pathlib import Path

os.environ["QT_LOGGING_RULES"] = ";".join([
    os.environ.get("QT_LOGGING_RULES", ""),
    "qt.multimedia.ffmpeg.debug=false",
    "qt.multimedia.ffmpeg.info=false",
    "qt.multimedia.ffmpeg.warning=false",
]).strip(";")

from PySide6.QtCore import QRectF, Qt, QThread, QTimer, QUrl, Signal, qInstallMessageHandler
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from core.rendering.material_icons import MaterialIcons

from ..base_field import BaseFormField


def qt_error_message_handler(message_type, context, message):
    if message_type.name in ("QtCriticalMsg", "QtFatalMsg"):
        print(message, file=sys.stderr)


qInstallMessageHandler(qt_error_message_handler)


class NativeStderrSilencer:
    def __init__(self):
        self.depth = 0
        self.original_fd = None
        self.null_file = None

    def begin(self):
        try:
            self.depth += 1
            if self.depth > 1:
                return

            sys.stderr.flush()
            self.original_fd = os.dup(2)
            self.null_file = open(os.devnull, "w", encoding="utf-8")
            os.dup2(self.null_file.fileno(), 2)
        except Exception:
            self.depth = 0
            self.original_fd = None
            if self.null_file is not None:
                try:
                    self.null_file.close()
                except Exception:
                    pass
            self.null_file = None

    def end(self):
        try:
            if self.depth <= 0:
                return

            self.depth -= 1
            if self.depth > 0:
                return

            if self.original_fd is not None:
                os.dup2(self.original_fd, 2)
                os.close(self.original_fd)
        except Exception:
            pass
        finally:
            if self.depth <= 0:
                self.depth = 0
                self.original_fd = None
                if self.null_file is not None:
                    try:
                        self.null_file.close()
                    except Exception:
                        pass
                self.null_file = None

    def force_end(self):
        try:
            while self.depth > 0:
                self.end()
        except Exception:
            self.depth = 0
            self.original_fd = None
            if self.null_file is not None:
                try:
                    self.null_file.close()
                except Exception:
                    pass
            self.null_file = None


native_stderr_silencer = NativeStderrSilencer()


def empty_audio():
    return {
        "audio_base64": "",
        "duration": 0.0,
        "file_name": "",
        "sample_rate": 44100,
        "channels": 2,
        "format": "wav",
    }


def normalize_audio(value):
    if isinstance(value, dict):
        audio_base64 = str(value.get("audio_base64", "") or "")
        file_name = str(value.get("file_name", "") or "")
        audio_format = str(value.get("format", "wav") or "wav")

        try:
            duration = float(value.get("duration", 0.0) or 0.0)
        except Exception:
            duration = 0.0

        try:
            sample_rate = int(value.get("sample_rate", 44100) or 44100)
        except Exception:
            sample_rate = 44100

        try:
            channels = int(value.get("channels", 2) or 2)
        except Exception:
            channels = 2

        return {
            "audio_base64": audio_base64,
            "duration": duration,
            "file_name": file_name,
            "sample_rate": sample_rate,
            "channels": channels,
            "format": audio_format,
        }

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return empty_audio()

        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return normalize_audio(parsed)
        except Exception:
            pass

        return {
            "audio_base64": value,
            "duration": 0.0,
            "file_name": "",
            "sample_rate": 44100,
            "channels": 2,
            "format": "wav",
        }

    return empty_audio()


def bytes_to_base64(value):
    if not value:
        return ""
    return base64.b64encode(value).decode("utf-8")


def base64_to_bytes(value):
    value = str(value or "").strip()
    if not value:
        return b""

    try:
        return base64.b64decode(value)
    except Exception:
        return b""


def format_duration(value):
    try:
        seconds = max(0, int(float(value or 0.0)))
    except Exception:
        seconds = 0

    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def get_audio_duration_from_bytes(raw):
    if not raw:
        return 0.0

    try:
        import soundfile as sf
        with sf.SoundFile(BytesIO(raw)) as audio_file:
            if audio_file.samplerate <= 0:
                return 0.0
            return float(len(audio_file) / audio_file.samplerate)
    except Exception:
        return 0.0


def get_audio_info_from_bytes(raw):
    result = empty_audio()

    if not raw:
        return result

    try:
        import soundfile as sf
        with sf.SoundFile(BytesIO(raw)) as audio_file:
            result["duration"] = float(len(audio_file) / audio_file.samplerate) if audio_file.samplerate > 0 else 0.0
            result["sample_rate"] = int(audio_file.samplerate)
            result["channels"] = int(audio_file.channels)
            result["format"] = str(audio_file.format or "wav").lower()
    except Exception:
        result["duration"] = get_audio_duration_from_bytes(raw)

    return result


def audio_base64_to_temp_file(value):
    audio = normalize_audio(value)
    raw = base64_to_bytes(audio.get("audio_base64"))
    if not raw:
        return ""

    suffix = "." + str(audio.get("format", "wav") or "wav").strip(".")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(raw)
    temp_file.flush()
    temp_file.close()
    return temp_file.name


def audio_base64_to_playback_file(value):
    audio = normalize_audio(value)
    raw = base64_to_bytes(audio.get("audio_base64"))
    if not raw:
        return ""

    try:
        import soundfile as sf
        data, sample_rate = sf.read(BytesIO(raw), always_2d=True, dtype="float32")
        if data.size > 0:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.close()
            sf.write(temp_file.name, data, sample_rate, format="WAV")
            return temp_file.name
    except Exception:
        pass

    return audio_base64_to_temp_file(audio)


class AudioRecorderThread(QThread):
    recorded = Signal(object)
    failed = Signal(str)

    def __init__(self, sample_rate=44100, parent=None):
        super().__init__(parent)
        self.sample_rate = int(sample_rate or 44100)
        self.running = False

    def stop(self):
        self.running = False

    def get_loopback_microphone(self):
        try:
            import soundcard as sc
        except Exception:
            raise RuntimeError("soundcard is required. Install it with: pip install soundcard")

        speaker = sc.default_speaker()
        microphones = sc.all_microphones(include_loopback=True)

        for microphone in microphones:
            microphone_name = str(microphone.name).lower()
            speaker_name = str(speaker.name).lower()
            if speaker_name and speaker_name in microphone_name:
                return microphone

        for microphone in microphones:
            microphone_name = str(microphone.name).lower()
            if "loopback" in microphone_name or "monitor" in microphone_name:
                return microphone

        if microphones:
            return microphones[0]

        raise RuntimeError("No loopback audio device found.")

    def run(self):
        try:
            import numpy as np
            import soundfile as sf
        except Exception:
            self.failed.emit("numpy and soundfile are required. Install them with: pip install numpy soundfile")
            return

        try:
            microphone = self.get_loopback_microphone()
            chunks = []
            self.running = True
            start_time = time.time()

            with microphone.recorder(samplerate=self.sample_rate) as recorder:
                while self.running:
                    data = recorder.record(numframes=max(1, int(self.sample_rate * 0.1)))
                    if data is not None and data.size > 0:
                        chunks.append(data)

            if not chunks:
                self.recorded.emit(empty_audio())
                return

            audio_data = np.concatenate(chunks, axis=0).astype("float32")
            duration = float(time.time() - start_time)

            buffer = BytesIO()
            sf.write(buffer, audio_data, self.sample_rate, format="WAV")
            raw = buffer.getvalue()

            channels = 1
            if len(audio_data.shape) > 1:
                channels = int(audio_data.shape[1])

            self.recorded.emit({
                "audio_base64": bytes_to_base64(raw),
                "duration": duration,
                "file_name": "recorded_system_audio.wav",
                "sample_rate": self.sample_rate,
                "channels": channels,
                "format": "wav",
            })
        except Exception as error:
            self.failed.emit(str(error))


class AudioWaveformPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._has_audio = False
        self.setMinimumHeight(48)
        self.setMaximumHeight(48)

    def set_audio(self, value):
        audio = normalize_audio(value)
        self._has_audio = bool(audio.get("audio_base64"))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(QColor("#17191f"))
        painter.setPen(QPen(QColor("#343849"), 1))
        painter.drawRoundedRect(rect, 8, 8)

        center_y = rect.center().y()
        painter.setPen(QPen(QColor("#4b5563"), 1))
        painter.drawLine(rect.left() + 10, center_y, rect.right() - 10, center_y)

        if self._has_audio:
            painter.setPen(QPen(QColor("#4da3ff"), 2))
            width = max(1, rect.width() - 20)
            left = rect.left() + 10
            for index in range(0, width, 5):
                ratio = (index % 30) / 30
                height = 8 + int(22 * abs(0.5 - ratio))
                x = left + index
                painter.drawLine(x, center_y - height // 2, x, center_y + height // 2)
        else:
            painter.setPen(QColor("#9ca3af"))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(QRectF(rect), Qt.AlignmentFlag.AlignCenter, "No audio")

        painter.end()


class AudioPickerInput(QWidget):
    audioChanged = Signal(object)

    def __init__(self, initial_value=None, parent=None):
        super().__init__(parent)
        self._current_value = normalize_audio(initial_value)
        self._recorder = None
        self._recording_started_at = 0.0
        self._playback_file = ""
        self.material_font = MaterialIcons.ensure_font()
        self.setObjectName("AudioPickerInput")

        self.recording_timer = QTimer(self)
        self.recording_timer.setInterval(250)
        self.recording_timer.timeout.connect(self.update_recording_duration)

        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.playbackStateChanged.connect(self.handle_player_state_changed)
        self.player.errorOccurred.connect(self.handle_player_error)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.preview = AudioWaveformPreview(self)
        layout.addWidget(self.preview, 1)

        self.info_label = QLabel(self)
        self.info_label.setMinimumWidth(46)
        self.info_label.setMaximumWidth(54)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

        self.action_button = QPushButton("fiber_manual_record", self)
        self.action_button.setFont(QFont(self.material_font))
        self.action_button.setToolTip("Record audio playing in PC")
        self.action_button.clicked.connect(self.handle_action_button)
        layout.addWidget(self.action_button)

        self.load_button = QPushButton("audio_file", self)
        self.load_button.setFont(QFont(self.material_font))
        self.load_button.setToolTip("Select audio file")
        self.load_button.clicked.connect(self.load_from_file)
        layout.addWidget(self.load_button)

        self.clear_button = QPushButton("close", self)
        self.clear_button.setFont(QFont(self.material_font))
        self.clear_button.setToolTip("Clear audio")
        self.clear_button.clicked.connect(self.clear_value)
        layout.addWidget(self.clear_button)

        self.set_value(self._current_value, emit_signal=False)

    def handle_action_button(self):
        if self._recorder is not None:
            self.stop_recording()
            return

        if self.has_audio():
            self.toggle_playback()
            return

        self.start_recording()

    def has_audio(self):
        return bool(self._current_value.get("audio_base64"))

    def start_recording(self):
        self.stop_playback()
        self._recording_started_at = time.time()
        self.recording_timer.start()
        self.info_label.setText("00:00")
        self.info_label.setToolTip("Recording")
        self.action_button.setText("stop")
        self.action_button.setToolTip("Stop recording")
        self.load_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        self._recorder = AudioRecorderThread(sample_rate=44100, parent=self)
        self._recorder.recorded.connect(self.finish_recording)
        self._recorder.failed.connect(self.recording_failed)
        self._recorder.finished.connect(self.recorder_finished)
        self._recorder.start()

    def stop_recording(self):
        if self._recorder is not None:
            self._recorder.stop()

    def update_recording_duration(self):
        if self._recorder is None:
            self.recording_timer.stop()
            return

        self.info_label.setText(format_duration(time.time() - self._recording_started_at))

    def finish_recording(self, value):
        self.set_value(value)

    def recording_failed(self, message):
        self.recording_timer.stop()
        self.info_label.setText("Error")
        self.info_label.setToolTip(message)

    def recorder_finished(self):
        self.recording_timer.stop()
        self._recorder = None
        self.load_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.update_action_button()
        self.update_preview()

    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.stop_playback()
            return

        self.play_audio()

    def play_audio(self):
        self.stop_playback()

        self._playback_file = audio_base64_to_playback_file(self._current_value)
        if not self._playback_file:
            return

        native_stderr_silencer.begin()
        self.player.setSource(QUrl.fromLocalFile(self._playback_file))
        self.player.play()
        QTimer.singleShot(3000, native_stderr_silencer.force_end)
        self.update_action_button()

    def stop_playback(self):
        if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()
        self.update_action_button()

    def handle_player_state_changed(self, state):
        self.update_action_button()
        if state == QMediaPlayer.PlaybackState.StoppedState:
            native_stderr_silencer.force_end()

    def handle_player_error(self, error, message=""):
        native_stderr_silencer.force_end()
        error_message = str(message or self.player.errorString() or "").strip()
        if error_message:
            print(error_message, file=sys.stderr)

    def load_from_file(self):
        self.stop_playback()

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio",
            "",
            "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a *.aac);;All Files (*.*)",
        )
        if not file_path:
            return

        path = Path(file_path)
        try:
            raw = path.read_bytes()
        except Exception:
            return

        info = get_audio_info_from_bytes(raw)
        info["audio_base64"] = bytes_to_base64(raw)
        info["file_name"] = path.name

        if not info.get("format") or info.get("format") == "wav":
            suffix = path.suffix.strip(".").lower()
            if suffix:
                info["format"] = suffix

        self.set_value(info)

    def clear_value(self):
        self.stop_playback()
        self.set_value(empty_audio())

    def set_value(self, value, emit_signal=True):
        self._current_value = normalize_audio(value)
        self.update_preview()
        self.update_action_button()

        if emit_signal:
            self.audioChanged.emit(self.get_value())

    def update_action_button(self):
        if self._recorder is not None:
            self.action_button.setText("stop")
            self.action_button.setToolTip("Stop recording")
            return

        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.action_button.setText("stop")
            self.action_button.setToolTip("Stop playing audio")
            return

        if self.has_audio():
            self.action_button.setText("play_arrow")
            self.action_button.setToolTip("Play audio")
            return

        self.action_button.setText("fiber_manual_record")
        self.action_button.setToolTip("Record audio playing in PC")

    def update_preview(self):
        if self._recorder is not None:
            self.preview.set_audio(self._current_value)
            self.info_label.setText(format_duration(time.time() - self._recording_started_at))
            self.info_label.setToolTip("Recording")
            return

        duration = float(self._current_value.get("duration", 0.0) or 0.0)
        file_name = str(self._current_value.get("file_name", "") or "")
        has_audio = bool(self._current_value.get("audio_base64"))

        self.preview.set_audio(self._current_value)

        if has_audio:
            self.info_label.setText(format_duration(duration))
            if file_name:
                self.info_label.setToolTip(file_name)
            else:
                self.info_label.setToolTip("")
        else:
            self.info_label.setText("00:00")
            self.info_label.setToolTip("")

    def get_value(self):
        return normalize_audio(self._current_value)


class AudioFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = AudioPickerInput(value, parent)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.audioChanged.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.get_value()

    def set_value(self, field, widget, value):
        widget.set_value(value)
