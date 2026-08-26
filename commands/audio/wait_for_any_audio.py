import math
import sys
import time
from functools import lru_cache

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


AudioCategory = MacroCommandCategory("audio", "Audio", "mc:e050")


def save_result_to_variable(runtime, variable_name, value):
    variable_name = str(variable_name or "").strip()
    if not variable_name or runtime is None or not hasattr(runtime, "vars"):
        return value
    runtime.vars.set(variable_name, value)
    return value


def normalize_float(value, default_value, minimum, maximum):
    try:
        normalized = float(value)
    except Exception:
        normalized = default_value
    return max(minimum, min(maximum, normalized))


def normalize_integer(value, default_value, minimum, maximum):
    try:
        normalized = int(value)
    except Exception:
        normalized = default_value
    return max(minimum, min(maximum, normalized))


def normalize_device_index(value):
    text = str(value or "").strip()
    if not text:
        return None

    try:
        index = int(text)
    except Exception:
        return None

    if index < 0:
        return None

    return index


@lru_cache(maxsize=8)
def get_analysis_data(sample_rate, chunk_size):
    try:
        import numpy as np
    except Exception:
        raise RuntimeError(
            "NumPy is required for audio detection. "
            "Install it with: pip install numpy"
        )

    window = np.hanning(chunk_size).astype(np.float32)
    frequencies = np.fft.rfftfreq(
        chunk_size,
        1.0 / sample_rate,
    ).astype(np.float32)

    return window, frequencies


def get_device_info(audio, device_index):
    if device_index is None:
        return None

    try:
        device_count = audio.get_device_count()
    except Exception:
        return None

    if device_index < 0 or device_index >= device_count:
        return None

    try:
        return audio.get_device_info_by_index(device_index)
    except Exception:
        return None


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
        devices.extend(
            list(
                audio.get_loopback_device_info_generator()
            )
        )
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
            device = audio.get_device_info_by_index(
                device_index
            )
        except Exception:
            continue

        if bool(device.get("isLoopbackDevice", False)):
            devices.append(device)

    return devices


def find_matching_loopback_device(
    output_device,
    loopback_devices,
):
    if not output_device:
        return None

    output_name = str(
        output_device.get("name", "") or ""
    ).casefold()
    output_key = device_name_key(output_name)

    best_device = None
    best_score = -1

    for device in loopback_devices:
        input_channels = int(
            device.get("maxInputChannels", 0) or 0
        )
        if input_channels <= 0:
            continue

        loopback_name = str(
            device.get("name", "") or ""
        ).casefold()
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
        score += len(
            output_words.intersection(loopback_words)
        ) * 10

        output_host_api = output_device.get("hostApi")
        loopback_host_api = device.get("hostApi")

        if output_host_api == loopback_host_api:
            score += 5

        if score > best_score:
            best_score = score
            best_device = device

    return best_device


def get_default_output_device(audio, pyaudio):
    try:
        wasapi_info = audio.get_host_api_info_by_type(
            pyaudio.paWASAPI
        )
        output_index = int(
            wasapi_info.get("defaultOutputDevice", -1)
        )

        if output_index >= 0:
            device = get_device_info(
                audio,
                output_index,
            )
            if device is not None:
                return device
    except Exception:
        pass

    try:
        return audio.get_default_output_device_info()
    except Exception:
        return None


def select_pc_audio_device(
    audio,
    pyaudio,
    requested_device_index,
):
    loopback_devices = get_loopback_devices(audio)

    requested_device = get_device_info(
        audio,
        requested_device_index,
    )

    if requested_device is not None:
        if (
            bool(
                requested_device.get(
                    "isLoopbackDevice",
                    False,
                )
            )
            and int(
                requested_device.get(
                    "maxInputChannels",
                    0,
                )
                or 0
            )
            > 0
        ):
            return requested_device

        matching_device = find_matching_loopback_device(
            requested_device,
            loopback_devices,
        )

        if matching_device is not None:
            return matching_device

    try:
        default_loopback = (
            audio.get_default_wasapi_loopback()
        )

        if (
            default_loopback
            and int(
                default_loopback.get(
                    "maxInputChannels",
                    0,
                )
                or 0
            )
            > 0
        ):
            return default_loopback
    except Exception:
        pass

    default_output = get_default_output_device(
        audio,
        pyaudio,
    )
    matching_device = find_matching_loopback_device(
        default_output,
        loopback_devices,
    )

    if matching_device is not None:
        return matching_device

    if loopback_devices:
        for device in loopback_devices:
            if (
                int(
                    device.get(
                        "maxInputChannels",
                        0,
                    )
                    or 0
                )
                > 0
            ):
                return device

    raise RuntimeError(
        "The default PC audio loopback device could not "
        "be detected. Make sure an output device is "
        "enabled and install PyAudioWPatch."
    )


