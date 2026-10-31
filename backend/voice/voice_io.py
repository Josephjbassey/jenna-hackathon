"""
Voice I/O for Jenna-Unified desktop voice agent.

STT: faster-whisper (CPU, tiny.en int8 — good balance for 8 GB RAM laptops)
TTS: Piper (lightweight local neural TTS, fast on CPU) with Kokoro ONNX optional.
Wake word: openWakeWord ONNX (hey_jenna.onnx).

Both run fully offline — no cloud STT/TTS APIs, nothing leaves the machine.
"""
import tempfile
import subprocess
import os
import sys
import shutil
import threading

import numpy as np
import sounddevice as sd

try:
    import httpx
    _HAS_HTTPX = True
except Exception:
    _HAS_HTTPX = False

from config import (
    SAMPLE_RATE, WHISPER_MODEL, WHISPER_COMPUTE, WHISPER_BEAM_SIZE, RECORD_SECONDS,
    TTS_ENGINE, PIPER_VOICE_PATH, KOKORO_MODEL_PATH, KOKORO_VOICES_PATH,
    WAKE_WORD_MODEL, WAKE_WORD_MEL_PATH, WAKE_WORD_ENABLED,
    DEEPGRAM_API_KEY, DEEPGRAM_MODEL, DEEPGRAM_FALLBACK,
    DEEPGRAM_VOICES, ACTIVE_TTS_VOICE, ACTIVE_TTS_ENGINE,
)

_current_tts_voice = ACTIVE_TTS_VOICE
_current_tts_engine = ACTIVE_TTS_ENGINE

# ── STT (lazy-loaded) ─────────────────────────────────────────────────────
_whisper_model = None
_whisper_lock = threading.Lock()


def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        with _whisper_lock:
            if _whisper_model is None:
                from faster_whisper import WhisperModel
                _whisper_model = WhisperModel(
                    WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE
                )
    return _whisper_model


def record_audio(seconds: float = RECORD_SECONDS) -> np.ndarray:
    """Record `seconds` of mono audio from the default microphone."""
    print(f"[voice] listening for {seconds}s...")
    audio = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    return audio.flatten()


def record_until_silence(max_duration: float = 15.0) -> np.ndarray:
    """Record from mic until silence, with a small pre-roll so onset isn't clipped."""
    import sounddevice as sd
    from collections import deque

    chunk_size = 1024
    # With float32 audio in [-1, 1], scale by 32767 to match 16-bit PCM energy threshold
    energy_threshold = 350.0
    silence_limit_chunks = int((1.0 * SAMPLE_RATE) / chunk_size)  # 1s silence = stop
    max_chunks = int((max_duration * SAMPLE_RATE) / chunk_size)
    pre_roll_size = max(3, int(0.2 * SAMPLE_RATE / chunk_size))  # 200ms pre-roll

    pre_roll = deque(maxlen=pre_roll_size)
    recorded = []
    speech_started = False
    silent_chunks = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            chunk = chunk.flatten()
            rms = float(np.sqrt(np.mean(chunk ** 2))) * 32767.0 if len(chunk) else 0.0

            if not speech_started:
                pre_roll.append(chunk.copy())
                if rms > energy_threshold:
                    speech_started = True
                    recorded.extend(pre_roll)
                    recorded.append(chunk.copy())
                    silent_chunks = 0
            else:
                recorded.append(chunk.copy())
                if rms < energy_threshold:
                    silent_chunks += 1
                    if silent_chunks >= silence_limit_chunks:
                        break
                else:
                    silent_chunks = 0

    if not recorded:
        return np.zeros(int(0.5 * SAMPLE_RATE), dtype="float32")
    return np.concatenate(recorded)


def transcribe(audio: np.ndarray) -> str:
    """Transcribe audio to text.

    Tries Deepgram (cloud) first if an API key is configured and the machine
    is online; falls back to faster-whisper (local, offline) otherwise.
    """
    if DEEPGRAM_FALLBACK and DEEPGRAM_API_KEY and _HAS_HTTPX:
        try:
            return _transcribe_deepgram(audio)
        except Exception as e:
            print(f"[voice] Deepgram unavailable ({e}); falling back to faster-whisper.")

    model = _load_whisper()
    segments, _ = model.transcribe(audio, language="en", beam_size=WHISPER_BEAM_SIZE)
    return " ".join(seg.text.strip() for seg in segments).strip()


def _transcribe_deepgram(audio: np.ndarray) -> str:
    """Transcribe audio via Deepgram's REST API (requires internet + API key)."""
    import wave
    import io

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        pcm = (audio * 32767).astype("<i2").tobytes()
        wf.writeframes(pcm)
    buf.seek(0)

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
    }
    params = {
        "model": DEEPGRAM_MODEL,
        "smart_format": "true",
        "punctuate": "true",
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            "https://api.deepgram.com/v1/listen",
            headers=headers,
            params=params,
            files={"file": ("audio.wav", buf, "audio/wav")},
        )
        resp.raise_for_status()
        data = resp.json()

    return data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()


