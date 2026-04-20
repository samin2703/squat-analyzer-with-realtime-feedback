"""Ollama API client."""

import time

import requests

from config import settings
from core.state import state_tracker


def call_ollama(prompt: str) -> str:
    if not settings.USE_OLLAMA:
        return ""

    call_time = time.time()
    start = state_tracker.get("session_start_time")
    t_from_start = call_time - start if start is not None else 0.0
    print(f"[{t_from_start:.1f}s] LLM HTTP call started")

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 100},
    }

    try:
        resp = requests.post(settings.OLLAMA_URL, json=payload, timeout=settings.OLLAMA_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except Exception as e:
        print(f"[Ollama error] {e}")
        return ""
