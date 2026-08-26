import base64
import json
import tempfile
import time
from pathlib import Path

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


AudioCategory = MacroCommandCategory("audio", "Audio", "mc:e050")


def empty_audio():
    return {
        "audio_base64": "",
        "duration": 0.0,
        "file_name": "",
        "sample_rate": 44100,
        "channels": 2,
        "format": "wav",
    }


def normalize_audio_value(value):
    if isinstance(value, dict):
        audio_base64 = str(value.get("audio_base64", "") or "")
        file_name = str(value.get("file_name", "") or "")
        audio_format = str(value.get("format", "wav") or "wav")
        file_path = str(value.get("file_path", "") or "")

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

        result = {
            "audio_base64": audio_base64,
            "duration": duration,
            "file_name": file_name,
            "sample_rate": sample_rate,
            "channels": channels,
            "format": audio_format,
        }

        if file_path:
            result["file_path"] = file_path

        return result

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return empty_audio()

        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return normalize_audio_value(parsed)
        except Exception:
            pass

        path = Path(value)
        if path.is_file():
            return {
                "audio_base64": "",
                "duration": 0.0,
                "file_name": path.name,
                "sample_rate": 44100,
                "channels": 2,
                "format": path.suffix.strip(".").lower() or "wav",
                "file_path": str(path),
            }

        return {
            "audio_base64": value,
            "duration": 0.0,
            "file_name": "",
            "sample_rate": 44100,
            "channels": 2,
            "format": "wav",
        }

    return empty_audio()


def base64_to_bytes(value):
    value = str(value or "").strip()
    if not value:
        return b""

    try:
        return base64.b64decode(value)
    except Exception:
        return b""


def audio_value_to_file(value):
    audio = normalize_audio_value(value)

    if audio.get("file_path"):
        return audio.get("file_path")

    raw = base64_to_bytes(audio.get("audio_base64"))
    if not raw:
        raise ValueError("Audio is required.")

    suffix = "." + str(audio.get("format", "wav") or "wav").strip(".")
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(raw)
    temp_file.flush()
    temp_file.close()
    return temp_file.name


def normalize_float(value, default_value=0.0, min_value=None, max_value=None):
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = default_value

    if min_value is not None and result < min_value:
        result = min_value
    if max_value is not None and result > max_value:
        result = max_value

    return result


def normalize_int(value, default_value=0, min_value=None, max_value=None):
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default_value

    if min_value is not None and result < min_value:
        result = min_value
    if max_value is not None and result > max_value:
        result = max_value

    return result


def normalize_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ["1", "true", "yes", "on"]


def is_runtime_stopped(runtime):
    return bool(runtime is not None and getattr(runtime, "stopped", False))


def sleep_runtime(runtime, seconds):
    if runtime is not None and hasattr(runtime, "sleep"):
        runtime.sleep(seconds)
    else:
        time.sleep(seconds)


def play_audio_file(file_path, volume=1.0, loops=0, wait_until_finished=False, runtime=None):
    try:
        import pygame
    except ImportError:
        raise RuntimeError("pygame is required. Install it using pip install pygame")

    path = str(file_path or "").strip()
    if not path:
        raise ValueError("Audio file path is required.")

    volume = normalize_float(volume, 1.0, 0.0, 1.0)
    loops = normalize_int(loops, 0, -1, None)
    wait_until_finished = normalize_bool(wait_until_finished)

    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(loops=loops)

    if wait_until_finished:
        while pygame.mixer.music.get_busy():
            if is_runtime_stopped(runtime):
                pygame.mixer.music.stop()
                return {
                    "success": False,
                    "stopped": True,
                    "file_path": path,
                    "volume": volume,
                    "loops": loops,
                    "playing": False,
                }

            sleep_runtime(runtime, 0.05)

    return {
        "success": True,
        "file_path": path,
        "volume": volume,
        "loops": loops,
        "playing": pygame.mixer.music.get_busy(),
    }


class PlayAudioCommand(MacroCommand):
    id = "audio.play"
    title = "Play Audio"
    category = AudioCategory
    icon = "mc:e405"
    description = "Play selected audio."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "file_path",
            "title": "Audio",
            "value_type": "audio",
            "default_value": empty_audio(),
        },
        {
            "name": "volume",
            "title": "Volume",
            "value_type": "float",
            "min_value": 0.0,
            "max_value": 1.0,
            "default_value": 1.0,
        },
        {
            "name": "loops",
            "title": "Loops",
            "value_type": "integer",
            "min_value": -1,
            "default_value": 0,
        },
        {
            "name": "wait_until_finished",
            "title": "Wait Until Finished",
            "value_type": "boolean",
            "default_value": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        audio = normalize_audio_value(values.get("file_path"))
        audio_name = audio.get("file_name") or "audio"
        return f"play audio {audio_name}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        return play_audio_file(
            file_path=audio_value_to_file(values.get("file_path")),
            volume=values.get("volume"),
            loops=values.get("loops"),
            wait_until_finished=values.get("wait_until_finished"),
            runtime=runtime,
        )


def register_macro(registry):
    registry.register(PlayAudioCommand)