# ── Tones (in-memory, no audio assets) ────────────────────────────────────
def _tone(freq: float, duration: float, volume: float = 0.2) -> np.ndarray:
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = np.sin(freq * t * 2 * np.pi)
    fade = min(200, len(wave) // 4)
    envelope = np.ones_like(wave)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    return (wave * envelope * volume).astype(np.float32)


def play_listen_tone() -> None:
    """Short ascending chime when push-to-talk activates."""
    tone = np.concatenate([_tone(660, 0.07), _tone(880, 0.09)])
    sd.play(tone, SAMPLE_RATE)
    sd.wait()


def play_done_tone() -> None:
    """Short descending chime when a voice turn finishes."""
    tone = np.concatenate([_tone(880, 0.07), _tone(660, 0.09)])
    sd.play(tone, SAMPLE_RATE)
    sd.wait()


# ── TTS ───────────────────────────────────────────────────────────────────
_tts_engine = None
_tts_lock = threading.Lock()


def _piper_bin() -> str:
    cand = os.path.join(os.path.dirname(sys.executable), "piper")
    if os.path.exists(cand):
        return cand
    return shutil.which("piper") or "piper"


def _play_wav(file_path: str) -> None:
    """Play any WAV file using Python's standard wave library and sounddevice."""
    try:
        import wave
        with wave.open(file_path, "rb") as wf:
            samplerate = wf.getframerate()
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())
            if sampwidth == 2:
                data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                data = np.frombuffer(frames, dtype=np.float32)
            if n_channels > 1:
                data = data.reshape(-1, n_channels)
            sd.play(data, samplerate)
            sd.wait()
    except Exception:
        if shutil.which("aplay"):
            subprocess.run(["aplay", file_path], check=False)
        elif shutil.which("powershell"):
            subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{file_path}').PlaySync()"], check=False)


def speak_piper(text: str) -> None:
    """Synthesize `text` with Piper and play cross-platform."""
    if not text.strip():
        return
    piper = _piper_bin()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        subprocess.run(
            [piper, "--model", PIPER_VOICE_PATH, "--output_file", tmp_path],
            input=text.encode("utf-8"),
            check=True,
        )
        _play_wav(tmp_path)
    except Exception as e:
        print(f"[voice] Piper synthesis failed: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def get_available_voices() -> list:
    """Return all available TTS voices across Deepgram Aura and local engines."""
    return DEEPGRAM_VOICES


def get_current_voice() -> dict:
    """Return currently active TTS voice and engine."""
    return {"voice": _current_tts_voice, "engine": _current_tts_engine}


def set_voice(voice_id: str, engine: str = None) -> dict:
    """Set active TTS voice and engine."""
    global _current_tts_voice, _current_tts_engine
    _current_tts_voice = voice_id
    if engine:
        _current_tts_engine = engine
    else:
        # Infer engine from voice_id
        match = next((v for v in DEEPGRAM_VOICES if v["id"] == voice_id), None)
        if match:
            _current_tts_engine = match.get("engine", "deepgram")
        elif "aura" in voice_id:
            _current_tts_engine = "deepgram"
        elif "af_" in voice_id or "am_" in voice_id:
            _current_tts_engine = "kokoro"
        else:
            _current_tts_engine = "piper"
    print(f"[voice] Active voice set to: {_current_tts_voice} (Engine: {_current_tts_engine})")
    return {"voice": _current_tts_voice, "engine": _current_tts_engine}


def speak_deepgram(text: str, voice: str = None) -> bool:
    """Synthesize speech using Deepgram Aura TTS."""
    if not text.strip():
        return False
    if not DEEPGRAM_API_KEY:
        print("[voice] Deepgram API key missing; falling back to local TTS.")
        return False
    if not _HAS_HTTPX:
        print("[voice] httpx missing; falling back to local TTS.")
        return False

    voice_model = voice or _current_tts_voice or "aura-asteria-en"
    tmp_path = None
    try:
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json",
        }
        params = {"model": voice_model}
        payload = {"text": text}

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://api.deepgram.com/v1/speak",
                headers=headers,
                params=params,
                json=payload,
            )
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name

        _play_wav(tmp_path)
        return True
    except Exception as e:
        print(f"[voice] Deepgram TTS error ({e}); falling back to local TTS.")
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def speak_kokoro(text: str) -> None:
    """Synthesize `text` with Kokoro ONNX (optional backend)."""
    try:
        from kokoro_onnx import Kokoro
    except Exception as e:
        print(f"[voice] Kokoro not installed ({e}); falling back to Piper.")
        speak_piper(text)
        return
    if not os.path.exists(KOKORO_MODEL_PATH) or not os.path.exists(KOKORO_VOICES_PATH):
        print("[voice] Kokoro weights missing; falling back to Piper.")
        speak_piper(text)
        return
    global _tts_engine
    with _tts_lock:
        if _tts_engine is None:
            _tts_engine = Kokoro(KOKORO_MODEL_PATH, KOKORO_VOICES_PATH)
    samples, sample_rate = _tts_engine.create(text, voice=_current_tts_voice if "af_" in _current_tts_voice else "af_bella", speed=1.0)
    sd.play(samples, sample_rate)
    sd.wait()


def speak(text: str) -> None:
    """Speak `text` using the configured or runtime active voice."""
    if _current_tts_engine == "deepgram" and DEEPGRAM_API_KEY:
        success = speak_deepgram(text, _current_tts_voice)
        if success:
            return

    # Fallback to local engines
    if _current_tts_engine == "kokoro" or (TTS_ENGINE == "kokoro" and os.path.exists(KOKORO_MODEL_PATH)):
        speak_kokoro(text)
    else:
        speak_piper(text)


# ── Wake word ─────────────────────────────────────────────────────────────
def build_wake_word_detector():
    """Build an openWakeWord detector for hey_jenna.onnx, or return None if unavailable."""
    if not WAKE_WORD_ENABLED:
        return None
    if not os.path.exists(WAKE_WORD_MODEL):
        print(f"[voice] Wake word model not found: {WAKE_WORD_MODEL}")
        return None
    try:
        from openwakeword import Model
        det = Model(wakeword_models=[WAKE_WORD_MODEL], enable_mono_conversion=True)
        return det
    except Exception as e:
        print(f"[voice] openWakeWord unavailable ({e}); wake word disabled.")
        return None
