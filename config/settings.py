"""Global runtime settings and constants for squat analyzer."""

from typing import Dict, Optional

# ===================== CONFIG (LLM + TTS) =====================
USE_OLLAMA = True
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TIMEOUT = 30

USE_TTS = True
TTS_RATE = 170
TTS_VOLUME = 1.0
TTS_VOICE_INDEX = 1

LLM_INTERVAL_SECONDS = 2
WINDOW_NAME = "Squat Form Analyzer"

# ===================== MODE CONFIGURATION =====================
PERSONALITY_ADAPTIVE_MODE = False
OLLAMA_MODEL = "squat-coach"

# ===================== BIG FIVE PERSONALITY CONFIG =====================
BIG5_PERSONALITY: Dict[str, float] = {
    "openness": 5.0,
    "conscientiousness": 5.0,
    "extraversion": 5.0,
    "agreeableness": 5.0,
    "neuroticism": 5.0,
}
PARTICIPANT_NAME: Optional[str] = None

# Color definitions
COLORS = {
    "blue": (255, 127, 0),
    "red": (50, 50, 255),
    "green": (127, 255, 0),
    "light_green": (127, 233, 100),
    "yellow": (0, 255, 255),
    "magenta": (255, 0, 255),
    "white": (255, 255, 255),
    "cyan": (255, 255, 0),
    "light_blue": (255, 200, 100),
    "orange": (0, 165, 255),
}

# Thresholds
THRESHOLDS = {
    "HIP_KNEE_VERT": {
        "NORMAL": [0, 30],
        "TRANS": [30, 50],
        "PASS": [50, 100],
    }
}

ISSUE_HINTS = {
    "Bend forward": "Bend forward",
    "Bend backward": "Bend backward",
    "Shallow squat": "go deeper",
    "Deep squat": "less deeper",
    "Knee crossing toe": "control knee position",
}


def set_mode(mode: str) -> None:
    """Set runtime mode and corresponding Ollama model."""
    global PERSONALITY_ADAPTIVE_MODE, OLLAMA_MODEL
    if mode == "Personality Adaptive":
        PERSONALITY_ADAPTIVE_MODE = True
        OLLAMA_MODEL = "squatper"
    else:
        PERSONALITY_ADAPTIVE_MODE = False
        OLLAMA_MODEL = "squat-coach"


def set_runtime_flags(use_ollama: bool, use_tts: bool) -> None:
    """Set feature toggles controlled by UI."""
    global USE_OLLAMA, USE_TTS
    USE_OLLAMA = bool(use_ollama)
    USE_TTS = bool(use_tts)
