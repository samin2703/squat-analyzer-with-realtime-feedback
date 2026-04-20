"""Flet control panel for squat analyzer.

Run in dev mode:
    flet dev app_flet.py

Note: Video still renders in the OpenCV window (cv2.imshow).
"""

from pathlib import Path
from typing import Optional

import flet as ft

from data.personality import get_participant_names
from main import launch_analyzer


CSV_PATH = "res_out.csv"


def _build_badge(label: str, value_control: ft.Control) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Text(label, size=12, color=ft.Colors.BLUE_GREY_700),
                value_control,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        bgcolor=ft.Colors.WHITE,
    )


def main(page: ft.Page) -> None:
    page.title = "Squat Form Analyzer"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window_min_width = 860
    page.window_min_height = 680
    page.scroll = ft.ScrollMode.AUTO
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        font_family="Segoe UI",
    )

    state = {
        "running": False,
        "selected_video_path": None,
    }

    status_value = ft.Text("Idle", size=13, color=ft.Colors.BLUE_GREY_900, weight=ft.FontWeight.W_600)
    source_value = ft.Text("Webcam", size=13, color=ft.Colors.BLUE_GREY_900, weight=ft.FontWeight.W_600)
    mode_value = ft.Text("Generic", size=13, color=ft.Colors.BLUE_GREY_900, weight=ft.FontWeight.W_600)

    selected_file_text = ft.Text(
        "No video selected",
        size=12,
        color=ft.Colors.BLUE_GREY_600,
        italic=True,
    )

    activity_ring = ft.ProgressRing(width=20, height=20, stroke_width=2.5, visible=False)

    mode_dropdown = ft.Dropdown(
        label="Mode",
        value="Generic",
        options=[
            ft.dropdown.Option("Generic"),
            ft.dropdown.Option("Personality Adaptive"),
        ],
        expand=True,
    )

    source_dropdown = ft.Dropdown(
        label="Input Source",
        value="Webcam",
        options=[
            ft.dropdown.Option("Webcam"),
            ft.dropdown.Option("Upload Video"),
        ],
        expand=True,
    )

    llm_switch = ft.Switch(label="Enable LLM", value=True)
    tts_switch = ft.Switch(label="Enable TTS", value=True)

    participant_dropdown = ft.Dropdown(
        label="Participant (from res_out.csv)",
        options=[],
        visible=False,
        expand=True,
    )

    manual_name_field = ft.TextField(
        label="Or type participant name",
        hint_text="Optional override",
        visible=False,
        expand=True,
    )

    personality_hint = ft.Text(
        "",
        size=12,
        color=ft.Colors.BLUE_GREY_600,
        visible=False,
    )

    def show_message(text: str, color: str = ft.Colors.BLUE_GREY_900) -> None:
        page.snack_bar = ft.SnackBar(content=ft.Text(text, color=color), open=True)
        page.update()

    def refresh_participants() -> None:
        names = get_participant_names(CSV_PATH)
        participant_dropdown.options = [ft.dropdown.Option(name) for name in names]

        if names:
            if participant_dropdown.value not in names:
                participant_dropdown.value = names[0]
            personality_hint.value = f"Loaded {len(names)} participant(s) from {CSV_PATH}."
            personality_hint.color = ft.Colors.GREEN_700
        else:
            participant_dropdown.value = None
            personality_hint.value = (
                f"No participants found in {CSV_PATH}. You can still type a name manually."
            )
            personality_hint.color = ft.Colors.ORANGE_700

    def sync_visibility() -> None:
        is_upload = source_dropdown.value == "Upload Video"
        is_personality = mode_dropdown.value == "Personality Adaptive"

        choose_video_btn.visible = is_upload
        selected_file_text.visible = is_upload

        participant_dropdown.visible = is_personality
        manual_name_field.visible = is_personality
        refresh_names_btn.visible = is_personality
        personality_hint.visible = is_personality

        source_value.value = source_dropdown.value or "-"
        mode_value.value = mode_dropdown.value or "-"

        if is_personality:
            refresh_participants()

        page.update()

    def on_file_result(e: ft.FilePickerResultEvent) -> None:
        if not e.files:
            return

        picked = e.files[0]
        state["selected_video_path"] = picked.path
        selected_file_text.value = f"Selected: {Path(picked.path).name}"
        selected_file_text.color = ft.Colors.BLUE_GREY_800
        selected_file_text.italic = False
        page.update()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    def on_choose_video(_: ft.ControlEvent) -> None:
        file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["mp4", "avi", "mov", "mkv"],
            dialog_title="Choose a video file",
        )

    choose_video_btn = ft.OutlinedButton(
        "Choose Video",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=on_choose_video,
        visible=False,
    )

    def on_refresh_names(_: ft.ControlEvent) -> None:
        refresh_participants()
        page.update()
        show_message("Participant list refreshed.")

    refresh_names_btn = ft.TextButton(
        "Refresh Names",
        icon=ft.Icons.REFRESH,
        on_click=on_refresh_names,
        visible=False,
    )

    def on_mode_or_source_change(_: ft.ControlEvent) -> None:
        sync_visibility()

    mode_dropdown.on_change = on_mode_or_source_change
    source_dropdown.on_change = on_mode_or_source_change

    def on_start(_: ft.ControlEvent) -> None:
        if state["running"]:
            return

        source = source_dropdown.value or "Webcam"
        mode = mode_dropdown.value or "Generic"

        selected_path: Optional[str] = state["selected_video_path"]
        if source == "Upload Video" and not selected_path:
            show_message("Please choose a video file before starting.", color=ft.Colors.RED_800)
            return

        participant_name = None
        if mode == "Personality Adaptive":
            typed = manual_name_field.value.strip() if manual_name_field.value else ""
            participant_name = typed or participant_dropdown.value

        uploaded_bytes = None
        uploaded_name = None
        if source == "Upload Video" and selected_path:
            try:
                uploaded_bytes = Path(selected_path).read_bytes()
                uploaded_name = Path(selected_path).name
            except OSError as exc:
                show_message(f"Could not read selected file: {exc}", color=ft.Colors.RED_800)
                return

        state["running"] = True
        start_btn.disabled = True
        activity_ring.visible = True
        status_value.value = "Running"
        page.update()

        try:
            launch_analyzer(
                mode=mode,
                source=source,
                uploaded_video_bytes=uploaded_bytes,
                uploaded_video_name=uploaded_name,
                participant_name=participant_name,
                use_ollama=llm_switch.value,
                use_tts=tts_switch.value,
            )
            show_message("Analyzer session ended.", color=ft.Colors.GREEN_800)
        except Exception as exc:  # noqa: BLE001 - surface backend failure in UI
            show_message(f"Failed to start analyzer: {exc}", color=ft.Colors.RED_800)
        finally:
            state["running"] = False
            start_btn.disabled = False
            activity_ring.visible = False
            status_value.value = "Idle"
            page.update()

    start_btn = ft.ElevatedButton(
        text="Start Analyzer",
        icon=ft.Icons.PLAY_CIRCLE,
        on_click=on_start,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.padding.symmetric(horizontal=24, vertical=14),
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
        ),
    )

    hero = ft.Container(
        content=ft.Column(
            [
                ft.Text("Squat Form Analyzer", size=34, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                ft.Text(
                    "A cleaner control panel for launching webcam and uploaded-video analysis.",
                    size=14,
                    color=ft.Colors.WHITE70,
                ),
            ],
            spacing=6,
        ),
        padding=28,
        border_radius=18,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.Colors.BLUE_900, ft.Colors.CYAN_700],
        ),
    )

    status_row = ft.ResponsiveRow(
        [
            ft.Container(content=_build_badge("Status", status_value), col={"xs": 12, "md": 4}),
            ft.Container(content=_build_badge("Source", source_value), col={"xs": 12, "md": 4}),
            ft.Container(content=_build_badge("Mode", mode_value), col={"xs": 12, "md": 4}),
        ],
        run_spacing=12,
    )

    controls_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Session Controls", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_GREY_900),
                ft.Row([source_dropdown, mode_dropdown], spacing=14),
                ft.Row([llm_switch, tts_switch], spacing=24),
                ft.Divider(height=14),
                ft.Row([participant_dropdown, manual_name_field], spacing=14),
                ft.Row([refresh_names_btn], alignment=ft.MainAxisAlignment.START),
                personality_hint,
                ft.Divider(height=14),
                ft.Row([choose_video_btn], alignment=ft.MainAxisAlignment.START),
                selected_file_text,
            ],
            spacing=10,
        ),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=16,
        border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
    )

    start_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Run Analyzer", size=18, weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_GREY_900),
                ft.Text(
                    "When started, live video feedback appears in a separate OpenCV window.",
                    size=12,
                    color=ft.Colors.BLUE_GREY_600,
                ),
                ft.Row([start_btn, activity_ring], spacing=14),
            ],
            spacing=12,
        ),
        padding=20,
        bgcolor=ft.Colors.WHITE,
        border_radius=16,
        border=ft.border.all(1, ft.Colors.BLUE_GREY_100),
    )

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    hero,
                    status_row,
                    controls_card,
                    start_card,
                ],
                spacing=16,
            ),
            padding=ft.padding.symmetric(horizontal=24, vertical=20),
            bgcolor=ft.Colors.BLUE_GREY_50,
        )
    )

    sync_visibility()


if __name__ == "__main__":
    ft.app(target=main)