def get_stream_settings(device):
    sample_rate = int(
        round(
            float(
                device.get(
                    "defaultSampleRate",
                    48000,
                )
                or 48000
            )
        )
    )
    maximum_channels = int(
        device.get("maxInputChannels", 0) or 0
    )

    if maximum_channels <= 0:
        raise RuntimeError(
            f'The selected audio device '
            f'"{device.get("name", "Unknown")}" '
            "does not support loopback input."
        )

    channels = min(maximum_channels, 2)
    return sample_rate, channels


def read_audio_frame(stream, chunk_size, channels):
    import numpy as np

    frame_data = stream.read(
        chunk_size,
        exception_on_overflow=False,
    )
    samples = np.frombuffer(
        frame_data,
        dtype=np.int16,
    )

    if channels > 1:
        usable_sample_count = (
            samples.size // channels
        ) * channels
        samples = samples[:usable_sample_count]

        if samples.size == 0:
            return np.zeros(
                chunk_size,
                dtype=np.float32,
            )

        samples = samples.reshape(-1, channels)
        samples = np.mean(samples, axis=1)

    samples = samples.astype(
        np.float32,
        copy=False,
    )

    if samples.size < chunk_size:
        samples = np.pad(
            samples,
            (0, chunk_size - samples.size),
        )
    elif samples.size > chunk_size:
        samples = samples[:chunk_size]

    return samples


def is_runtime_stopped(runtime):
    return runtime is not None and bool(
        getattr(runtime, "stopped", False)
    )


def create_result(
    detected,
    stopped,
    confidence,
    rms,
    peak,
    level_dbfs,
    volume_increase_db,
    spectral_change,
    dominant_frequency,
    stable_frames,
    elapsed,
    device,
    sample_rate,
    channels,
):
    return {
        "detected": bool(detected),
        "stopped": bool(stopped),
        "confidence": round(float(confidence), 2),
        "rms": round(float(rms), 6),
        "peak": round(float(peak), 6),
        "level_dbfs": round(float(level_dbfs), 2),
        "volume_increase_db": round(
            float(volume_increase_db),
            2,
        ),
        "spectral_change": round(
            float(spectral_change),
            2,
        ),
        "dominant_frequency": (
            round(float(dominant_frequency), 2)
            if dominant_frequency is not None
            else None
        ),
        "stable_frames": int(stable_frames),
        "elapsed": round(float(elapsed), 3),
        "device_index": int(device["index"]),
        "device_name": str(device.get("name", "")),
        "sample_rate": int(sample_rate),
        "channels": int(channels),
    }


