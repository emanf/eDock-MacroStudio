import math
import sys
import threading
import time
from collections import deque

try:
    import numpy as np
except Exception as error:
    raise RuntimeError(
        "NumPy is required. Install it with: pip install numpy"
    ) from error

try:
    import pyaudiowpatch as pyaudio
except Exception as error:
    raise RuntimeError(
        "PyAudioWPatch is required. Install it with: pip install PyAudioWPatch"
    ) from error

try:
    from PySide6.QtCore import QObject, Qt, Signal
    from PySide6.QtGui import QColor, QFont
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QDoubleSpinBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QProgressBar,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except Exception as error:
    raise RuntimeError(
        "PySide6 is required. Install it with: pip install PySide6"
    ) from error


def device_name_key(name):
    name = str(name or "").casefold()
    replacements = (
        "loopback",
        "stereo mix",
        "what u hear",
        "what you hear",
        "speakers",
        "speaker",
        "headphones",
        "headphone",
        "output",
        "input",
        "(",
        ")",
        "[",
        "]",
        "-",
        "_",
    )

    for replacement in replacements:
        name = name.replace(replacement, " ")

    return " ".join(name.split())


def get_loopback_devices(audio):
    devices = []

    try:
        devices.extend(list(audio.get_loopback_device_info_generator()))
    except Exception:
        pass

    if devices:
        return devices

    try:
        device_count = audio.get_device_count()
    except Exception:
        return devices

    for device_index in range(device_count):
        try:
            device = audio.get_device_info_by_index(device_index)
        except Exception:
            continue

        if bool(device.get("isLoopbackDevice", False)):
            devices.append(device)

    return devices


def find_matching_loopback_device(output_device, loopback_devices):
    if not output_device:
        return None

    output_name = str(output_device.get("name", "") or "").casefold()
    output_key = device_name_key(output_name)
    best_device = None
    best_score = -1

    for device in loopback_devices:
        if int(device.get("maxInputChannels", 0) or 0) <= 0:
            continue

        loopback_name = str(device.get("name", "") or "").casefold()
        loopback_key = device_name_key(loopback_name)
        score = 0

        if output_name and output_name in loopback_name:
            score += 100

        if loopback_name and loopback_name in output_name:
            score += 100

        if output_key and output_key == loopback_key:
            score += 80

        output_words = set(output_key.split())
        loopback_words = set(loopback_key.split())
        score += len(output_words.intersection(loopback_words)) * 10

        if output_device.get("hostApi") == device.get("hostApi"):
            score += 5

        if score > best_score:
            best_score = score
            best_device = device

    return best_device


def get_default_output_device(audio):
    try:
        wasapi_info = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
        output_index = int(wasapi_info.get("defaultOutputDevice", -1))

        if output_index >= 0:
            return audio.get_device_info_by_index(output_index)
    except Exception:
        pass

    try:
        return audio.get_default_output_device_info()
    except Exception:
        return None


def select_default_loopback_device(audio):
    loopback_devices = get_loopback_devices(audio)

    try:
        default_loopback = audio.get_default_wasapi_loopback()

        if (
            default_loopback
            and int(default_loopback.get("maxInputChannels", 0) or 0) > 0
        ):
            return default_loopback
    except Exception:
        pass

    default_output = get_default_output_device(audio)
    matching_device = find_matching_loopback_device(
        default_output,
        loopback_devices,
    )

    if matching_device is not None:
        return matching_device

    for device in loopback_devices:
        if int(device.get("maxInputChannels", 0) or 0) > 0:
            return device

    raise RuntimeError(
        "No PC audio loopback device was found. Make sure an output device "
        "is enabled and PyAudioWPatch is installed."
    )


def get_stream_settings(device):
    sample_rate = int(
        round(float(device.get("defaultSampleRate", 48000) or 48000))
    )
    maximum_channels = int(device.get("maxInputChannels", 0) or 0)

    if maximum_channels <= 0:
        raise RuntimeError(
            f'The device "{device.get("name", "Unknown")}" has no input channels.'
        )

    return sample_rate, min(maximum_channels, 2)


