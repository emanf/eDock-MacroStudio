import base64
import hashlib
import json
import threading
import time
from collections import OrderedDict
from io import BytesIO
from pathlib import Path

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


AudioCategory = MacroCommandCategory("audio", "Audio", "mc:e050")

_AUDIO_CACHE = OrderedDict()
_TARGET_CACHE = OrderedDict()
_WINDOW_CACHE = OrderedDict()
_MEL_FILTER_CACHE = OrderedDict()
_DCT_CACHE = OrderedDict()
_CHROMA_CACHE = OrderedDict()
_CACHE_LOCK = threading.RLock()
_LOOPBACK_MICROPHONE = None
_MAX_AUDIO_CACHE_SIZE = 12
_MAX_TARGET_CACHE_SIZE = 12
_MAX_FEATURE_CACHE_SIZE = 24


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
        return base64.b64decode(value, validate=False)
    except Exception:
        return b""


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


def normalize_detection_formula(value):
    value = str(value or "hybrid").strip().lower()

    aliases = {
        "lite": "waveform",
        "full": "hybrid",
        "fast": "waveform",
        "exact": "waveform",
        "tone": "spectral",
        "best": "hybrid",
        "spectrum": "spectral",
        "mel": "mel_spectrogram",
        "mel spectrogram": "mel_spectrogram",
        "mel-spectrogram": "mel_spectrogram",
        "mel_spectrum": "mel_spectrogram",
        "mfcc_match": "mfcc",
        "chroma_match": "chroma",
        "spectrogram_match": "spectrogram",
    }

    value = aliases.get(value, value)

    if value not in (
        "spectral",
        "fingerprint",
        "spectrogram",
        "mel_spectrogram",
        "mfcc",
        "chroma",
        "waveform",
        "hybrid",
    ):
        return "hybrid"

    return value


def is_runtime_stopped(runtime):
    return bool(runtime is not None and getattr(runtime, "stopped", False))


def sleep_runtime(runtime, seconds):
    if runtime is not None and hasattr(runtime, "sleep"):
        runtime.sleep(seconds)
    else:
        time.sleep(seconds)


def save_result_to_variable(runtime, variable_name, result):
    variable_name = str(variable_name or "").strip()
    if not variable_name or runtime is None:
        return

    runtime_vars = getattr(runtime, "vars", None)
    if runtime_vars is not None and hasattr(runtime_vars, "set"):
        runtime_vars.set(variable_name, result)


def cache_get(cache, key):
    with _CACHE_LOCK:
        value = cache.get(key)
        if value is not None:
            cache.move_to_end(key)
        return value


def cache_set(cache, key, value, maximum_size):
    with _CACHE_LOCK:
        cache[key] = value
        cache.move_to_end(key)

        while len(cache) > maximum_size:
            cache.popitem(last=False)

    return value


def audio_value_cache_key(audio, sample_rate):
    sample_rate = int(sample_rate)
    file_path = str(audio.get("file_path", "") or "").strip()

    if file_path:
        path = Path(file_path)

        try:
            resolved_path = str(path.resolve())
            stat = path.stat()
            return (
                "file",
                resolved_path,
                int(stat.st_mtime_ns),
                int(stat.st_size),
                sample_rate,
            )
        except Exception:
            return ("file", str(path), sample_rate)

    encoded = str(audio.get("audio_base64", "") or "")
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    return ("base64", digest, sample_rate)


def load_audio_value(audio_value, sample_rate):
    audio = normalize_audio_value(audio_value)
    cache_key = audio_value_cache_key(audio, sample_rate)
    cached_audio = cache_get(_AUDIO_CACHE, cache_key)

    if cached_audio is not None:
        return cached_audio

    if audio.get("file_path"):
        loaded_audio = load_audio_file(audio.get("file_path"), sample_rate)
    else:
        raw = base64_to_bytes(audio.get("audio_base64"))
        if not raw:
            raise ValueError("Audio is required.")

        loaded_audio = load_audio_bytes(raw, sample_rate)

    loaded_audio.setflags(write=False)

    return cache_set(
        _AUDIO_CACHE,
        cache_key,
        loaded_audio,
        _MAX_AUDIO_CACHE_SIZE,
    )


def load_audio_file(audio_path, sample_rate):
    try:
        import numpy as np
        import soundfile as sf
    except ImportError:
        raise RuntimeError(
            "numpy and soundfile are required. Install them with: pip install numpy soundfile"
        )

    path = Path(str(audio_path or "").strip())
    if not path.is_file():
        raise ValueError("Audio file not found.")

    data, source_rate = sf.read(str(path), always_2d=True, dtype="float32")
    if data.size == 0:
        raise ValueError("Audio file is empty.")

    mono = np.mean(data, axis=1, dtype="float32")
    if int(source_rate) != int(sample_rate):
        mono = resample_audio(mono, int(source_rate), int(sample_rate))

    return remove_dc_offset(mono)


def load_audio_bytes(raw, sample_rate):
    try:
        import numpy as np
        import soundfile as sf
    except ImportError:
        raise RuntimeError(
            "numpy and soundfile are required. Install them with: pip install numpy soundfile"
        )

    data, source_rate = sf.read(
        BytesIO(raw),
        always_2d=True,
        dtype="float32",
    )
    if data.size == 0:
        raise ValueError("Audio is empty.")

    mono = np.mean(data, axis=1, dtype="float32")
    if int(source_rate) != int(sample_rate):
        mono = resample_audio(mono, int(source_rate), int(sample_rate))

    return remove_dc_offset(mono)


def remove_dc_offset(audio):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.asarray(audio, dtype="float32")
    if audio.size == 0:
        return audio

    return (audio - np.mean(audio, dtype="float64")).astype("float32")


def normalize_audio(audio):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = remove_dc_offset(audio)
    if audio.size == 0:
        return audio

    peak = float(np.max(np.abs(audio)))
    if peak <= 1e-8:
        return audio

    return (audio / peak).astype("float32")


