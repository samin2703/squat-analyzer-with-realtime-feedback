"""Entry-point glue between Streamlit controls and analyzer backend."""

import os
import tempfile
from typing import Optional

from config import settings
from core.analyzer import run_squat_analyzer
from data.personality import load_big5_from_csv


def launch_analyzer(
    mode: str,
    source: str,
    uploaded_video_bytes: Optional[bytes] = None,
    uploaded_video_name: Optional[str] = None,
    participant_name: Optional[str] = None,
    use_ollama: bool = True,
    use_tts: bool = True,
    interactive_personality_input: bool = False,
):
    """Set runtime config from UI, prepare input source, then run analyzer."""
    settings.set_mode(mode)
    settings.set_runtime_flags(use_ollama, use_tts)

    video_path = None
    temp_path = None

    if source == "Upload Video":
        if not uploaded_video_bytes:
            raise ValueError("Upload Video selected, but no file was provided.")
        suffix = os.path.splitext(uploaded_video_name or "uploaded.mp4")[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_video_bytes)
            temp_path = tmp.name
        video_path = temp_path

    if settings.PERSONALITY_ADAPTIVE_MODE:
        # Streamlit can pass participant_name directly; CLI flow can enable interactive prompt.
        load_big5_from_csv(
            csv_path="res_out.csv",
            participant_name=participant_name,
            interactive=interactive_personality_input,
        )

    try:
        run_squat_analyzer(video_path=video_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def _run_cli() -> None:
    """CLI entry for terminal usage (kept separate from Streamlit app flow)."""
    while True:
        print("Select mode:")
        print("1. Personality Adaptive")
        print("2. Generic")
        mode_choice = input("Enter 1 or 2: ").strip()
        if mode_choice == "1":
            mode = "Personality Adaptive"
            break
        if mode_choice == "2":
            mode = "Generic"
            break
        print("Invalid choice. Please enter 1 or 2.")

    launch_analyzer(
        mode=mode,
        source="Webcam",
        use_ollama=True,
        use_tts=True,
        interactive_personality_input=True,
    )


if __name__ == "__main__":
    _run_cli()