def read_audio_frame(stream, chunk_size, channels):
    frame_data = stream.read(
        chunk_size,
        exception_on_overflow=False,
    )
    samples = np.frombuffer(frame_data, dtype=np.int16)

    if channels > 1:
        usable_count = (samples.size // channels) * channels
        samples = samples[:usable_count]

        if samples.size == 0:
            return np.zeros(chunk_size, dtype=np.float32)

        samples = samples.reshape(-1, channels)
        samples = np.mean(samples, axis=1)

    samples = samples.astype(np.float32, copy=False)

    if samples.size < chunk_size:
        samples = np.pad(samples, (0, chunk_size - samples.size))
    elif samples.size > chunk_size:
        samples = samples[:chunk_size]

    return samples


def calculate_analysis(
    samples,
    window,
    frequencies,
    baseline_rms,
    baseline_spectrum,
    minimum_level_dbfs,
    minimum_volume_increase,
    minimum_spectral_change,
    minimum_confidence,
):
    normalized_samples = samples.astype(np.float32, copy=False) / 32768.0
    normalized_samples -= float(np.mean(normalized_samples))

    rms = float(
        np.sqrt(
            np.mean(normalized_samples * normalized_samples) + 1e-20
        )
    )
    peak = float(np.max(np.abs(normalized_samples)))
    level_dbfs = 20.0 * math.log10(max(rms, 1e-10))
    volume_increase_db = 20.0 * math.log10(
        max(rms / max(baseline_rms, 1e-10), 1e-10)
    )

    spectrum = np.abs(
        np.fft.rfft(normalized_samples * window)
    ) ** 2
    spectrum = np.maximum(spectrum, 1e-20)

    current_total = float(np.sum(spectrum))
    baseline_total = float(np.sum(baseline_spectrum))

    normalized_spectrum = (
        spectrum / current_total
        if current_total > 1e-20
        else spectrum
    )
    normalized_baseline = (
        baseline_spectrum / baseline_total
        if baseline_total > 1e-20
        else baseline_spectrum
    )

    current_norm = float(np.linalg.norm(normalized_spectrum))
    baseline_norm = float(np.linalg.norm(normalized_baseline))

    if current_norm > 1e-20 and baseline_norm > 1e-20:
        similarity = float(
            np.dot(normalized_spectrum, normalized_baseline)
            / (current_norm * baseline_norm)
        )
        similarity = max(0.0, min(1.0, similarity))
        spectral_change = (1.0 - similarity) * 100.0
    else:
        spectral_change = 0.0

    minimum_bin = int(np.searchsorted(frequencies, 20.0))

    if spectrum.size > minimum_bin and current_total > 1e-20:
        dominant_index = minimum_bin + int(
            np.argmax(spectrum[minimum_bin:])
        )
        dominant_frequency = float(frequencies[dominant_index])
    else:
        dominant_frequency = 0.0

    volume_score = 50.0 + (
        volume_increase_db - minimum_volume_increase
    ) * 5.0
    spectral_score = 50.0 + (
        spectral_change - minimum_spectral_change
    ) * 2.5
    level_score = 50.0 + (
        level_dbfs - minimum_level_dbfs
    ) * 2.0

    volume_score = max(0.0, min(100.0, volume_score))
    spectral_score = max(0.0, min(100.0, spectral_score))
    level_score = max(0.0, min(100.0, level_score))

    volume_confidence = volume_score * 0.75 + level_score * 0.25
    spectral_confidence = spectral_score * 0.65 + level_score * 0.35
    confidence = max(volume_confidence, spectral_confidence)

    level_matched = level_dbfs >= minimum_level_dbfs
    volume_matched = volume_increase_db >= minimum_volume_increase
    spectrum_matched = spectral_change >= minimum_spectral_change
    event_matched = level_matched and (
        volume_matched or spectrum_matched
    )
    detected = event_matched and confidence >= minimum_confidence

    return {
        "detected": detected,
        "confidence": confidence,
        "rms": rms,
        "peak": peak,
        "level_dbfs": level_dbfs,
        "volume_increase_db": volume_increase_db,
        "spectral_change": spectral_change,
        "dominant_frequency": dominant_frequency,
        "spectrum": spectrum,
    }


class AudioSignals(QObject):
    data_ready = Signal(dict)
    state_changed = Signal(str)
    error = Signal(str)
    devices_ready = Signal(list, int)


class AudioMonitorWorker:
    def __init__(self):
        self.signals = AudioSignals()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread = None
        self.settings_lock = threading.Lock()
        self.device_index = None
        self.calibration_duration = 1.0
        self.minimum_confidence = 65.0
        self.minimum_level_dbfs = -50.0
        self.minimum_volume_increase = 8.0
        self.minimum_spectral_change = 32.0

    def update_settings(
        self,
        calibration_duration,
        minimum_confidence,
        minimum_level_dbfs,
        minimum_volume_increase,
        minimum_spectral_change,
    ):
        with self.settings_lock:
            self.calibration_duration = float(calibration_duration)
            self.minimum_confidence = float(minimum_confidence)
            self.minimum_level_dbfs = float(minimum_level_dbfs)
            self.minimum_volume_increase = float(
                minimum_volume_increase
            )
            self.minimum_spectral_change = float(
                minimum_spectral_change
            )

    def set_device(self, device_index):
        self.device_index = device_index

    def load_devices(self):
        def task():
            audio = None

            try:
                audio = pyaudio.PyAudio()
                devices = get_loopback_devices(audio)
                devices = [
                    device
                    for device in devices
                    if int(device.get("maxInputChannels", 0) or 0) > 0
                ]

                default_device = select_default_loopback_device(audio)
                default_index = int(default_device["index"])
                result = []

                for device in devices:
                    result.append(
                        {
                            "index": int(device["index"]),
                            "name": str(device.get("name", "Unknown")),
                            "sample_rate": int(
                                round(
                                    float(
                                        device.get(
                                            "defaultSampleRate",
                                            48000,
                                        )
                                        or 48000
                                    )
                                )
                            ),
                            "channels": int(
                                device.get("maxInputChannels", 0) or 0
                            ),
                        }
                    )

                self.signals.devices_ready.emit(result, default_index)
            except Exception as error:
                self.signals.error.emit(str(error))
            finally:
                if audio is not None:
                    audio.terminate()

        threading.Thread(target=task, daemon=True).start()

    def start(self):
        if self.thread is not None and self.thread.is_alive():
            self.pause_event.clear()
            self.signals.state_changed.emit("Listening")
            return

        self.stop_event.clear()
        self.pause_event.clear()
        self.thread = threading.Thread(
            target=self.run,
            daemon=True,
        )
        self.thread.start()

    def pause(self):
        self.pause_event.set()
        self.signals.state_changed.emit("Paused")

    def stop(self):
        self.stop_event.set()
        self.pause_event.clear()

    def read_settings(self):
        with self.settings_lock:
            return {
                "calibration_duration": self.calibration_duration,
                "minimum_confidence": self.minimum_confidence,
                "minimum_level_dbfs": self.minimum_level_dbfs,
                "minimum_volume_increase": self.minimum_volume_increase,
                "minimum_spectral_change": self.minimum_spectral_change,
            }

    def run(self):
        audio = None
        stream = None

        try:
            self.signals.state_changed.emit("Opening audio device")
            audio = pyaudio.PyAudio()

            if self.device_index is None:
                device = select_default_loopback_device(audio)
            else:
                device = audio.get_device_info_by_index(
                    int(self.device_index)
                )

            sample_rate, channels = get_stream_settings(device)
            chunk_size = 2048
            window = np.hanning(chunk_size).astype(np.float32)
            frequencies = np.fft.rfftfreq(
                chunk_size,
                1.0 / sample_rate,
            ).astype(np.float32)

            stream = audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=int(device["index"]),
                frames_per_buffer=chunk_size,
            )

            settings = self.read_settings()
            calibration_frame_count = max(
                1,
                int(
                    math.ceil(
                        settings["calibration_duration"]
                        * sample_rate
                        / chunk_size
                    )
                ),
            )

            self.signals.state_changed.emit("Calibrating")
            rms_values = []
            spectra = []

            for _ in range(calibration_frame_count):
                if self.stop_event.is_set():
                    return

                samples = read_audio_frame(
                    stream,
                    chunk_size,
                    channels,
                )
                normalized = samples.astype(
                    np.float32,
                    copy=False,
                ) / 32768.0
                normalized -= float(np.mean(normalized))
                rms = float(
                    np.sqrt(np.mean(normalized * normalized) + 1e-20)
                )
                spectrum = np.abs(
                    np.fft.rfft(normalized * window)
                ) ** 2
                rms_values.append(rms)
                spectra.append(spectrum)

            baseline_rms = max(
                float(np.percentile(rms_values, 70)),
                1e-10,
            )
            baseline_spectrum = np.maximum(
                np.percentile(
                    np.stack(spectra),
                    70,
                    axis=0,
                ),
                1e-20,
            )

            self.signals.state_changed.emit("Listening")
            started_at = time.monotonic()
            frame_count = 0

            while not self.stop_event.is_set():
                if self.pause_event.is_set():
                    time.sleep(0.05)
                    continue

                samples = read_audio_frame(
                    stream,
                    chunk_size,
                    channels,
                )
                settings = self.read_settings()
                analysis = calculate_analysis(
                    samples,
                    window,
                    frequencies,
                    baseline_rms,
                    baseline_spectrum,
                    settings["minimum_level_dbfs"],
                    settings["minimum_volume_increase"],
                    settings["minimum_spectral_change"],
                    settings["minimum_confidence"],
                )

                frame_count += 1

                if not analysis["detected"]:
                    baseline_rms = (
                        baseline_rms * 0.995
                        + analysis["rms"] * 0.005
                    )
                    baseline_spectrum = (
                        baseline_spectrum * 0.995
                        + analysis["spectrum"] * 0.005
                    )

                current_time = time.monotonic()
                analysis["timestamp"] = current_time
                analysis["elapsed"] = current_time - started_at
                analysis["device_index"] = int(device["index"])
                analysis["device_name"] = str(device.get("name", ""))
                analysis["sample_rate"] = sample_rate
                analysis["channels"] = channels
                analysis["baseline_rms"] = baseline_rms
                analysis["frames"] = frame_count
                analysis.pop("spectrum", None)
                self.signals.data_ready.emit(analysis)

            self.signals.state_changed.emit("Stopped")
        except Exception as error:
            self.signals.state_changed.emit("Error")
            self.signals.error.emit(str(error))
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                except Exception:
                    pass

                try:
                    stream.close()
                except Exception:
                    pass

            if audio is not None:
                audio.terminate()