def analyze_audio_frame(
    samples,
    window,
    frequencies,
    baseline_rms,
    baseline_spectrum,
    minimum_level_dbfs,
    minimum_volume_increase,
    minimum_spectral_change,
):
    import numpy as np

    normalized_samples = (
        samples.astype(
            np.float32,
            copy=False,
        )
        / 32768.0
    )
    normalized_samples -= float(
        np.mean(normalized_samples)
    )

    rms = float(
        np.sqrt(
            np.mean(
                normalized_samples
                * normalized_samples
            )
            + 1e-20
        )
    )
    peak = float(
        np.max(
            np.abs(normalized_samples)
        )
    )

    level_dbfs = 20.0 * math.log10(
        max(rms, 1e-10)
    )
    volume_increase_db = 20.0 * math.log10(
        max(
            rms / max(baseline_rms, 1e-10),
            1e-10,
        )
    )

    spectrum = np.abs(
        np.fft.rfft(
            normalized_samples * window
        )
    ) ** 2
    spectrum = np.maximum(
        spectrum,
        1e-20,
    )

    current_total = float(
        np.sum(spectrum)
    )
    baseline_total = float(
        np.sum(baseline_spectrum)
    )

    if current_total > 1e-20:
        normalized_spectrum = (
            spectrum / current_total
        )
    else:
        normalized_spectrum = spectrum

    if baseline_total > 1e-20:
        normalized_baseline = (
            baseline_spectrum / baseline_total
        )
    else:
        normalized_baseline = baseline_spectrum

    current_norm = float(
        np.linalg.norm(normalized_spectrum)
    )
    baseline_norm = float(
        np.linalg.norm(normalized_baseline)
    )

    if (
        current_norm > 1e-20
        and baseline_norm > 1e-20
    ):
        similarity = float(
            np.dot(
                normalized_spectrum,
                normalized_baseline,
            )
            / (
                current_norm
                * baseline_norm
            )
        )
        similarity = max(
            0.0,
            min(1.0, similarity),
        )
        spectral_change = (
            1.0 - similarity
        ) * 100.0
    else:
        spectral_change = 0.0

    minimum_bin = int(
        np.searchsorted(
            frequencies,
            20.0,
        )
    )

    if (
        spectrum.size > minimum_bin
        and current_total > 1e-20
    ):
        dominant_index = (
            minimum_bin
            + int(
                np.argmax(
                    spectrum[minimum_bin:]
                )
            )
        )
        dominant_frequency = float(
            frequencies[dominant_index]
        )
    else:
        dominant_frequency = None

    volume_score = 50.0 + (
        volume_increase_db
        - minimum_volume_increase
    ) * 5.0
    spectral_score = 50.0 + (
        spectral_change
        - minimum_spectral_change
    ) * 2.5
    level_score = 50.0 + (
        level_dbfs
        - minimum_level_dbfs
    ) * 2.0

    volume_score = max(
        0.0,
        min(100.0, volume_score),
    )
    spectral_score = max(
        0.0,
        min(100.0, spectral_score),
    )
    level_score = max(
        0.0,
        min(100.0, level_score),
    )

    volume_confidence = (
        volume_score * 0.75
        + level_score * 0.25
    )
    spectral_confidence = (
        spectral_score * 0.65
        + level_score * 0.35
    )
    confidence = max(
        volume_confidence,
        spectral_confidence,
    )

    level_matched = (
        level_dbfs >= minimum_level_dbfs
    )
    volume_matched = (
        volume_increase_db
        >= minimum_volume_increase
    )
    spectrum_matched = (
        spectral_change
        >= minimum_spectral_change
    )
    event_matched = (
        level_matched
        and (
            volume_matched
            or spectrum_matched
        )
    )

    return {
        "confidence": confidence,
        "rms": rms,
        "peak": peak,
        "level_dbfs": level_dbfs,
        "volume_increase_db": volume_increase_db,
        "spectral_change": spectral_change,
        "dominant_frequency": dominant_frequency,
        "event_matched": event_matched,
        "spectrum": spectrum,
    }