def trim_audio_silence(audio, threshold=0.02, padding=512):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.asarray(audio, dtype="float32")
    if audio.size == 0:
        return audio

    absolute_audio = np.abs(audio)
    peak = float(np.max(absolute_audio))
    if peak <= 1e-8:
        return audio

    indexes = np.flatnonzero(absolute_audio >= peak * float(threshold))
    if indexes.size == 0:
        return audio

    start = max(0, int(indexes[0]) - int(padding))
    end = min(audio.size, int(indexes[-1]) + int(padding) + 1)

    return audio[start:end]


def audio_rms(audio):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.asarray(audio, dtype="float32")
    if audio.size == 0:
        return 0.0

    return float(np.sqrt(np.mean(np.square(audio), dtype="float64")))


def audio_peak(audio):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.asarray(audio, dtype="float32")
    if audio.size == 0:
        return 0.0

    return float(np.max(np.abs(audio)))


def audio_active_ratio(audio, threshold=0.01):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.asarray(audio, dtype="float32")
    if audio.size == 0:
        return 0.0

    return float(np.mean(np.abs(audio) >= float(threshold)))


def has_real_audio_signal(audio):
    audio = remove_dc_offset(audio)
    rms = audio_rms(audio)
    peak = audio_peak(audio)
    active = audio_active_ratio(audio, 0.004)

    return rms >= 0.0015 and peak >= 0.008 and active >= 0.004


def resize_audio(audio, target_length):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.asarray(audio, dtype="float32")
    target_length = int(target_length)

    if audio.size == 0 or target_length <= 0:
        return np.array([], dtype="float32")

    if audio.size == target_length:
        return audio.astype("float32", copy=False)

    if target_length == 1:
        return np.asarray([audio[0]], dtype="float32")

    source_positions = np.arange(audio.size, dtype="float32")
    target_positions = np.linspace(
        0,
        audio.size - 1,
        target_length,
        dtype="float32",
    )

    return np.interp(target_positions, source_positions, audio).astype("float32")


def resample_audio(audio, source_rate, target_rate):
    source_rate = int(source_rate)
    target_rate = int(target_rate)

    if source_rate == target_rate:
        return audio

    source_length = len(audio)
    target_length = max(
        1,
        int(round(source_length * target_rate / float(source_rate))),
    )

    return resize_audio(audio, target_length)


def smooth_audio_values(audio, window_size=64):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.asarray(audio, dtype="float32")
    window_size = int(window_size)

    if audio.size == 0 or window_size <= 1:
        return audio

    window_size = min(window_size, audio.size)
    cumulative = np.cumsum(
        np.insert(audio, 0, 0.0),
        dtype="float64",
    )
    smoothed = (
        cumulative[window_size:] - cumulative[:-window_size]
    ) / float(window_size)

    left_padding = window_size // 2
    right_padding = audio.size - smoothed.size - left_padding

    return np.pad(
        smoothed.astype("float32"),
        (left_padding, right_padding),
        mode="edge",
    )


def pre_emphasis(audio, coefficient=0.96):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.asarray(audio, dtype="float32")
    if audio.size <= 1:
        return audio

    emphasized = np.empty_like(audio)
    emphasized[0] = audio[0]
    emphasized[1:] = audio[1:] - float(coefficient) * audio[:-1]

    return emphasized


def prepare_audio_for_match(audio):
    audio = normalize_audio(audio)
    audio = trim_audio_silence(audio)
    audio = normalize_audio(audio)

    return audio.astype("float32", copy=False)


def extend_audio_for_loop_matching(audio, minimum_length=0):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.asarray(audio, dtype="float32")
    minimum_length = int(minimum_length or 0)

    if audio.size == 0:
        return audio

    if minimum_length <= audio.size:
        return np.concatenate((audio, audio)).astype("float32")

    repeat_count = max(
        2,
        int(np.ceil(minimum_length / float(audio.size))) + 1,
    )

    return np.tile(audio, repeat_count).astype("float32")


def downsample_pair_for_match(
    source_audio,
    target_audio,
    max_target_length=6000,
):
    source_length = int(source_audio.size)
    target_length = int(target_audio.size)

    if source_length <= 0 or target_length <= 0:
        return source_audio, target_audio

    longer_length = max(source_length, target_length)
    if longer_length <= max_target_length:
        return source_audio, target_audio

    ratio = max_target_length / float(longer_length)
    source_target_length = max(1, int(source_length * ratio))
    target_target_length = max(1, int(target_length * ratio))

    return (
        resize_audio(source_audio, source_target_length),
        resize_audio(target_audio, target_target_length),
    )


def normalized_cross_correlation(source_audio, target_audio):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    source_audio = normalize_audio(source_audio)
    target_audio = normalize_audio(target_audio)

    if source_audio.size == 0 or target_audio.size == 0:
        return np.array([], dtype="float32"), source_audio, target_audio

    if source_audio.size < target_audio.size:
        source_audio, target_audio = target_audio, source_audio

    target_length = int(target_audio.size)
    target_norm = float(np.linalg.norm(target_audio))
    if target_norm <= 1e-8:
        return np.array([], dtype="float32"), source_audio, target_audio

    correlations = np.correlate(
        source_audio,
        target_audio,
        mode="valid",
    )
    section_energy = np.convolve(
        np.square(source_audio),
        np.ones(target_length, dtype="float32"),
        mode="valid",
    )
    section_norms = np.sqrt(np.maximum(section_energy, 0.0))
    denominator = section_norms * target_norm
    valid = denominator > 1e-8

    if not np.any(valid):
        return np.array([], dtype="float32"), source_audio, target_audio

    scores = np.zeros_like(correlations, dtype="float32")
    scores[valid] = correlations[valid] / denominator[valid]
    scores = np.clip(scores, 0.0, 1.0)

    return scores.astype("float32"), source_audio, target_audio


def waveform_similarity_prepared(source_audio, target_audio):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    if source_audio.size == 0 or target_audio.size == 0:
        return 0.0

    source_audio, target_audio = downsample_pair_for_match(
        source_audio,
        target_audio,
        max_target_length=9000,
    )
    scores, _, _ = normalized_cross_correlation(
        source_audio,
        target_audio,
    )

    if scores.size == 0:
        return 0.0

    best_score = float(np.max(scores))
    best_score = max(0.0, (best_score - 0.08) / 0.92)

    return min(1.0, best_score)


