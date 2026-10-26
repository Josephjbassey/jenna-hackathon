"""
Unified configuration for Jenna-Unified desktop voice agent.

Merged from Jenna LVA + local_ai_agent + Jenna-AI + Jenna v2.
All tuning knobs in one place: models, Ollama, voice, paths, safety.
Secrets belong in .env (chmod 600), never in this file.
"""
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:
    pass

try:
    from pynput import keyboard
except Exception:
    keyboard = None

# ─── Paths ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
SANDBOX_DIR = BASE_DIR / "sandbox"
SANDBOX_DIR.mkdir(exist_ok=True)
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
MODELS_DIR = BASE_DIR / "models"
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

# ─── Ollama (default local provider) ──────────────────────────────────────
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

MODELS = {
    "fast":       "qwen2.5:1.5b",        # General purpose — fast, fits 8 GB
    "coder":      "qwen2.5-coder:3b",    # Code tasks — pulled, fits 8 GB
    "coder-strong": "qwen2.5-coder:7b",  # Heavy code tasks — use deliberately
    "writer":     "gemma2:2b",           # Creative writing, essays, emails
}
DEFAULT_MODEL_KEY = "fast"
EMBEDDING_MODEL = "nomic-embed-text:latest"

OLLAMA_OPTIONS = {
    "num_ctx": 4096,          # Context window — room for tools + short history
    "num_predict": 300,       # Max reply tokens (TTS reads this aloud)
    "temperature": 0.7,       # Balanced creativity
}
OLLAMA_KEEP_ALIVE = -1        # Pin model in RAM — eliminates cold-start latency

# ─── Ultramarine / Paper Instruments (optional cloud provider) ─────────────
# Base URL: https://api.paperinstruments.com/v1  |  Model: ultramarine-1-flash
# Prepaid billing — set PAPERINSTRUMENTS_API_KEY in .env (chmod 600).
ULTRAMARINE_API_BASE = os.getenv("ULTRAMARINE_API_BASE", "https://api.paperinstruments.com/v1")
ULTRAMARINE_API_KEY = os.getenv("PAPERINSTRUMENTS_API_KEY", "")

# ─── NVIDIA Nemotron (optional cloud provider) ─────────────────────────────
NVIDIA_API_BASE = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# Model routing keywords — router picks the right specialist model per query.
MODEL_ROUTES = {
    "coder-strong": (
        "heavy coding", "complex code", "architecture", "big script",
        "huge refactor", "advanced python", "debug this codebase",
    ),
    "coder": (
        "code", "script", "python", "debug", "compile", "build", "refactor",
        "bug", "html", "css", "js", "django", "programming", "function",
    ),
    "writer": (
        "write", "draft", "email", "essay", "blog", "story", "poem",
        "document", "summarize", "creative", "letter", "report",
    ),
}

# Provider selection per role: "ollama" or "nvidia".
MODEL_PROVIDERS = {
    role: os.getenv(f"{role.upper().replace('-', '_')}_PROVIDER", "ollama")
    for role in ("fast", "coder", "coder-strong", "writer")
}

# Provider-specific model IDs for OpenAI-compatible backends.
PROVIDER_MODELS = {
    "nvidia": {"fast": os.getenv("NVIDIA_FAST_MODEL", ""), "coder": os.getenv("NVIDIA_CODER_MODEL", ""),
               "coder-strong": os.getenv("NVIDIA_CODER_STRONG_MODEL", ""), "writer": os.getenv("NVIDIA_WRITER_MODEL", "")},
    "ultramarine": {"fast": "ultramarine-1-flash", "coder": "ultramarine-1-flash",
                    "coder-strong": "ultramarine-1-flash", "writer": "ultramarine-1-flash"},
}

# ─── Audio / ASR ──────────────────────────────────────────────────────────
SAMPLE_RATE = 16000               # Standard for Whisper
WHISPER_MODEL = "tiny.en"         # tiny.en ~75 MB — best for 8 GB. Bump to base.en if you upgrade RAM.
WHISPER_COMPUTE = "int8"          # int8 quantization for speed
WHISPER_BEAM_SIZE = 1             # Greedy decoding — fastest
RECORD_SECONDS = 5.0              # Fixed recording window (fallback if no VAD)

# Deepgram (cloud STT fallback — requires internet + API key)
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
DEEPGRAM_MODEL = "nova-2"
DEEPGRAM_FALLBACK = os.getenv("JENNA_DEEPGRAM_FALLBACK", "true").lower() == "true"

# ─── TTS ──────────────────────────────────────────────────────────────────
# "piper" (fast, lightweight) or "kokoro" (natural, slightly heavier)
TTS_ENGINE = os.getenv("JENNA_TTS_ENGINE", "piper")
PIPER_VOICE_PATH = str(MODELS_DIR / "tts" / "en_US-lessac-medium.onnx")
KOKORO_MODEL_PATH = str(MODELS_DIR / "tts" / "kokoro-v1.0.int8.onnx")
KOKORO_VOICES_PATH = str(MODELS_DIR / "tts" / "voices-v1.0.bin")

# ─── Wake Word ────────────────────────────────────────────────────────────
WAKE_WORD_ENABLED = os.getenv("JENNA_WAKE_WORD", "true").lower() == "true"
WAKE_WORD_MODEL = str(MODELS_DIR / "wakeword" / "hey_jenna.onnx")
WAKE_WORD_MEL_PATH = str(MODELS_DIR / "wakeword" / "melspectrogram.onnx")

# ─── User ─────────────────────────────────────────────────────────────────
USER_NAME = "Jabs"
ASSISTANT_NAME = "Jenna"

# ─── Hotkey ───────────────────────────────────────────────────────────────
if keyboard is None:
    HOTKEY = set()
else:
    HOTKEY = {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.Key.space}

# ─── Dashboard / overlay ──────────────────────────────────────────────────
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 8787

# ─── Executor Safety ──────────────────────────────────────────────────────
CONFIRM_BEFORE_EXECUTE = True
REJECT_DANGEROUS_COMMANDS = True
LOG_COMMANDS = True
HISTORY_FILE = SANDBOX_DIR / "command_history.json"
MAX_HISTORY_SIZE = 100

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"mkfs",
    r"dd\s+if=",
    r">\s*/dev/sda",
    r"chmod\s+-R\s+777\s+/",
    r"chown\s+-R\s+.*:.*\s+/",
    r":(){ :\|:& };:",     # Fork bomb
]

# ─── Memory ───────────────────────────────────────────────────────────────
MEMORY_DB_PATH = MEMORY_DIR / "memory.db"
LONG_TERM_MEMORY_PATH = MEMORY_DIR / "long_term.json"
CONVERSATION_HISTORY_LIMIT = 6   # Last N messages injected into context