def wait_for_any_audio(
    timeout,
    calibration_duration,
    minimum_confidence,
    minimum_level_dbfs,
    minimum_volume_increase,
    minimum_spectral_change,
    stable_frames,
    device_index,
    runtime,
):
    try:
        import numpy as np
    except Exception:
        raise RuntimeError(
            "NumPy is required for audio detection. "
            "Install it with: pip install numpy"
        )

    try:
        import pyaudiowpatch as pyaudio
    except Exception:
        raise RuntimeError(
            "PyAudioWPatch is required to capture "
            "the main PC audio output. Install it with: "
            "pip install PyAudioWPatch"
        )

    chunk_size = 2048
    audio = pyaudio.PyAudio()
    stream = None

    try:
        device = select_pc_audio_device(
            audio,
            pyaudio,
            device_index,
        )
        sample_rate, channels = get_stream_settings(
            device
        )
        window, frequencies = get_analysis_data(
            sample_rate,
            chunk_size,
        )

        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=int(
                    device["index"]
                ),
                frames_per_buffer=chunk_size,
            )
        except Exception as error:
            raise RuntimeError(
                "Could not open the automatically "
                "detected PC audio device "
                f'"{device.get("name", "Unknown")}" '
                f"at {sample_rate} Hz with "
                f"{channels} channel(s): {error}"
            )

        calibration_frame_count = max(
            1,
            int(
                math.ceil(
                    calibration_duration
                    * sample_rate
                    / chunk_size
                )
            ),
        )
        calibration_rms_values = []
        calibration_spectra = []
        calibration_started_at = time.monotonic()

        for _ in range(calibration_frame_count):
            if is_runtime_stopped(runtime):
                return create_result(
                    False,
                    True,
                    0,
                    0,
                    0,
                    -200,
                    0,
                    0,
                    None,
                    0,
                    time.monotonic()
                    - calibration_started_at,
                    device,
                    sample_rate,
                    channels,
                )

            samples = read_audio_frame(
                stream,
                chunk_size,
                channels,
            )
            normalized_samples = (
                samples.astype(
                    np.float32,
                    copy=False,
                )
                / 32768.0
            )
            normalized_samples -= float(
                np.mean(normalized_samples)
            )

            rms = float(
                np.sqrt(
                    np.mean(
                        normalized_samples
                        * normalized_samples
                    )
                    + 1e-20
                )
            )
            spectrum = np.abs(
                np.fft.rfft(
                    normalized_samples * window
                )
            ) ** 2

            calibration_rms_values.append(rms)
            calibration_spectra.append(spectrum)

        baseline_rms = max(
            float(
                np.percentile(
                    calibration_rms_values,
                    70,
                )
            ),
            1e-10,
        )
        baseline_spectrum = np.maximum(
            np.percentile(
                np.stack(calibration_spectra),
                70,
                axis=0,
            ),
            1e-20,
        )

        started_at = time.monotonic()
        consecutive_matches = 0
        best_analysis = None

        while (
            time.monotonic() - started_at
            < timeout
        ):
            if is_runtime_stopped(runtime):
                analysis = best_analysis or {
                    "confidence": 0,
                    "rms": 0,
                    "peak": 0,
                    "level_dbfs": -200,
                    "volume_increase_db": 0,
                    "spectral_change": 0,
                    "dominant_frequency": None,
                }

                return create_result(
                    False,
                    True,
                    analysis["confidence"],
                    analysis["rms"],
                    analysis["peak"],
                    analysis["level_dbfs"],
                    analysis[
                        "volume_increase_db"
                    ],
                    analysis[
                        "spectral_change"
                    ],
                    analysis[
                        "dominant_frequency"
                    ],
                    consecutive_matches,
                    time.monotonic()
                    - started_at,
                    device,
                    sample_rate,
                    channels,
                )

            samples = read_audio_frame(
                stream,
                chunk_size,
                channels,
            )
            analysis = analyze_audio_frame(
                samples,
                window,
                frequencies,
                baseline_rms,
                baseline_spectrum,
                minimum_level_dbfs,
                minimum_volume_increase,
                minimum_spectral_change,
            )

            if (
                best_analysis is None
                or analysis["confidence"]
                > best_analysis["confidence"]
            ):
                best_analysis = analysis

            matched = (
                analysis["event_matched"]
                and analysis["confidence"]
                >= minimum_confidence
            )

            if matched:
                consecutive_matches += 1
            else:
                consecutive_matches = 0
                baseline_rms = (
                    baseline_rms * 0.995
                    + analysis["rms"] * 0.005
                )
                baseline_spectrum = (
                    baseline_spectrum * 0.995
                    + analysis["spectrum"] * 0.005
                )

            if consecutive_matches >= stable_frames:
                return create_result(
                    True,
                    False,
                    analysis["confidence"],
                    analysis["rms"],
                    analysis["peak"],
                    analysis["level_dbfs"],
                    analysis[
                        "volume_increase_db"
                    ],
                    analysis[
                        "spectral_change"
                    ],
                    analysis[
                        "dominant_frequency"
                    ],
                    consecutive_matches,
                    time.monotonic()
                    - started_at,
                    device,
                    sample_rate,
                    channels,
                )

        analysis = best_analysis or {
            "confidence": 0,
            "rms": 0,
            "peak": 0,
            "level_dbfs": -200,
            "volume_increase_db": 0,
            "spectral_change": 0,
            "dominant_frequency": None,
        }

        return create_result(
            False,
            False,
            analysis["confidence"],
            analysis["rms"],
            analysis["peak"],
            analysis["level_dbfs"],
            analysis["volume_increase_db"],
            analysis["spectral_change"],
            analysis["dominant_frequency"],
            0,
            time.monotonic() - started_at,
            device,
            sample_rate,
            channels,
        )
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

        audio.terminate()