def waveform_similarity(source_audio, target_audio):
    if not has_real_audio_signal(source_audio):
        return 0.0

    return waveform_similarity_prepared(
        prepare_audio_for_match(source_audio),
        prepare_audio_for_match(target_audio),
    )


def envelope_similarity_prepared(source_audio, target_audio):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    source_envelope = smooth_audio_values(np.abs(source_audio), 192)
    target_envelope = smooth_audio_values(np.abs(target_audio), 192)

    if source_envelope.size == 0 or target_envelope.size == 0:
        return 0.0

    source_envelope, target_envelope = downsample_pair_for_match(
        source_envelope,
        target_envelope,
        max_target_length=2600,
    )
    scores, _, _ = normalized_cross_correlation(
        source_envelope,
        target_envelope,
    )

    if scores.size == 0:
        return 0.0

    best_score = float(np.max(scores))
    best_score = max(0.0, (best_score - 0.24) / 0.76)

    return min(1.0, best_score)


def envelope_similarity(source_audio, target_audio):
    if not has_real_audio_signal(source_audio):
        return 0.0

    return envelope_similarity_prepared(
        prepare_audio_for_match(source_audio),
        prepare_audio_for_match(target_audio),
    )


def audio_frames(audio, frame_size=1024, hop_size=512):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    audio = np.ascontiguousarray(audio, dtype="float32")
    frame_size = int(frame_size)
    hop_size = int(hop_size)

    if audio.size == 0 or frame_size <= 0 or hop_size <= 0:
        return np.empty((0, 0), dtype="float32")

    if audio.size < frame_size:
        audio = np.pad(audio, (0, frame_size - audio.size))

    remainder = (audio.size - frame_size) % hop_size
    if remainder:
        audio = np.pad(audio, (0, hop_size - remainder))

    frame_count = 1 + (audio.size - frame_size) // hop_size
    shape = (frame_count, frame_size)
    strides = (
        audio.strides[0] * hop_size,
        audio.strides[0],
    )

    return np.lib.stride_tricks.as_strided(
        audio,
        shape=shape,
        strides=strides,
        writeable=False,
    )


def cached_hanning(frame_size):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    frame_size = int(frame_size)
    cached = cache_get(_WINDOW_CACHE, frame_size)

    if cached is not None:
        return cached

    window = np.hanning(frame_size).astype("float32")
    window.setflags(write=False)

    return cache_set(
        _WINDOW_CACHE,
        frame_size,
        window,
        _MAX_FEATURE_CACHE_SIZE,
    )


def normalize_feature_rows(features):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    features = np.asarray(features, dtype="float32")
    if features.size == 0:
        return features

    features = features - np.mean(
        features,
        axis=1,
        keepdims=True,
        dtype="float32",
    )
    norms = np.linalg.norm(features, axis=1, keepdims=True)

    return (
        features / np.maximum(norms, 1e-8)
    ).astype("float32")


def suppress_stationary_background(features, strength=0.72):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    features = np.asarray(features, dtype="float32")
    if features.size == 0 or features.shape[0] < 3:
        return features

    floor = np.percentile(
        features,
        20.0,
        axis=0,
        keepdims=True,
    )
    cleaned = np.maximum(
        features - floor * float(strength),
        0.0,
    )

    return cleaned.astype("float32")


def add_feature_deltas(features, delta_weight=0.35):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    features = np.asarray(features, dtype="float32")
    if features.size == 0:
        return features

    deltas = np.zeros_like(features)
    if features.shape[0] > 1:
        deltas[1:] = features[1:] - features[:-1]

    combined = np.concatenate(
        (features, deltas * float(delta_weight)),
        axis=1,
    )

    return normalize_feature_rows(combined)


def spectrogram_features_prepared(
    audio,
    frame_size=2048,
    hop_size=512,
    max_bins=192,
):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    emphasized = pre_emphasis(audio)
    frames = audio_frames(emphasized, frame_size, hop_size)

    if frames.size == 0:
        return np.empty((0, 0), dtype="float32")

    window = cached_hanning(frame_size)
    spectrum = np.abs(
        np.fft.rfft(frames * window, axis=1)
    ).astype("float32")
    spectrum = spectrum[
        :,
        :min(int(max_bins), spectrum.shape[1]),
    ]
    spectrum = np.log1p(spectrum)
    spectrum = suppress_stationary_background(spectrum)
    spectrum = normalize_feature_rows(spectrum)

    return add_feature_deltas(spectrum)


def spectrogram_features(
    audio,
    frame_size=2048,
    hop_size=512,
    max_bins=192,
):
    return spectrogram_features_prepared(
        prepare_audio_for_match(audio),
        frame_size,
        hop_size,
        max_bins,
    )


def resize_feature_sequence(features, target_length):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    features = np.asarray(features, dtype="float32")
    target_length = int(target_length)

    if (
        features.size == 0
        or target_length <= 0
        or features.shape[0] == target_length
    ):
        return features

    source_positions = np.arange(
        features.shape[0],
        dtype="float32",
    )
    target_positions = np.linspace(
        0,
        features.shape[0] - 1,
        target_length,
        dtype="float32",
    )
    resized = np.empty(
        (target_length, features.shape[1]),
        dtype="float32",
    )

    for feature_index in range(features.shape[1]):
        resized[:, feature_index] = np.interp(
            target_positions,
            source_positions,
            features[:, feature_index],
        )

    return normalize_feature_rows(resized)


def aligned_feature_score(source_features, target_features):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    if source_features.shape[0] < target_features.shape[0]:
        source_features, target_features = (
            target_features,
            source_features,
        )

    target_length = target_features.shape[0]
    if target_length <= 0:
        return 0.0

    correlation_count = (
        source_features.shape[0] - target_length + 1
    )
    if correlation_count <= 0:
        return 0.0

    correlations = np.zeros(
        correlation_count,
        dtype="float32",
    )

    for feature_index in range(source_features.shape[1]):
        correlations += np.correlate(
            source_features[:, feature_index],
            target_features[:, feature_index],
            mode="valid",
        ).astype("float32")

    correlations /= float(target_length)

    return float(np.max(correlations))


