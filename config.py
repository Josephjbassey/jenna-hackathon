"""
Unified configuration for Jenna-Unified desktop voice agent & multi-agent squad.

Works seamlessly on Linux, Windows, and macOS.
Dynamically discovers available local Ollama models and sets sensible defaults.
All tuning knobs in one place: models, Ollama, voice, paths, safety, squad, communications.
"""
from pathlib import Path
import os
import platform
import sys
import json

# Platform detection
OS_NAME = platform.system().lower()
IS_WINDOWS = OS_NAME == "windows"
IS_LINUX = OS_NAME == "linux"
IS_MACOS = OS_NAME == "darwin"

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
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
TTS_MODELS_DIR = MODELS_DIR / "tts"
TTS_MODELS_DIR.mkdir(parents=True, exist_ok=True)
WAKEWORD_MODELS_DIR = MODELS_DIR / "wakeword"
WAKEWORD_MODELS_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
OBSIDIAN_VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", str(Path.home() / "wiki")))
if not OBSIDIAN_VAULT_PATH.exists():
    # Fallback to local memory dir if user has not set an external vault
    OBSIDIAN_VAULT_PATH = MEMORY_DIR / "obsidian_vault"
    OBSIDIAN_VAULT_PATH.mkdir(parents=True, exist_ok=True)

# ─── Ollama & Model Configuration ─────────────────────────────────────────
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Fallback default models if Ollama discovery is offline
DEFAULT_MODELS = {
    "fast":         "qwen3.5:0.8b",
    "coder":        "qwen2.5-coder:3b",
    "coder-strong": "qwen2.5-coder:3b",
    "writer":       "llama3.2:latest",
    "planner":      "phi4-mini:latest",
    "researcher":   "qwen3.5:2b",
}