class ValueCard(QFrame):
    def __init__(
        self,
        title,
        value="--",
        show_range=True,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("valueCard")
        self.show_range = show_range

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("cardValue")
        self.value_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

        self.range_frame = QFrame()
        self.range_frame.setObjectName("rangeFrame")
        range_layout = QGridLayout(self.range_frame)
        range_layout.setContentsMargins(9, 7, 9, 7)
        range_layout.setHorizontalSpacing(12)
        range_layout.setVerticalSpacing(3)

        min_title = QLabel("MIN")
        min_title.setObjectName("rangeTitle")
        max_title = QLabel("MAX")
        max_title.setObjectName("rangeTitle")

        self.min_label = QLabel("--")
        self.min_label.setObjectName("rangeValue")
        self.max_label = QLabel("--")
        self.max_label.setObjectName("rangeValue")

        self.min_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.max_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        range_layout.addWidget(min_title, 0, 0)
        range_layout.addWidget(max_title, 0, 1)
        range_layout.addWidget(self.min_label, 1, 0)
        range_layout.addWidget(self.max_label, 1, 1)

        layout.addWidget(self.range_frame)
        self.range_frame.setVisible(show_range)

    def set_value(self, value):
        self.value_label.setText(str(value))

    def set_range(self, minimum, maximum):
        self.min_label.setText(str(minimum))
        self.max_label.setText(str(maximum))

    def clear_range(self):
        self.min_label.setText("--")
        self.max_label.setText("--")


class AudioMonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC Audio Data Monitor")
        self.resize(1180, 900)
        self.setMinimumSize(940, 720)
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            True,
        )

        self.worker = AudioMonitorWorker()
        self.latest_data = None
        self.history = deque()

        self.worker.signals.data_ready.connect(self.update_data)
        self.worker.signals.state_changed.connect(self.update_state)
        self.worker.signals.error.connect(self.show_error)
        self.worker.signals.devices_ready.connect(self.set_devices)

        self.build_ui()
        self.apply_style()
        self.connect_controls()
        self.apply_settings()
        self.worker.load_devices()

    def build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title_label = QLabel("PC Audio Data Monitor")
        title_label.setObjectName("windowTitle")

        subtitle_label = QLabel(
            "Real-time loopback audio analysis and threshold testing"
        )
        subtitle_label.setObjectName("subtitle")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        self.state_label = QLabel("Stopped")
        self.state_label.setObjectName("stateLabel")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setFixedHeight(36)
        self.state_label.setMinimumWidth(110)

        self.play_button = QPushButton("Play")
        self.play_button.setObjectName("primaryButton")
        self.pause_button = QPushButton("Pause")
        self.capture_button = QPushButton("Capture Data")
        self.clear_button = QPushButton("Clear Captures")

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.state_label)
        header_layout.addWidget(self.play_button)
        header_layout.addWidget(self.pause_button)
        header_layout.addWidget(self.capture_button)
        header_layout.addWidget(self.clear_button)

        root_layout.addLayout(header_layout)

        settings_frame = QFrame()
        settings_frame.setObjectName("panel")
        settings_layout = QGridLayout(settings_frame)
        settings_layout.setContentsMargins(14, 14, 14, 14)
        settings_layout.setHorizontalSpacing(12)
        settings_layout.setVerticalSpacing(8)

        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(300)

        self.history_duration_spin = QDoubleSpinBox()
        self.history_duration_spin.setRange(0.1, 300.0)
        self.history_duration_spin.setDecimals(1)
        self.history_duration_spin.setSingleStep(0.5)
        self.history_duration_spin.setValue(3.0)
        self.history_duration_spin.setSuffix(" sec")

        self.calibration_spin = QDoubleSpinBox()
        self.calibration_spin.setRange(0.2, 10.0)
        self.calibration_spin.setDecimals(1)
        self.calibration_spin.setSingleStep(0.1)
        self.calibration_spin.setValue(1.0)
        self.calibration_spin.setSuffix(" sec")

        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.0, 100.0)
        self.confidence_spin.setDecimals(1)
        self.confidence_spin.setValue(65.0)
        self.confidence_spin.setSuffix("%")

        self.level_spin = QDoubleSpinBox()
        self.level_spin.setRange(-100.0, 0.0)
        self.level_spin.setDecimals(1)
        self.level_spin.setValue(-50.0)
        self.level_spin.setSuffix(" dBFS")

        self.volume_spin = QDoubleSpinBox()
        self.volume_spin.setRange(
            -sys.float_info.max,
            sys.float_info.max,
        )
        self.volume_spin.setDecimals(1)
        self.volume_spin.setValue(8.0)
        self.volume_spin.setSuffix(" dB")

        self.spectral_spin = QDoubleSpinBox()
        self.spectral_spin.setRange(0.0, 100.0)
        self.spectral_spin.setDecimals(1)
        self.spectral_spin.setValue(32.0)
        self.spectral_spin.setSuffix("%")

        settings_layout.addWidget(QLabel("Audio Device"), 0, 0)
        settings_layout.addWidget(self.device_combo, 1, 0, 1, 2)
        settings_layout.addWidget(QLabel("Min / Max Period"), 0, 2)
        settings_layout.addWidget(self.history_duration_spin, 1, 2)
        settings_layout.addWidget(QLabel("Calibration"), 0, 3)
        settings_layout.addWidget(self.calibration_spin, 1, 3)
        settings_layout.addWidget(QLabel("Min Confidence"), 2, 0)
        settings_layout.addWidget(self.confidence_spin, 3, 0)
        settings_layout.addWidget(QLabel("Min Audio Level"), 2, 1)
        settings_layout.addWidget(self.level_spin, 3, 1)
        settings_layout.addWidget(QLabel("Min Volume Increase"), 2, 2)
        settings_layout.addWidget(self.volume_spin, 3, 2)
        settings_layout.addWidget(QLabel("Min Frequency Change"), 2, 3)
        settings_layout.addWidget(self.spectral_spin, 3, 3)

        root_layout.addWidget(settings_frame)

        meter_frame = QFrame()
        meter_frame.setObjectName("panel")
        meter_layout = QVBoxLayout(meter_frame)
        meter_layout.setContentsMargins(14, 12, 14, 12)
        meter_layout.setSpacing(8)

        meter_header = QHBoxLayout()
        meter_header.addWidget(QLabel("Real-Time Detection Confidence"))

        self.range_period_label = QLabel(
            "Min / Max: last 3.0 seconds"
        )
        self.range_period_label.setObjectName("rangePeriodLabel")
        meter_header.addWidget(self.range_period_label)
        meter_header.addStretch()

        self.detected_label = QLabel("NO AUDIO EVENT")
        self.detected_label.setObjectName("detectedLabel")
        meter_header.addWidget(self.detected_label)

        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 1000)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setFormat("0.0%")

        meter_layout.addLayout(meter_header)
        meter_layout.addWidget(self.confidence_bar)

        root_layout.addWidget(meter_frame)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(10)
        cards_layout.setVerticalSpacing(10)

        self.cards = {
            "confidence": ValueCard("Confidence"),
            "rms": ValueCard("RMS"),
            "peak": ValueCard("Peak"),
            "level_dbfs": ValueCard("Audio Level"),
            "volume_increase_db": ValueCard("Volume Increase"),
            "spectral_change": ValueCard("Frequency Change"),
            "dominant_frequency": ValueCard("Dominant Frequency"),
            "baseline_rms": ValueCard("Baseline RMS"),
            "elapsed": ValueCard("Elapsed", show_range=False),
            "sample_rate": ValueCard("Sample Rate", show_range=False),
            "channels": ValueCard("Channels", show_range=False),
            "frames": ValueCard("Frames Read", show_range=False),
        }

        for index, card in enumerate(self.cards.values()):
            row = index // 4
            column = index % 4
            cards_layout.addWidget(card, row, column)

        root_layout.addLayout(cards_layout)

        table_frame = QFrame()
        table_frame.setObjectName("panel")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(14, 12, 14, 14)

        table_title = QLabel("Captured Data")
        table_title.setObjectName("sectionTitle")

        self.capture_table = QTableWidget(0, 9)
        self.capture_table.setHorizontalHeaderLabels(
            [
                "Time",
                "Detected",
                "Confidence",
                "RMS",
                "Peak",
                "Level",
                "Increase",
                "Frequency Change",
                "Dominant Hz",
            ]
        )
        self.capture_table.verticalHeader().setVisible(False)
        self.capture_table.setAlternatingRowColors(True)
        self.capture_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.capture_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.capture_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        table_layout.addWidget(table_title)
        table_layout.addWidget(self.capture_table)

        root_layout.addWidget(table_frame, 1)

    def apply_style(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #101114;
                color: #e5e7eb;
                font-family: "Segoe UI";
                font-size: 13px;
            }
            #windowTitle {
                font-size: 23px;
                font-weight: 700;
                color: #f9fafb;
            }
            #subtitle {
                color: #8b93a1;
            }
            #panel, #valueCard {
                background: #17191f;
                border: 1px solid #292d36;
                border-radius: 10px;
            }
            #cardTitle {
                color: #8b93a1;
                font-size: 12px;
                font-weight: 600;
            }
            #cardValue {
                color: #f9fafb;
                font-size: 18px;
                font-weight: 650;
            }
            #rangeFrame {
                background: #111319;
                border: 1px solid #252a34;
                border-radius: 7px;
            }
            #rangeTitle {
                color: #6b7280;
                font-size: 9px;
                font-weight: 700;
            }
            #rangeValue {
                color: #cbd5e1;
                font-size: 11px;
                font-weight: 650;
            }
            #rangePeriodLabel {
                padding: 4px 9px;
                background: #20242d;
                border: 1px solid #303541;
                border-radius: 6px;
                color: #9ca3af;
                font-size: 11px;
            }
            #sectionTitle {
                color: #f9fafb;
                font-size: 15px;
                font-weight: 650;
            }
            #stateLabel {
                min-width: 110px;
                min-height: 36px;
                max-height: 36px;
                padding: 0 14px;
                background: #242833;
                border: 1px solid #343946;
                border-radius: 8px;
                color: #d1d5db;
                font-weight: 600;
            }
            #detectedLabel {
                padding: 5px 10px;
                background: #2a2022;
                border: 1px solid #5c2d35;
                border-radius: 7px;
                color: #fb7185;
                font-weight: 700;
            }
            QPushButton {
                min-height: 34px;
                max-height: 34px;
                padding: 0 14px;
                background: #242833;
                border: 1px solid #343946;
                border-radius: 8px;
                color: #e5e7eb;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #2d3240;
                border-color: #485063;
            }
            QPushButton:pressed {
                background: #1e222b;
            }
            #primaryButton {
                background: #2563eb;
                border-color: #3b82f6;
                color: white;
            }
            #primaryButton:hover {
                background: #1d4ed8;
            }
            QComboBox, QDoubleSpinBox {
                min-height: 34px;
                padding: 0 9px;
                background: #0f1117;
                border: 1px solid #303541;
                border-radius: 8px;
                color: #e5e7eb;
            }
            QComboBox:hover, QDoubleSpinBox:hover {
                border-color: #4b5563;
            }
            QComboBox QAbstractItemView {
                background: #17191f;
                border: 1px solid #303541;
                selection-background-color: #2563eb;
                color: #e5e7eb;
            }
            QProgressBar {
                min-height: 23px;
                background: #0f1117;
                border: 1px solid #303541;
                border-radius: 8px;
                text-align: center;
                color: #f9fafb;
                font-weight: 700;
            }
            QProgressBar::chunk {
                background: #3b82f6;
                border-radius: 7px;
            }
            QTableWidget {
                background: #0f1117;
                alternate-background-color: #14171d;
                border: 1px solid #292d36;
                border-radius: 8px;
                gridline-color: #252933;
                color: #e5e7eb;
                selection-background-color: #1d4ed8;
            }
            QHeaderView::section {
                background: #20232b;
                color: #cbd5e1;
                border: none;
                border-right: 1px solid #303541;
                border-bottom: 1px solid #303541;
                padding: 8px;
                font-weight: 650;
            }
            QScrollBar:vertical {
                width: 11px;
                background: #0f1117;
            }
            QScrollBar::handle:vertical {
                min-height: 25px;
                background: #343946;
                border-radius: 5px;
            }
            """
        )

    def connect_controls(self):
        self.play_button.clicked.connect(self.start_listening)
        self.pause_button.clicked.connect(self.worker.pause)
        self.capture_button.clicked.connect(self.capture_data)
        self.clear_button.clicked.connect(self.clear_captures)
        self.device_combo.currentIndexChanged.connect(
            self.device_changed
        )
        self.history_duration_spin.valueChanged.connect(
            self.history_duration_changed
        )

        controls = (
            self.calibration_spin,
            self.confidence_spin,
            self.level_spin,
            self.volume_spin,
            self.spectral_spin,
        )

        for control in controls:
            control.valueChanged.connect(self.apply_settings)

    def set_devices(self, devices, default_index):
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        selected_combo_index = 0

        for combo_index, device in enumerate(devices):
            name = (
                f'{device["name"]} '
                f'[{device["index"]}] '
                f'{device["sample_rate"]} Hz'
            )
            self.device_combo.addItem(name, device["index"])

            if device["index"] == default_index:
                selected_combo_index = combo_index

        if self.device_combo.count() > 0:
            self.device_combo.setCurrentIndex(selected_combo_index)
            self.worker.set_device(
                self.device_combo.currentData()
            )

        self.device_combo.blockSignals(False)

    def device_changed(self):
        self.worker.set_device(self.device_combo.currentData())

    def history_duration_changed(self):
        duration = self.history_duration_spin.value()
        self.range_period_label.setText(
            f"Min / Max: last {duration:.1f} seconds"
        )
        self.trim_history()
        self.update_ranges()

    def apply_settings(self):
        self.worker.update_settings(
            self.calibration_spin.value(),
            self.confidence_spin.value(),
            self.level_spin.value(),
            self.volume_spin.value(),
            self.spectral_spin.value(),
        )

    def start_listening(self):
        if self.device_combo.count() == 0:
            self.show_error("No loopback audio device is available.")
            return

        self.worker.set_device(self.device_combo.currentData())
        self.apply_settings()
        self.worker.start()

    def update_state(self, state):
        self.state_label.setText(state)

        common_style = (
            "min-width:110px;min-height:36px;max-height:36px;"
            "border-radius:8px;padding:0 14px;font-weight:600;"
        )

        if state == "Listening":
            self.state_label.setStyleSheet(
                common_style
                + "background:#163326;border:1px solid #236644;"
                + "color:#4ade80;"
            )
        elif state == "Paused":
            self.state_label.setStyleSheet(
                common_style
                + "background:#382d16;border:1px solid #705b20;"
                + "color:#facc15;"
            )
        elif state == "Error":
            self.state_label.setStyleSheet(
                common_style
                + "background:#3b1d22;border:1px solid #7f2935;"
                + "color:#fb7185;"
            )
        else:
            self.state_label.setStyleSheet(
                common_style
                + "background:#242833;border:1px solid #343946;"
                + "color:#d1d5db;"
            )

    def trim_history(self):
        cutoff = time.monotonic() - self.history_duration_spin.value()

        while (
            self.history
            and float(self.history[0].get("timestamp", 0.0)) < cutoff
        ):
            self.history.popleft()

    def format_metric(self, key, value):
        if key == "confidence":
            return f"{float(value):.2f}%"
        if key in ("rms", "peak", "baseline_rms"):
            return f"{float(value):.6f}"
        if key == "level_dbfs":
            return f"{float(value):.2f} dBFS"
        if key == "volume_increase_db":
            return f"{float(value):.2f} dB"
        if key == "spectral_change":
            return f"{float(value):.2f}%"
        if key == "dominant_frequency":
            return f"{float(value):.2f} Hz"
        return str(value)

    def update_ranges(self):
        range_keys = (
            "confidence",
            "rms",
            "peak",
            "level_dbfs",
            "volume_increase_db",
            "spectral_change",
            "dominant_frequency",
            "baseline_rms",
        )

        if not self.history:
            for key in range_keys:
                self.cards[key].clear_range()
            return

        for key in range_keys:
            values = [
                float(item[key])
                for item in self.history
                if key in item
            ]

            if values:
                self.cards[key].set_range(
                    self.format_metric(key, min(values)),
                    self.format_metric(key, max(values)),
                )
            else:
                self.cards[key].clear_range()

    def update_data(self, data):
        self.latest_data = dict(data)
        self.history.append(dict(data))
        self.trim_history()

        confidence = float(data.get("confidence", 0))
        detected = bool(data.get("detected", False))

        self.confidence_bar.setValue(
            int(max(0.0, min(100.0, confidence)) * 10)
        )
        self.confidence_bar.setFormat(f"{confidence:.1f}%")

        self.cards["confidence"].set_value(
            f"{confidence:.2f}%"
        )
        self.cards["rms"].set_value(
            f'{float(data.get("rms", 0)):.6f}'
        )
        self.cards["peak"].set_value(
            f'{float(data.get("peak", 0)):.6f}'
        )
        self.cards["level_dbfs"].set_value(
            f'{float(data.get("level_dbfs", -200)):.2f} dBFS'
        )
        self.cards["volume_increase_db"].set_value(
            f'{float(data.get("volume_increase_db", 0)):.2f} dB'
        )
        self.cards["spectral_change"].set_value(
            f'{float(data.get("spectral_change", 0)):.2f}%'
        )
        self.cards["dominant_frequency"].set_value(
            f'{float(data.get("dominant_frequency", 0)):.2f} Hz'
        )
        self.cards["baseline_rms"].set_value(
            f'{float(data.get("baseline_rms", 0)):.6f}'
        )
        self.cards["elapsed"].set_value(
            f'{float(data.get("elapsed", 0)):.2f} sec'
        )
        self.cards["sample_rate"].set_value(
            f'{int(data.get("sample_rate", 0))} Hz'
        )
        self.cards["channels"].set_value(
            str(int(data.get("channels", 0)))
        )
        self.cards["frames"].set_value(
            str(int(data.get("frames", 0)))
        )

        self.update_ranges()

        if detected:
            self.detected_label.setText("AUDIO EVENT DETECTED")
            self.detected_label.setStyleSheet(
                "padding:5px 10px;background:#163326;"
                "border:1px solid #236644;border-radius:7px;"
                "color:#4ade80;font-weight:700;"
            )
        else:
            self.detected_label.setText("NO AUDIO EVENT")
            self.detected_label.setStyleSheet(
                "padding:5px 10px;background:#2a2022;"
                "border:1px solid #5c2d35;border-radius:7px;"
                "color:#fb7185;font-weight:700;"
            )

    def capture_data(self):
        if self.latest_data is None:
            self.show_error(
                "Start listening and wait for audio data before capturing."
            )
            return

        data = self.latest_data
        row = self.capture_table.rowCount()
        self.capture_table.insertRow(row)

        values = [
            time.strftime("%H:%M:%S"),
            "Yes" if data.get("detected") else "No",
            f'{float(data.get("confidence", 0)):.2f}%',
            f'{float(data.get("rms", 0)):.6f}',
            f'{float(data.get("peak", 0)):.6f}',
            f'{float(data.get("level_dbfs", -200)):.2f} dBFS',
            f'{float(data.get("volume_increase_db", 0)):.2f} dB',
            f'{float(data.get("spectral_change", 0)):.2f}%',
            f'{float(data.get("dominant_frequency", 0)):.2f}',
        ]

        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if column == 1:
                item.setForeground(
                    QColor("#4ade80")
                    if data.get("detected")
                    else QColor("#fb7185")
                )

            self.capture_table.setItem(row, column, item)

        self.capture_table.scrollToBottom()

    def clear_captures(self):
        self.capture_table.setRowCount(0)

    def show_error(self, message):
        QMessageBox.critical(
            self,
            "Audio Monitor Error",
            str(message),
        )

    def closeEvent(self, event):
        self.worker.stop()

        if (
            self.worker.thread is not None
            and self.worker.thread.is_alive()
        ):
            self.worker.thread.join(timeout=1.5)

        event.accept()


def main():
    application = QApplication(sys.argv)
    application.setApplicationName("PC Audio Data Monitor")
    application.setFont(QFont("Segoe UI", 10))

    window = AudioMonitorWindow()
    window.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()