def sequence_feature_similarity(source_features, target_features):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    source_features = np.asarray(
        source_features,
        dtype="float32",
    )
    target_features = np.asarray(
        target_features,
        dtype="float32",
    )

    if source_features.size == 0 or target_features.size == 0:
        return 0.0

    if source_features.shape[1] != target_features.shape[1]:
        feature_count = min(
            source_features.shape[1],
            target_features.shape[1],
        )
        source_features = source_features[:, :feature_count]
        target_features = target_features[:, :feature_count]

    best_score = 0.0
    original_target_length = target_features.shape[0]

    for scale in (0.94, 1.0, 1.06):
        scaled_length = max(
            1,
            int(round(original_target_length * scale)),
        )

        if scaled_length == original_target_length:
            scaled_target = target_features
        else:
            scaled_target = resize_feature_sequence(
                target_features,
                scaled_length,
            )

        score = aligned_feature_score(
            source_features,
            scaled_target,
        )
        best_score = max(best_score, score)

    best_score = max(0.0, (best_score - 0.26) / 0.74)

    return min(1.0, best_score)


def spectrogram_similarity_prepared(source_audio, target_audio):
    source_features = spectrogram_features_prepared(source_audio)
    target_features = spectrogram_features_prepared(target_audio)

    return sequence_feature_similarity(
        source_features,
        target_features,
    )


def spectrogram_similarity(source_audio, target_audio):
    if not has_real_audio_signal(source_audio):
        return 0.0

    return spectrogram_similarity_prepared(
        prepare_audio_for_match(source_audio),
        prepare_audio_for_match(target_audio),
    )


def hz_to_mel(hz):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    return 2595.0 * np.log10(1.0 + hz / 700.0)


def mel_to_hz(mel):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)


