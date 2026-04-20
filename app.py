"""Streamlit control panel for squat analyzer.

Important: Video is rendered in OpenCV window (cv2.imshow), not Streamlit.
"""

import streamlit as st

from data.personality import get_participant_names
from main import launch_analyzer


st.set_page_config(page_title="Squat Form Analyzer", layout="wide")

st.sidebar.header("Controls")
source = st.sidebar.selectbox("Input source", ["Webcam", "Upload Video"])
mode = st.sidebar.selectbox("Mode", ["Generic", "Personality Adaptive"])
use_ollama = st.sidebar.toggle("Enable LLM", value=True)
use_tts = st.sidebar.toggle("Enable TTS", value=True)

participant_name = None
if mode == "Personality Adaptive":
    names = get_participant_names("res_out.csv")
    if names:
        participant_name = st.sidebar.selectbox("Participant (from res_out.csv)", names)
    else:
        st.sidebar.warning("Could not load participant names from res_out.csv")
    manual_name = st.sidebar.text_input("Or type participant name", value="").strip()
    if manual_name:
        participant_name = manual_name

uploaded_file = None
if source == "Upload Video":
    uploaded_file = st.sidebar.file_uploader("Upload video", type=["mp4", "avi", "mov", "mkv"])

st.title("Squat Form Analyzer")
st.write("Use Start to launch the analyzer. Live video will open in a separate OpenCV window.")

if st.button("Start", type="primary"):
    if source == "Upload Video" and uploaded_file is None:
        st.error("Please upload a video file before starting.")
    else:
        with st.spinner("Launching analyzer in OpenCV window..."):
            try:
                launch_analyzer(
                    mode=mode,
                    source=source,
                    uploaded_video_bytes=uploaded_file.read() if uploaded_file else None,
                    uploaded_video_name=uploaded_file.name if uploaded_file else None,
                    participant_name=participant_name,
                    use_ollama=use_ollama,
                    use_tts=use_tts,
                )
                st.success("Analyzer session ended.")
            except Exception as e:
                st.error(f"Failed to start analyzer: {e}")
