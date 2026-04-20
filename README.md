# Squat Form Analyzer with Feedback

Real-time squat form analysis using pose estimation, rule-based evaluation, and optional LLM-generated coaching feedback.

## Features

- Real-time squat tracking from webcam or uploaded video.
- Rep counting with posture-state transitions.
- Form checks for spine, knee, and ankle alignment.
- Rule-based coaching suggestions.
- Optional personality-adaptive feedback using Ollama.
- Optional text-to-speech playback for feedback.

## Project Structure

```
.
|-- app.py                  # Streamlit UI
|-- app_flet.py             # Flet UI
|-- main.py                 # Launch/entry glue
|-- config/
|   `-- settings.py         # Runtime settings and thresholds
|-- core/
|   |-- analyzer.py         # Main analysis loop
|   |-- evaluation.py       # Scoring and compliance logic
|   |-- geometry.py         # Angle/state calculations
|   `-- state.py            # Shared runtime state tracker
|-- data/
|   `-- personality.py      # Big Five data loading/helpers
|-- llm/
|   |-- client.py           # Ollama HTTP client
|   |-- feedback.py         # Prompt and feedback generation
|   `-- worker.py           # Background LLM worker queue
|-- models/
|   |-- model/
|   `-- Modelfile
|-- utils/
|   |-- drawing.py
|   `-- tts.py
`-- records/                # Session summary outputs
```

## Requirements

- Python 3.10+
- Webcam (for live mode)
- Ollama (optional, for LLM feedback)

## Installation

```bash
pip install -r requirements.txt
```

## Run

### Streamlit UI

```bash
streamlit run app.py
```

### Flet UI

```bash
flet run app_flet.py
```

### CLI Mode

```bash
python main.py
```

## Configuration

Core runtime settings are in `config/settings.py`.

- Toggle LLM feedback.
- Toggle TTS output.
- Adjust thresholds/colors/window behavior.

## Media Placeholders

Use the sections below to add visual assets when publishing.

### Interface Images

<!-- Add interface screenshots below -->

![Interface Image 1](interface.png)
![Interface Image 2](interface-2.png)

### Demo Images

<!-- Add demo images below -->

![Demo Image 1](demo-1.jpg)
![Demo Image 2](demo-2.jpg)

### Demo Video

<!-- Add demo video link or embedded preview below -->

Demo video: [Watch demo video](demo-video.MOV)

[![Watch demo](demo-1.jpg)](demo-video.MOV)

## Notes

- Personality-adaptive mode expects `res_out.csv` with the required scaled Big Five columns.
- Session summaries are written to `records/`.

## License

This project is licensed under the MIT License. See `LICENSE`.