def mel_filterbank(
    sample_rate,
    fft_size=2048,
    mel_count=48,
    min_hz=20.0,
    max_hz=None,
):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    sample_rate = int(sample_rate or 44100)
    fft_size = int(fft_size)
    mel_count = int(mel_count)
    max_hz = float(max_hz or sample_rate / 2.0)
    cache_key = (
        sample_rate,
        fft_size,
        mel_count,
        float(min_hz),
        max_hz,
    )
    cached = cache_get(_MEL_FILTER_CACHE, cache_key)

    if cached is not None:
        return cached

    min_mel = hz_to_mel(float(min_hz))
    max_mel = hz_to_mel(max_hz)
    mel_points = np.linspace(
        min_mel,
        max_mel,
        mel_count + 2,
    )
    hz_points = mel_to_hz(mel_points)
    bins = np.floor(
        (fft_size + 1) * hz_points / sample_rate
    ).astype("int32")
    bins = np.clip(
        bins,
        0,
        fft_size // 2,
    )
    filters = np.zeros(
        (mel_count, fft_size // 2 + 1),
        dtype="float32",
    )

    for index in range(mel_count):
        left = int(bins[index])
        center = max(left + 1, int(bins[index + 1]))
        right = max(center + 1, int(bins[index + 2]))
        center = min(center, filters.shape[1] - 1)
        right = min(right, filters.shape[1])

        if center > left:
            filters[index, left:center] = np.linspace(
                0.0,
                1.0,
                center - left,
                endpoint=False,
                dtype="float32",
            )

        if right > center:
            filters[index, center:right] = np.linspace(
                1.0,
                0.0,
                right - center,
                endpoint=False,
                dtype="float32",
            )

    filters.setflags(write=False)

    return cache_set(
        _MEL_FILTER_CACHE,
        cache_key,
        filters,
        _MAX_FEATURE_CACHE_SIZE,
    )


def mel_spectrogram_features_prepared(
    audio,
    sample_rate=44100,
    frame_size=2048,
    hop_size=512,
    mel_count=48,
):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    emphasized = pre_emphasis(audio)
    frames = audio_frames(emphasized, frame_size, hop_size)

    if frames.size == 0:
        return np.empty((0, 0), dtype="float32")

    window = cached_hanning(frame_size)
    spectrum = np.fft.rfft(frames * window, axis=1)
    power = np.square(np.abs(spectrum)).astype("float32")
    filters = mel_filterbank(
        sample_rate,
        frame_size,
        mel_count,
    )
    mel = np.dot(power, filters.T)
    mel = np.log1p(mel)
    mel = suppress_stationary_background(mel)
    mel = normalize_feature_rows(mel)

    return add_feature_deltas(mel)


def mel_spectrogram_features(
    audio,
    sample_rate=44100,
    frame_size=2048,
    hop_size=512,
    mel_count=48,
):
    return mel_spectrogram_features_prepared(
        prepare_audio_for_match(audio),
        sample_rate,
        frame_size,
        hop_size,
        mel_count,
    )


def mel_spectrogram_similarity_prepared(
    source_audio,
    target_audio,
    sample_rate=44100,
):
    source_features = mel_spectrogram_features_prepared(
        source_audio,
        sample_rate=sample_rate,
    )
    target_features = mel_spectrogram_features_prepared(
        target_audio,
        sample_rate=sample_rate,
    )

    return sequence_feature_similarity(
        source_features,
        target_features,
    )


def mel_spectrogram_similarity(
    source_audio,
    target_audio,
    sample_rate=44100,
):
    if not has_real_audio_signal(source_audio):
        return 0.0

    return mel_spectrogram_similarity_prepared(
        prepare_audio_for_match(source_audio),
        prepare_audio_for_match(target_audio),
        sample_rate,
    )


def dct_features(features, coefficient_count=13):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    features = np.asarray(features, dtype="float32")
    if features.size == 0:
        return features

    feature_count = features.shape[1]
    coefficient_count = min(
        int(coefficient_count),
        feature_count,
    )
    cache_key = (feature_count, coefficient_count)
    basis = cache_get(_DCT_CACHE, cache_key)

    if basis is None:
        feature_indexes = np.arange(
            feature_count,
            dtype="float32",
        )
        coefficient_indexes = np.arange(
            coefficient_count,
            dtype="float32",
        )[:, None]
        basis = np.cos(
            np.pi
            * coefficient_indexes
            * (feature_indexes[None, :] + 0.5)
            / feature_count
        ).astype("float32")
        basis.setflags(write=False)
        cache_set(
            _DCT_CACHE,
            cache_key,
            basis,
            _MAX_FEATURE_CACHE_SIZE,
        )

    result = np.dot(features, basis.T)

    return normalize_feature_rows(result)


def mfcc_similarity_prepared(
    source_audio,
    target_audio,
    sample_rate=44100,
):
    source_mel = mel_spectrogram_features_prepared(
        source_audio,
        sample_rate=sample_rate,
    )
    target_mel = mel_spectrogram_features_prepared(
        target_audio,
        sample_rate=sample_rate,
    )
    source_features = dct_features(source_mel, 13)
    target_features = dct_features(target_mel, 13)

    return sequence_feature_similarity(
        source_features,
        target_features,
    )


def mfcc_similarity(
    source_audio,
    target_audio,
    sample_rate=44100,
):
    if not has_real_audio_signal(source_audio):
        return 0.0

    return mfcc_similarity_prepared(
        prepare_audio_for_match(source_audio),
        prepare_audio_for_match(target_audio),
        sample_rate,
    )


def chroma_bin_mapping(sample_rate, frame_size):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    sample_rate = int(sample_rate or 44100)
    frame_size = int(frame_size)
    cache_key = (sample_rate, frame_size)
    cached = cache_get(_CHROMA_CACHE, cache_key)

    if cached is not None:
        return cached

    frequencies = np.fft.rfftfreq(
        frame_size,
        1.0 / sample_rate,
    )
    valid_indexes = np.flatnonzero(frequencies >= 27.5)
    pitches = (
        np.rint(
            12.0
            * np.log2(frequencies[valid_indexes] / 440.0)
        ).astype("int32")
        % 12
    )
    result = (valid_indexes, pitches)

    return cache_set(
        _CHROMA_CACHE,
        cache_key,
        result,
        _MAX_FEATURE_CACHE_SIZE,
    )


def chroma_features_prepared(
    audio,
    sample_rate=44100,
    frame_size=4096,
    hop_size=1024,
):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError("numpy is required. Install it with: pip install numpy")

    emphasized = pre_emphasis(audio, 0.94)
    frames = audio_frames(emphasized, frame_size, hop_size)

    if frames.size == 0:
        return np.empty((0, 0), dtype="float32")

    window = cached_hanning(frame_size)
    spectrum = np.abs(
        np.fft.rfft(frames * window, axis=1)
    ).astype("float32")
    valid_indexes, pitches = chroma_bin_mapping(
        sample_rate,
        frame_size,
    )
    chroma = np.zeros(
        (frames.shape[0], 12),
        dtype="float32",
    )

    for pitch in range(12):
        pitch_indexes = valid_indexes[pitches == pitch]
        if pitch_indexes.size:
            chroma[:, pitch] = np.sum(
                spectrum[:, pitch_indexes],
                axis=1,
            )

    chroma = np.log1p(chroma)
    chroma = suppress_stationary_background(chroma, 0.6)
    chroma = normalize_feature_rows(chroma)

    return add_feature_deltas(chroma, 0.25)


def chroma_features(
    audio,
    sample_rate=44100,
    frame_size=4096,
    hop_size=1024,
):
    return chroma_features_prepared(
        prepare_audio_for_match(audio),
        sample_rate,
        frame_size,
        hop_size,
    )


def chroma_similarity_prepared(
    source_audio,
    target_audio,
    sample_rate=44100,
):
    source_features = chroma_features_prepared(
        source_audio,
        sample_rate=sample_rate,
    )
    target_features = chroma_features_prepared(
        target_audio,
        sample_rate=sample_rate,
    )

    return sequence_feature_similarity(
        source_features,
        target_features,
    )


def chroma_similarity(
    source_audio,
    target_audio,
    sample_rate=44100,
):
    if not has_real_audio_signal(source_audio):
        return 0.0

    return chroma_similarity_prepared(
        prepare_audio_for_match(source_audio),
        prepare_audio_for_match(target_audio),
        sample_rate,
    )


def build_audio_profile(audio, sample_rate=44100):
    prepared = prepare_audio_for_match(audio)

    return {
        "audio": prepared,
        "sample_rate": int(sample_rate),
        "waveform": prepared,
        "envelope": None,
        "spectrogram": None,
        "mel_spectrogram": None,
        "mfcc": None,
        "chroma": None,
    }


def get_profile_features(profile, feature_name):
    features = profile.get(feature_name)
    if features is not None:
        return features

    audio = profile["audio"]
    sample_rate = profile["sample_rate"]

    if feature_name == "envelope":
        try:
            import numpy as np
        except ImportError:
            raise RuntimeError(
                "numpy is required. Install it with: pip install numpy"
            )

        features = smooth_audio_values(np.abs(audio), 192)
    elif feature_name == "spectrogram":
        features = spectrogram_features_prepared(audio)
    elif feature_name == "mel_spectrogram":
        features = mel_spectrogram_features_prepared(
            audio,
            sample_rate=sample_rate,
        )
    elif feature_name == "mfcc":
        mel_features = get_profile_features(
            profile,
            "mel_spectrogram",
        )
        features = dct_features(mel_features, 13)
    elif feature_name == "chroma":
        features = chroma_features_prepared(
            audio,
            sample_rate=sample_rate,
        )
    else:
        features = audio

    profile[feature_name] = features

    return features


def profile_waveform_similarity(source_profile, target_profile):
    return waveform_similarity_prepared(
        source_profile["waveform"],
        target_profile["waveform"],
    )


def profile_envelope_similarity(source_profile, target_profile):
    source_envelope = get_profile_features(
        source_profile,
        "envelope",
    )
    target_envelope = get_profile_features(
        target_profile,
        "envelope",
    )
    source_envelope, target_envelope = downsample_pair_for_match(
        source_envelope,
        target_envelope,
        max_target_length=2600,
    )
    scores, _, _ = normalized_cross_correlation(
        source_envelope,
        target_envelope,
    )

    if scores.size == 0:
        return 0.0

    score = float(scores.max())
    score = max(0.0, (score - 0.24) / 0.76)

    return min(1.0, score)


def profile_feature_similarity(
    source_profile,
    target_profile,
    feature_name,
):
    return sequence_feature_similarity(
        get_profile_features(source_profile, feature_name),
        get_profile_features(target_profile, feature_name),
    )


def spectral_similarity(source_audio, target_audio):
    return spectrogram_similarity(source_audio, target_audio)


def fingerprint_similarity(source_audio, target_audio):
    if not has_real_audio_signal(source_audio):
        return 0.0

    source_profile = build_audio_profile(source_audio)
    target_profile = build_audio_profile(target_audio)
    waveform_score = profile_waveform_similarity(
        source_profile,
        target_profile,
    )
    spectrogram_score = profile_feature_similarity(
        source_profile,
        target_profile,
        "spectrogram",
    )

    score = max(
        waveform_score * 0.62 + spectrogram_score * 0.38,
        spectrogram_score * 0.86 + waveform_score * 0.14,
    )

    return max(0.0, min(1.0, float(score)))


def hybrid_profile_similarity(source_profile, target_profile):
    waveform_score = profile_waveform_similarity(
        source_profile,
        target_profile,
    )
    spectrogram_score = profile_feature_similarity(
        source_profile,
        target_profile,
        "spectrogram",
    )
    mel_score = profile_feature_similarity(
        source_profile,
        target_profile,
        "mel_spectrogram",
    )
    envelope_score = profile_envelope_similarity(
        source_profile,
        target_profile,
    )

    balanced_score = (
        waveform_score * 0.34
        + spectrogram_score * 0.28
        + mel_score * 0.28
        + envelope_score * 0.10
    )
    noise_resistant_score = (
        max(spectrogram_score, mel_score) * 0.70
        + min(spectrogram_score, mel_score) * 0.20
        + envelope_score * 0.06
        + waveform_score * 0.04
    )
    score = max(balanced_score, noise_resistant_score)

    return max(0.0, min(1.0, float(score)))


def hybrid_similarity(
    source_audio,
    target_audio,
    sample_rate=44100,
):
    if not has_real_audio_signal(source_audio):
        return 0.0

    source_profile = build_audio_profile(
        source_audio,
        sample_rate,
    )
    target_profile = build_audio_profile(
        target_audio,
        sample_rate,
    )

    return hybrid_profile_similarity(
        source_profile,
        target_profile,
    )


def audio_similarity_profiles(
    source_profile,
    target_profile,
    detection_formula="hybrid",
):
    detection_formula = normalize_detection_formula(
        detection_formula
    )

    if detection_formula == "fingerprint":
        waveform_score = profile_waveform_similarity(
            source_profile,
            target_profile,
        )
        spectrogram_score = profile_feature_similarity(
            source_profile,
            target_profile,
            "spectrogram",
        )
        return max(
            waveform_score * 0.62 + spectrogram_score * 0.38,
            spectrogram_score * 0.86 + waveform_score * 0.14,
        )

    if detection_formula in ("spectral", "spectrogram"):
        return profile_feature_similarity(
            source_profile,
            target_profile,
            "spectrogram",
        )

    if detection_formula == "mel_spectrogram":
        return profile_feature_similarity(
            source_profile,
            target_profile,
            "mel_spectrogram",
        )

    if detection_formula == "mfcc":
        return profile_feature_similarity(
            source_profile,
            target_profile,
            "mfcc",
        )

    if detection_formula == "chroma":
        return profile_feature_similarity(
            source_profile,
            target_profile,
            "chroma",
        )

    if detection_formula == "waveform":
        return profile_waveform_similarity(
            source_profile,
            target_profile,
        )

    return hybrid_profile_similarity(
        source_profile,
        target_profile,
    )


def audio_similarity(
    source_audio,
    target_audio,
    detection_formula="hybrid",
    sample_rate=44100,
):
    if not has_real_audio_signal(source_audio):
        return 0.0

    source_profile = build_audio_profile(
        source_audio,
        sample_rate,
    )
    target_profile = build_audio_profile(
        target_audio,
        sample_rate,
    )

    return audio_similarity_profiles(
        source_profile,
        target_profile,
        detection_formula,
    )


def get_loopback_microphone():
    global _LOOPBACK_MICROPHONE

    if _LOOPBACK_MICROPHONE is not None:
        return _LOOPBACK_MICROPHONE

    try:
        import soundcard as sc
    except ImportError:
        raise RuntimeError(
            "soundcard is required. Install it with: pip install soundcard"
        )

    speaker = sc.default_speaker()
    microphones = sc.all_microphones(include_loopback=True)
    speaker_name = str(
        getattr(speaker, "name", "") or ""
    ).lower()

    for microphone in microphones:
        microphone_name = str(
            getattr(microphone, "name", "") or ""
        ).lower()

        if speaker_name and speaker_name in microphone_name:
            _LOOPBACK_MICROPHONE = microphone
            return microphone

    for microphone in microphones:
        microphone_name = str(
            getattr(microphone, "name", "") or ""
        ).lower()

        if (
            "loopback" in microphone_name
            or "monitor" in microphone_name
        ):
            _LOOPBACK_MICROPHONE = microphone
            return microphone

    if microphones:
        _LOOPBACK_MICROPHONE = microphones[0]
        return microphones[0]

    raise RuntimeError("No loopback audio device found.")


def record_system_audio(
    duration,
    sample_rate,
    runtime=None,
    warmup=True,
):
    try:
        import numpy as np
    except ImportError:
        raise RuntimeError(
            "numpy is required. Install it with: pip install numpy"
        )

    microphone = get_loopback_microphone()
    duration = max(0.1, float(duration or 0))
    sample_rate = max(8000, int(sample_rate or 44100))
    chunk_seconds = 0.1
    warmup_seconds = 0.08 if warmup else 0.0
    chunk_frames = max(1, int(sample_rate * chunk_seconds))
    warmup_frames = max(0, int(sample_rate * warmup_seconds))
    total_frames = max(1, int(duration * sample_rate))
    remaining_frames = total_frames
    chunks = []

    with microphone.recorder(samplerate=sample_rate) as recorder:
        discarded_frames = warmup_frames

        while discarded_frames > 0:
            if is_runtime_stopped(runtime):
                break

            current_frames = min(
                chunk_frames,
                discarded_frames,
            )
            recorder.record(numframes=current_frames)
            discarded_frames -= current_frames

        while remaining_frames > 0:
            if is_runtime_stopped(runtime):
                break

            current_frames = min(
                chunk_frames,
                remaining_frames,
            )
            data = recorder.record(numframes=current_frames)

            if data.size > 0:
                if data.ndim > 1:
                    data = np.mean(
                        data,
                        axis=1,
                        dtype="float32",
                    )

                chunks.append(
                    np.asarray(data, dtype="float32")
                )

            remaining_frames -= current_frames

    if not chunks:
        return np.array([], dtype="float32")

    return remove_dc_offset(
        np.concatenate(chunks).astype("float32")
    )


def build_target_audio_for_match(
    target_audio,
    match_mode,
    partial_seconds,
    sample_rate,
    listen_duration,
):
    target_audio = prepare_audio_for_match(target_audio)

    if target_audio.size == 0:
        return target_audio

    if match_mode == "partial":
        minimum_length = max(
            1,
            int(
                max(
                    float(partial_seconds or 0),
                    float(listen_duration or 0),
                )
                * int(sample_rate or 44100)
            ),
        )
        return extend_audio_for_loop_matching(
            target_audio,
            minimum_length,
        )

    return target_audio.astype("float32", copy=False)


def get_target_profile(
    audio,
    sample_rate,
    match_mode,
    partial_seconds,
    listen_duration,
):
    audio_key = audio_value_cache_key(audio, sample_rate)
    cache_key = (
        audio_key,
        int(sample_rate),
        str(match_mode),
        round(float(partial_seconds), 4),
        round(float(listen_duration), 4),
    )
    cached_profile = cache_get(_TARGET_CACHE, cache_key)

    if cached_profile is not None:
        return cached_profile

    target_audio = load_audio_value(audio, sample_rate)
    target_audio = build_target_audio_for_match(
        target_audio,
        match_mode,
        partial_seconds,
        sample_rate,
        listen_duration,
    )
    profile = build_audio_profile(
        target_audio,
        sample_rate,
    )
    profile["audio"].setflags(write=False)

    return cache_set(
        _TARGET_CACHE,
        cache_key,
        profile,
        _MAX_TARGET_CACHE_SIZE,
    )


def check_audio_match(
    audio_file,
    confidence,
    duration,
    sample_rate,
    match_mode,
    partial_seconds,
    detection_formula,
    runtime=None,
    warmup=True,
):
    sample_rate = normalize_int(
        sample_rate,
        44100,
        8000,
        192000,
    )
    duration = normalize_float(
        duration,
        3.0,
        0.1,
        120.0,
    )
    confidence = normalize_float(
        confidence,
        0.55,
        0.0,
        1.0,
    )
    partial_seconds = normalize_float(
        partial_seconds,
        2.0,
        0.1,
        120.0,
    )
    detection_formula = normalize_detection_formula(
        detection_formula
    )
    match_mode = str(
        match_mode or "partial"
    ).strip().lower()
    audio = normalize_audio_value(audio_file)
    original_target_audio = load_audio_value(
        audio,
        sample_rate,
    )

    if match_mode == "partial":
        duration = max(0.5, partial_seconds)
    else:
        duration = max(
            duration,
            len(original_target_audio) / float(sample_rate),
        )

    target_profile = get_target_profile(
        audio,
        sample_rate,
        match_mode,
        partial_seconds,
        duration,
    )
    captured_audio = record_system_audio(
        duration,
        sample_rate,
        runtime=runtime,
        warmup=warmup,
    )
    captured_rms = audio_rms(captured_audio)
    captured_peak = audio_peak(captured_audio)
    captured_active_ratio = audio_active_ratio(
        captured_audio,
        0.004,
    )

    result = {
        "condition": False,
        "matched": False,
        "confidence": 0.0,
        "required_confidence": confidence,
        "audio_file": audio.get("file_name", ""),
        "duration": duration,
        "sample_rate": sample_rate,
        "match_mode": match_mode,
        "detection_formula": detection_formula,
        "captured_rms": captured_rms,
        "captured_peak": captured_peak,
        "captured_active_ratio": captured_active_ratio,
    }

    if is_runtime_stopped(runtime):
        result["stopped"] = True
        return result

    if not has_real_audio_signal(captured_audio):
        return result

    source_profile = build_audio_profile(
        captured_audio,
        sample_rate,
    )
    score = audio_similarity_profiles(
        source_profile,
        target_profile,
        detection_formula,
    )
    score = max(0.0, min(1.0, float(score)))
    matched = score >= confidence

    result["condition"] = matched
    result["matched"] = matched
    result["confidence"] = score

    return result


class WaitForAudioCommand(MacroCommand):
    id = "audio.wait_for_audio"
    title = "Wait For Audio"
    category = AudioCategory
    icon = "mc:e023"
    description = "Wait until selected audio is playing on the computer."
    result_policy = ResultPolicy.CONDITION
    fields = [
        {
            "name": "audio_file",
            "title": "Audio",
            "value_type": "audio",
            "default_value": empty_audio(),
        },
        {
            "name": "match_mode",
            "title": "Match Mode",
            "value_type": "choice",
            "options": [
                {
                    "value": "partial",
                    "title": "Part of Audio",
                },
                {
                    "value": "full",
                    "title": "Full Audio",
                },
            ],
            "default_value": "partial",
        },
        {
            "name": "detection_formula",
            "title": "Detection Formula",
            "value_type": "choice",
            "options": [
                {
                    "value": "spectral",
                    "title": "Spectral Match",
                },
                {
                    "value": "fingerprint",
                    "title": "Audio Fingerprint",
                },
                {
                    "value": "spectrogram",
                    "title": "Spectrogram Match",
                },
                {
                    "value": "mel_spectrogram",
                    "title": "Mel Spectrogram Match",
                },
                {
                    "value": "mfcc",
                    "title": "MFCC Match",
                },
                {
                    "value": "chroma",
                    "title": "Chroma Match",
                },
                {
                    "value": "waveform",
                    "title": "Waveform Match",
                },
                {
                    "value": "hybrid",
                    "title": "Hybrid Match",
                },
            ],
            "default_value": "spectral",
        },
        {
            "name": "confidence",
            "title": "Confidence",
            "value_type": "float",
            "min_value": 0.0,
            "max_value": 1.0,
            "default_value": 0.55,
        },
        {
            "name": "timeout",
            "title": "Timeout (seconds)",
            "value_type": "float",
            "min_value": 0.0,
            "max_value": 86400.0,
            "default_value": 30.0,
        },
        {
            "name": "listen_duration",
            "title": "Listen Duration (seconds)",
            "value_type": "float",
            "min_value": 0.1,
            "max_value": 120.0,
            "default_value": 3.0,
        },
        {
            "name": "interval",
            "title": "Check Interval (seconds)",
            "value_type": "float",
            "min_value": 0.05,
            "max_value": 60.0,
            "default_value": 0.25,
        },
        {
            "name": "partial_seconds",
            "title": "Partial Match Seconds",
            "value_type": "float",
            "min_value": 0.1,
            "max_value": 120.0,
            "default_value": 2.0,
            "visible_if": {
                "field": "match_mode",
                "operator": "==",
                "value": "partial",
            },
        },
        {
            "name": "sample_rate",
            "title": "Sample Rate",
            "value_type": "integer",
            "min_value": 8000,
            "max_value": 192000,
            "default_value": 44100,
        },
        {
            "name": "save_to_variable",
            "title": "Save To Variable",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        audio = normalize_audio_value(
            values.get("audio_file")
        )
        audio_name = audio.get("file_name") or "audio"
        timeout = values.get("timeout")
        confidence = values.get("confidence")
        detection_formula = normalize_detection_formula(
            values.get("detection_formula")
            or values.get("detection_mode")
        )

        return (
            f"wait for {audio_name} up to {timeout} secs "
            f"with {detection_formula} formula and "
            f"confidence {confidence}"
        )

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        timeout = normalize_float(
            values.get("timeout"),
            30.0,
            0.0,
            86400.0,
        )
        interval = normalize_float(
            values.get("interval"),
            0.25,
            0.05,
            60.0,
        )
        save_to_variable = values.get(
            "save_to_variable"
        )
        detection_formula = normalize_detection_formula(
            values.get("detection_formula")
            or values.get("detection_mode")
        )
        start_time = time.monotonic()
        first_recording = True

        while True:
            if is_runtime_stopped(runtime):
                result = {
                    "condition": False,
                    "matched": False,
                    "stopped": True,
                    "confidence": 0.0,
                    "required_confidence": normalize_float(
                        values.get("confidence"),
                        0.55,
                        0.0,
                        1.0,
                    ),
                    "audio_file": normalize_audio_value(
                        values.get("audio_file")
                    ).get("file_name", ""),
                    "duration": normalize_float(
                        values.get("listen_duration"),
                        3.0,
                        0.1,
                        120.0,
                    ),
                    "sample_rate": normalize_int(
                        values.get("sample_rate"),
                        44100,
                        8000,
                        192000,
                    ),
                    "match_mode": values.get(
                        "match_mode"
                    ),
                    "detection_formula": detection_formula,
                    "elapsed": time.monotonic() - start_time,
                    "timeout": timeout,
                }
                save_result_to_variable(
                    runtime,
                    save_to_variable,
                    result,
                )
                return result

            elapsed = time.monotonic() - start_time

            if timeout > 0 and elapsed >= timeout:
                result = {
                    "condition": False,
                    "matched": False,
                    "confidence": 0.0,
                    "required_confidence": normalize_float(
                        values.get("confidence"),
                        0.55,
                        0.0,
                        1.0,
                    ),
                    "audio_file": normalize_audio_value(
                        values.get("audio_file")
                    ).get("file_name", ""),
                    "duration": normalize_float(
                        values.get("listen_duration"),
                        3.0,
                        0.1,
                        120.0,
                    ),
                    "sample_rate": normalize_int(
                        values.get("sample_rate"),
                        44100,
                        8000,
                        192000,
                    ),
                    "match_mode": values.get(
                        "match_mode"
                    ),
                    "detection_formula": detection_formula,
                    "elapsed": elapsed,
                    "timeout": timeout,
                }
                save_result_to_variable(
                    runtime,
                    save_to_variable,
                    result,
                )
                return result

            audio_result = check_audio_match(
                audio_file=values.get("audio_file"),
                confidence=values.get("confidence"),
                duration=values.get("listen_duration"),
                sample_rate=values.get("sample_rate"),
                match_mode=values.get("match_mode"),
                partial_seconds=values.get(
                    "partial_seconds"
                ),
                detection_formula=detection_formula,
                runtime=runtime,
                warmup=first_recording,
            )
            first_recording = False
            elapsed = time.monotonic() - start_time
            audio_result["elapsed"] = elapsed
            audio_result["timeout"] = timeout

            if audio_result.get("stopped"):
                save_result_to_variable(
                    runtime,
                    save_to_variable,
                    audio_result,
                )
                return audio_result

            if audio_result.get("condition"):
                save_result_to_variable(
                    runtime,
                    save_to_variable,
                    audio_result,
                )
                return audio_result

            if timeout > 0 and elapsed >= timeout:
                audio_result["condition"] = False
                audio_result["matched"] = False
                save_result_to_variable(
                    runtime,
                    save_to_variable,
                    audio_result,
                )
                return audio_result

            sleep_runtime(runtime, interval)


def register_macro(registry):
    registry.register(WaitForAudioCommand)