def discover_ollama_models() -> dict:
    """Query Ollama daemon for installed models and map them to roles."""
    models = dict(DEFAULT_MODELS)
    try:
        import urllib.request
        import json
        req = urllib.request.Request(f"{OLLAMA_HOST.rstrip('/')}/api/tags", headers={"User-Agent": "Jenna-Unified"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            installed = [m.get("name") for m in data.get("models", []) if m.get("name")]
            if not installed:
                return models

            # Map fast / general
            for cand in ["qwen3.5:0.8b", "llama3.2:1b", "qwen2.5:1.5b", "gemma2:2b", "qwen3:0.6b", "qwen3.5:2b", "llama3.2:latest"]:
                if any(cand in m for m in installed):
                    models["fast"] = cand
                    break
            else:
                models["fast"] = installed[0]

            # Map coder
            for cand in ["qwen2.5-coder:3b", "qwen2.5-coder:7b", "qwen2.5-coder", "coder"]:
                match = next((m for m in installed if cand in m), None)
                if match:
                    models["coder"] = match
                    models["coder-strong"] = match
                    break
            else:
                models["coder"] = models["fast"]
                models["coder-strong"] = models["fast"]

            # Map writer
            for cand in ["llama3.2:latest", "gemma2:2b", "llama3.2:1b", "qwen3.5:2b"]:
                match = next((m for m in installed if cand in m), None)
                if match:
                    models["writer"] = match
                    break
            else:
                models["writer"] = models["fast"]

            # Map planner (reasoning & structured breakdown)
            for cand in ["phi4-mini:latest", "gemma2:2b", "qwen3.5:2b", "llama3.2:latest"]:
                match = next((m for m in installed if cand in m), None)
                if match:
                    models["planner"] = match
                    break
            else:
                models["planner"] = models["writer"]

            # Map researcher (fact finding & synthesis)
            for cand in ["qwen3.5:2b", "gemma2:2b", "phi4-mini:latest", "llama3.2:latest"]:
                match = next((m for m in installed if cand in m), None)
                if match:
                    models["researcher"] = match
                    break
            else:
                models["researcher"] = models["writer"]
    except Exception:
        pass
    return models

def discover_all_models() -> dict:
    """Discover all local models (Ollama & LM Studio) and configured cloud providers."""
    import urllib.request
    import json

    ollama_models = []
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST.rstrip('/')}/api/tags", headers={"User-Agent": "Jenna-Unified"})
        with urllib.request.urlopen(req, timeout=1.2) as resp:
            data = json.loads(resp.read().decode())
            for m in data.get("models", []):
                name = m.get("name")
                if name:
                    size_gb = round(m.get("size", 0) / (1024**3), 2)
                    ollama_models.append({
                        "name": name,
                        "size_gb": size_gb,
                        "provider": "ollama",
                        "details": m.get("details", {})
                    })
    except Exception:
        pass

    if not ollama_models:
        known_ollama = [
            {"name": "gemma2:2b", "provider": "ollama", "role_hint": "fast"},
            {"name": "qwen2.5:1.5b", "provider": "ollama", "role_hint": "fast"},
            {"name": "qwen2.5-coder:3b", "provider": "ollama", "role_hint": "coder"},
            {"name": "qwen3.5:0.8b", "provider": "ollama", "role_hint": "fast"},
            {"name": "llama3.2:latest", "provider": "ollama", "role_hint": "writer"},
            {"name": "phi4-mini:latest", "provider": "ollama", "role_hint": "planner"},
            {"name": "qwen3.5:2b", "provider": "ollama", "role_hint": "researcher"},
        ]
        ollama_models.extend(known_ollama)

    lmstudio_models = []
    try:
        req = urllib.request.Request(f"{LMSTUDIO_HOST.rstrip('/')}/models", headers={"User-Agent": "Jenna-Unified"})
        with urllib.request.urlopen(req, timeout=1.2) as resp:
            data = json.loads(resp.read().decode())
            for m in data.get("data", []):
                m_id = m.get("id")
                if m_id:
                    lmstudio_models.append({
                        "name": m_id,
                        "provider": "lmstudio",
                        "type": "local-llm"
                    })
    except Exception:
        # Fallback to configured Omarchy LM Studio models if daemon is offline
        for r_name, m_id in PROVIDER_MODELS.get("lmstudio", {}).items():
            if m_id not in [x["name"] for x in lmstudio_models]:
                lmstudio_models.append({
                    "name": m_id,
                    "provider": "lmstudio",
                    "role_hint": r_name
                })

    cloud_models = []
    if NVIDIA_API_KEY:
        cloud_models.append({"name": "meta/llama-3.1-nemotron-70b-instruct", "provider": "nvidia"})
        cloud_models.append({"name": "meta/llama-3.2-1b-instruct", "provider": "nvidia"})
    if OPENAI_API_KEY:
        cloud_models.append({"name": "gpt-4o", "provider": "openai"})
        cloud_models.append({"name": "gpt-4o-mini", "provider": "openai"})
    if ULTRAMARINE_API_KEY:
        cloud_models.append({"name": "qwen3.5-0.8b", "provider": "ultramarine"})

    return {
        "active_role_models": MODELS,
        "ollama": ollama_models,
        "lmstudio": lmstudio_models,
        "cloud": cloud_models
    }

MODELS = discover_ollama_models()
DEFAULT_MODEL_KEY = "fast"
ACTIVE_CUSTOM_MODEL = os.getenv("JENNA_ACTIVE_MODEL", "")
ACTIVE_CUSTOM_PROVIDER = os.getenv("JENNA_ACTIVE_PROVIDER", "ollama")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")

OLLAMA_OPTIONS = {
    "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "4096")),
    "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "350")),
    "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
}
OLLAMA_KEEP_ALIVE = -1  # Pin model in RAM to prevent reload delay

# ─── LM Studio (Local OpenAI-Compatible Server) ───────────────────────────
LMSTUDIO_HOST = os.getenv("LMSTUDIO_HOST", "http://localhost:1234/v1")
LMSTUDIO_API_KEY = os.getenv("LMSTUDIO_API_KEY", "lm-studio")

# ─── Cloud Providers (Optional) ───────────────────────────────────────────
ULTRAMARINE_API_BASE = os.getenv("ULTRAMARINE_API_BASE", "https://api.paperinstruments.com/v1")
ULTRAMARINE_API_KEY = os.getenv("PAPERINSTRUMENTS_API_KEY", "")

NVIDIA_API_BASE = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── Meta Model API (Hackathon) ─────────────────────────────────────────
META_MODEL_API_BASE = os.getenv("META_MODEL_API_BASE", "https://ai.meta.com/api")
META_MODEL_API_KEY = os.getenv("META_MODEL_API_KEY", "")

# Meta models for hackathon
META_MODELS = {
    "muse-spark-1.3": "Reasoning/agent orchestration (Planner/Commander)",
    "muse-voice-transcribe-1.0": "Speech-to-text (voice pipeline)",
    "muse-image-1.0": "Image generation/understanding (Scholar/vision)",
    "sam-3.1": "Segmentation anything (vision pipeline)",
    "muse-wonder-1.0": "Advanced reasoning",
    "muse-code": "Code generation",
}

# Provider routing per model key (defaults to local ollama or lmstudio)
MODEL_PROVIDERS = {
    "fast":         os.getenv("PROVIDER_FAST", "ollama"),
    "coder":        os.getenv("PROVIDER_CODER", "ollama"),
    "coder-strong": os.getenv("PROVIDER_CODER_STRONG", "ollama"),
    "writer":       os.getenv("PROVIDER_WRITER", "ollama"),
    "planner":      os.getenv("PROVIDER_PLANNER", "meta" if META_MODEL_API_KEY else "ollama"),
    "researcher":   os.getenv("PROVIDER_RESEARCHER", "ollama"),
}

PROVIDER_MODELS = {
    "lmstudio": {
        "fast": os.getenv("LMSTUDIO_MODEL_FAST", "LFM2-1.2B-GGUF"),
        "coder": os.getenv("LMSTUDIO_MODEL_CODER", "Qwen3-4B-GGUF"),
        "planner": os.getenv("LMSTUDIO_MODEL_PLANNER", "NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF"),
        "researcher": os.getenv("LMSTUDIO_MODEL_RESEARCHER", "Ministral-3-3B-Instruct-2512-GGUF"),
        "writer": os.getenv("LMSTUDIO_MODEL_WRITER", "Gemma-4-E2B-Uncensored-HauhauCS-Aggressive"),
        "flagship": "NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF",
        "uncensored": "Gemma-4-E2B-Uncensored-HauhauCS-Aggressive",
    },
    "nvidia": {
        "fast": "meta/llama-3.2-1b-instruct",
        "coder": "meta/codellama-70b",
        "writer": "meta/llama-3.1-nemotron-70b-instruct",
    },
    "ultramarine": {
        "fast": "qwen3.5-0.8b",
        "coder": "qwen2.5-coder-7b",
    },
    "meta": {
        "planner": "muse-spark-1.3",
        "commander": "muse-spark-1.3",
        "writer": "muse-spark-1.3",
        "coder": "muse-code",
        "researcher": "muse-wonder-1.0",
    },
}

# ─── Squad & Multi-Agent Roles ───────────────────────────────────────────
SQUAD_ROLES = {
    "commander": {
        "name": "Jenna Commander",
        "description": "Executive coordinator, voice conversationalist, and task decomposer.",
        "model_key": "fast",
    },
    "coder": {
        "name": "Jenna Engineer",
        "description": "Code generation, debugging, refactoring, terminal tasks.",
        "model_key": "coder",
    },
    "researcher": {
        "name": "Jenna Scholar",
        "description": "Web research, factual aggregation, documentation.",
        "model_key": "researcher",
    },
    "desktop": {
        "name": "Jenna Operator",
        "description": "Computer use, desktop vision, keyboard/mouse actions.",
        "model_key": "fast",
    },
    "communicator": {
        "name": "Jenna Communications",
        "description": "AgentPhone (Twilio SMS/calls) and AgentMail (Email).",
        "model_key": "fast",
    },
    "scheduler": {
        "name": "Jenna Chronos",
        "description": "Self-scheduling, reminders, recurring timers, autonomous loop.",
        "model_key": "fast",
    },
}

# ─── Audio / ASR ──────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
WHISPER_MODEL = os.getenv("JENNA_WHISPER_MODEL", "tiny.en")
WHISPER_COMPUTE = os.getenv("JENNA_WHISPER_COMPUTE", "int8")
WHISPER_BEAM_SIZE = 1
RECORD_SECONDS = 5.0

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
DEEPGRAM_MODEL = "nova-2"
DEEPGRAM_FALLBACK = os.getenv("JENNA_DEEPGRAM_FALLBACK", "true").lower() == "true"

# Deepgram Aura Voices
DEEPGRAM_VOICES = [
    {"id": "aura-asteria-en", "name": "Asteria", "gender": "Female", "accent": "US", "style": "Conversational, Warm", "engine": "deepgram"},
    {"id": "aura-luna-en", "name": "Luna", "gender": "Female", "accent": "US", "style": "Calm, Pleasant", "engine": "deepgram"},
    {"id": "aura-stella-en", "name": "Stella", "gender": "Female", "accent": "US", "style": "Professional, Articulate", "engine": "deepgram"},
    {"id": "aura-athena-en", "name": "Athena", "gender": "Female", "accent": "UK", "style": "Authoritative, Crisp", "engine": "deepgram"},
    {"id": "aura-hera-en", "name": "Hera", "gender": "Female", "accent": "US", "style": "Energetic, Expressive", "engine": "deepgram"},
    {"id": "aura-orion-en", "name": "Orion", "gender": "Male", "accent": "US", "style": "Casual, Approachable", "engine": "deepgram"},
    {"id": "aura-arcas-en", "name": "Arcas", "gender": "Male", "accent": "US", "style": "Deep, Resonant", "engine": "deepgram"},
    {"id": "aura-perseus-en", "name": "Perseus", "gender": "Male", "accent": "US", "style": "Engaging, Articulate", "engine": "deepgram"},
    {"id": "aura-angus-en", "name": "Angus", "gender": "Male", "accent": "Irish", "style": "Rich, Natural", "engine": "deepgram"},
    {"id": "aura-orpheus-en", "name": "Orpheus", "gender": "Male", "accent": "US", "style": "Soothing, Confident", "engine": "deepgram"},
    {"id": "aura-helios-en", "name": "Helios", "gender": "Male", "accent": "UK", "style": "Warm, Articulate", "engine": "deepgram"},
    {"id": "aura-zeus-en", "name": "Zeus", "gender": "Male", "accent": "US", "style": "Commanding, Classic", "engine": "deepgram"},
    # Local offline voices
    {"id": "piper-lessac", "name": "Lessac (Local Piper)", "gender": "Female", "accent": "US", "style": "Offline Fast", "engine": "piper"},
    {"id": "af_bella", "name": "Bella (Local Kokoro)", "gender": "Female", "accent": "US", "style": "Offline Neural", "engine": "kokoro"},
]

ACTIVE_TTS_VOICE = os.getenv("JENNA_TTS_VOICE", "aura-asteria-en")
ACTIVE_TTS_ENGINE = os.getenv("JENNA_TTS_ENGINE", "deepgram" if DEEPGRAM_API_KEY else "piper")

# ─── TTS ──────────────────────────────────────────────────────────────────
TTS_ENGINE = ACTIVE_TTS_ENGINE
PIPER_VOICE_PATH = str(TTS_MODELS_DIR / "en_US-lessac-medium.onnx")
PIPER_CONFIG_PATH = str(TTS_MODELS_DIR / "en_US-lessac-medium.onnx.json")
KOKORO_MODEL_PATH = str(TTS_MODELS_DIR / "kokoro-v1.0.int8.onnx")
KOKORO_VOICES_PATH = str(TTS_MODELS_DIR / "voices-v1.0.bin")
TTS_SPEED = float(os.getenv("JENNA_TTS_SPEED", "1.05"))

# ─── Privacy-Gated Vision Permissions ─────────────────────────────────────
VISION_PERMISSIONS_FILE = MEMORY_DIR / "vision_permissions.json"

def get_vision_permissions() -> dict:
    defaults = {"screen": False, "camera": False}
    if VISION_PERMISSIONS_FILE.exists():
        try:
            with open(VISION_PERMISSIONS_FILE, "r") as f:
                return {**defaults, **json.load(f)}
        except Exception:
            pass
    return defaults

def set_vision_permission(target: str, allowed: bool) -> dict:
    perms = get_vision_permissions()
    perms[target] = bool(allowed)
    try:
        with open(VISION_PERMISSIONS_FILE, "w") as f:
            json.dump(perms, f, indent=2)
    except Exception:
        pass
    return perms

# ─── Hermes & Continuous Learning Paths ───────────────────────────────────
LEARNINGS_FILE = OBSIDIAN_VAULT_PATH / "learnings.md"
EVOLUTION_FILE = OBSIDIAN_VAULT_PATH / "self_evolution.md"

# ─── Wake Word ────────────────────────────────────────────────────────────
WAKE_WORD_ENABLED = os.getenv("JENNA_WAKE_WORD", "true").lower() == "true"
WAKE_WORD_MODEL = str(WAKEWORD_MODELS_DIR / "hey_jenna.onnx")
WAKE_WORD_MEL_PATH = str(WAKEWORD_MODELS_DIR / "melspectrogram.onnx")

# ─── User Profile ─────────────────────────────────────────────────────────
USER_NAME = os.getenv("JENNA_USER_NAME", "Jabs")
ASSISTANT_NAME = os.getenv("JENNA_ASSISTANT_NAME", "Jenna")

# ─── Hotkey ───────────────────────────────────────────────────────────────
if keyboard is None:
    HOTKEY = set()
else:
    # Ctrl + Alt + Space across OSes
    HOTKEY = {keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.Key.space}

# ─── Dashboard & API ──────────────────────────────────────────────────────
DASHBOARD_HOST = os.getenv("JENNA_HOST", "127.0.0.1")
DASHBOARD_PORT = int(os.getenv("JENNA_PORT", "8787"))

# ─── Telephony (AgentPhone) ───────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# ─── Email (AgentMail) ────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_USER = os.getenv("GMAIL_USER", os.getenv("EMAIL_USER", ""))
EMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", os.getenv("EMAIL_PASSWORD", ""))

# ─── Executor Safety ──────────────────────────────────────────────────────
CONFIRM_BEFORE_EXECUTE = os.getenv("JENNA_CONFIRM_EXEC", "false").lower() == "true"
REJECT_DANGEROUS_COMMANDS = True
LOG_COMMANDS = True
HISTORY_FILE = SANDBOX_DIR / "command_history.json"
MAX_HISTORY_SIZE = 100

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"mkfs",
    r"dd\s+if=",
    r">\s*/dev/sda",
    r"format\s+[A-Za-z]:",
    r"del\s+/f\s+/s\s+C:\\",
    r":(){ :\|:& };:",  # Fork bomb
]

# ─── Memory & Storage ─────────────────────────────────────────────────────
MEMORY_DB_PATH = MEMORY_DIR / "memory.db"
LONG_TERM_MEMORY_PATH = MEMORY_DIR / "long_term.json"
CONVERSATION_HISTORY_LIMIT = 8