class WaitForAnyAudioCommand(MacroCommand):
    id = "audio.wait_for_any_audio"
    title = "Wait For Any Audio"
    category = AudioCategory
    icon = "mc:e1b8"
    description = (
        "Wait for a new sound or audio change "
        "from the main PC output."
    )
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "timeout",
            "title": "Timeout",
            "place_holder": "20 seconds",
            "value_type": "float",
            "default_value": 20,
            "min_value": 0.5,
            "max_value": 3600,
            "decimals": 1,
        },
        {
            "name": "calibration_duration",
            "title": "Background Calibration",
            "place_holder": "1 seconds",
            "value_type": "float",
            "default_value": 1,
            "min_value": 0.2,
            "max_value": 30,
            "decimals": 1,
        },
        {
            "name": "minimum_confidence",
            "title": "Minimum Confidence",
            "place_holder": "70%",
            "value_type": "float",
            "default_value": 70,
            "min_value": 0,
            "max_value": 100,
            "decimals": 1,
        },
        {
            "name": "minimum_level_dbfs",
            "title": "Minimum Audio Level",
            "place_holder": "-20 dBFS",
            "value_type": "float",
            "default_value": -20,
            "min_value": -100,
            "max_value": 0,
            "decimals": 1,
        },
        {
            "name": "minimum_volume_increase",
            "title": "Minimum Volume Increase",
            "place_holder": "10 dB",
            "value_type": "float",
            "default_value": 10,
            "min_value": -sys.float_info.max,
            "max_value": sys.float_info.max,
            "decimals": 1,
        },
        {
            "name": "minimum_spectral_change",
            "title": "Minimum Frequency Change",
            "place_holder": "50%",
            "value_type": "float",
            "default_value": 50,
            "min_value": 0,
            "max_value": 100,
            "decimals": 1,
        },
        {
            "name": "stable_frames",
            "title": "Required Stable Frames",
            "place_holder": "3",
            "value_type": "int",
            "default_value": 3,
            "min_value": 1,
            "max_value": 30,
        },
        {
            "name": "device_index",
            "title": "PC Audio Device Override",
            "place_holder": (
                "Empty = detect main PC audio"
            ),
            "value_type": "text",
            "default_value": "",
            "required": False,
        },
        {
            "name": "save_to_variable",
            "title": "Save Confidence To Variable",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        minimum_confidence = normalize_float(
            values.get(
                "minimum_confidence",
                50,
            ),
            50,
            0,
            100,
        )
        return (
            "wait for any PC audio: "
            f"{minimum_confidence:g}% confidence"
        )

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)

        timeout = normalize_float(
            values.get("timeout", 10),
            10,
            0.5,
            3600,
        )
        calibration_duration = normalize_float(
            values.get(
                "calibration_duration",
                1,
            ),
            1,
            0.2,
            10,
        )
        minimum_confidence = normalize_float(
            values.get(
                "minimum_confidence",
                50,
            ),
            50,
            0,
            100,
        )
        minimum_level_dbfs = normalize_float(
            values.get(
                "minimum_level_dbfs",
                -55,
            ),
            -55,
            -100,
            0,
        )
        minimum_volume_increase = normalize_float(
            values.get(
                "minimum_volume_increase",
                8,
            ),
            8,
            -sys.float_info.max,
            sys.float_info.max,
        )
        minimum_spectral_change = normalize_float(
            values.get(
                "minimum_spectral_change",
                15,
            ),
            15,
            0,
            100,
        )
        stable_frames = normalize_integer(
            values.get("stable_frames", 2),
            2,
            1,
            30,
        )
        device_index = normalize_device_index(
            values.get("device_index")
        )

        result = wait_for_any_audio(
            timeout,
            calibration_duration,
            minimum_confidence,
            minimum_level_dbfs,
            minimum_volume_increase,
            minimum_spectral_change,
            stable_frames,
            device_index,
            runtime,
        )

        confidence = (
            result.get("confidence", 0)
            if result.get("detected")
            else 0
        )

        save_result_to_variable(
            runtime,
            values.get("save_to_variable"),
            confidence,
        )

        return result


def register_macro(registry):
    registry.register(WaitForAnyAudioCommand)
