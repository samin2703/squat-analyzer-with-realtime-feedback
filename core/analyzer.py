"""Main squat analyzer runtime using OpenCV + MediaPipe."""

import os
import time
import warnings
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np

from config import settings
from core.evaluation import analyze_form_and_score, check_compliance
from core.geometry import calculate_angle, get_state, update_state_sequence
from core.state import reset_state_tracker, state_tracker
from llm.worker import send_rep_to_llm, start_feedback_worker
from utils.drawing import draw_dotted_line
from utils.tts import speak_async

warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf.symbol_database")

mp_pose = mp.solutions.pose


def run_squat_analyzer(video_path: Optional[str] = None):
    """Run analyzer in OpenCV window. Streamlit is control-plane only."""
    reset_state_tracker()
    start_feedback_worker()

    if video_path is None:
        is_live = True
        cap = cv2.VideoCapture(2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1440)

        actual_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"Webcam Initialized. Resolution: {int(actual_w)}x{int(actual_h)}")
        if not cap.isOpened():
            print("Error: Could not open webcam (device 2).")
            return
    else:
        is_live = False
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file: {video_path}")
            return

    cv2.namedWindow(settings.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(settings.WINDOW_NAME, 1280, 720)

    frame_number = 0
    session_start_time = time.time()
    state_tracker["session_start_time"] = session_start_time
    fps = cap.get(cv2.CAP_PROP_FPS) or 0

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_number += 1
            current_wall_time = time.time()
            frame_time = current_wall_time - session_start_time if is_live else (frame_number / fps if fps > 0 else 0)

            if settings.USE_OLLAMA and state_tracker["first_llm_call_made"]:
                elapsed_since_llm = current_wall_time - state_tracker["last_llm_call_time"]
                if elapsed_since_llm >= settings.LLM_INTERVAL_SECONDS and state_tracker["rep_data"]:
                    latest_rep = state_tracker["rep_data"][-1]
                    send_rep_to_llm(latest_rep, frame_time, reason=f"{settings.LLM_INTERVAL_SECONDS}s interval")

            frame_height, frame_width, _ = frame.shape
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark

                left_shoulder = [
                    int(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * frame_width),
                    int(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * frame_height),
                ]
                left_hip = [
                    int(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x * frame_width),
                    int(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y * frame_height),
                ]
                left_knee = [
                    int(landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x * frame_width),
                    int(landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y * frame_height),
                ]
                left_ankle = [
                    int(landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x * frame_width),
                    int(landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y * frame_height),
                ]

                vertical_point_hip = np.array([left_hip[0], 0])
                vertical_point_knee = np.array([left_knee[0], 0])
                vertical_point_ankle = np.array([left_ankle[0], 0])

                spine_angle = calculate_angle(vertical_point_hip, left_hip, left_shoulder)
                knee_angle = calculate_angle(vertical_point_knee, left_knee, left_hip)
                ankle_angle = calculate_angle(vertical_point_ankle, left_ankle, left_knee)

                current_state = get_state(int(knee_angle))
                prev_state = state_tracker["prev_state"]
                state_tracker["curr_state"] = current_state

                if prev_state == "s1" and current_state == "s2":
                    if state_tracker["feedback_start_time"] is not None:
                        feedback_duration = frame_time - state_tracker["feedback_start_time"]
                        state_tracker["current_feedback_time"] = feedback_duration
                        state_tracker["feedback_start_time"] = None

                if current_state == "s1":
                    state_tracker["show_feedback"] = True
                    if (
                        state_tracker["feedback_ready"]
                        and state_tracker["latest_llm_feedback"]
                        and state_tracker["latest_llm_feedback"] not in state_tracker["spoken_reps"]
                    ):
                        speak_async(state_tracker["latest_llm_feedback"])
                        state_tracker["spoken_reps"].add(state_tracker["latest_llm_feedback"])
                        state_tracker["feedback_ready"] = False
                elif current_state in ["s2", "s3"]:
                    state_tracker["show_feedback"] = False

                update_state_sequence(state_tracker, current_state, spine_angle, knee_angle, ankle_angle)

                if prev_state == "s3" and current_state == "s2":
                    angles_rep = state_tracker["angles_during_rep"]
                    if len(angles_rep["spine"]) > 0:
                        max_spine = max(angles_rep["spine"])
                        max_knee = max(angles_rep["knee"])
                        max_ankle = max(angles_rep["ankle"])
                        min_spine = min(angles_rep["spine"])
                        min_knee = min(angles_rep["knee"])
                        min_ankle = min(angles_rep["ankle"])

                        form_issues, deviations, abs_deviations, score, spine_cond, knee_cond, ankle_cond = analyze_form_and_score(
                            max_spine, min_spine, max_knee, max_ankle
                        )
                        issue_count = len(form_issues)
                        rep_index = state_tracker["SQUAT_COUNT"] + 1

                        state_tracker["pending_rep_analysis"] = {
                            "rep": rep_index,
                            "max_spine": max_spine,
                            "max_knee": max_knee,
                            "max_ankle": max_ankle,
                            "min_spine": min_spine,
                            "min_knee": min_knee,
                            "min_ankle": min_ankle,
                            "form_issues": form_issues,
                            "deviations": deviations,
                            "abs_deviations": abs_deviations,
                            "issue_count": issue_count,
                            "score": score,
                            "spine_cond": spine_cond,
                            "knee_cond": knee_cond,
                            "ankle_cond": ankle_cond,
                        }

                if current_state == "s1":
                    if len(state_tracker["state_seq"]) == 3:
                        rep_index = state_tracker["SQUAT_COUNT"] + 1
                        rep_info = state_tracker["pending_rep_analysis"]

                        if rep_info is None or rep_info.get("rep") != rep_index:
                            angles_rep = state_tracker["angles_during_rep"]
                            if len(angles_rep["spine"]) > 0:
                                max_spine = max(angles_rep["spine"])
                                max_knee = max(angles_rep["knee"])
                                max_ankle = max(angles_rep["ankle"])
                                min_spine = min(angles_rep["spine"])
                                min_knee = min(angles_rep["knee"])
                                min_ankle = min(angles_rep["ankle"])
                                form_issues, deviations, abs_deviations, score, spine_cond, knee_cond, ankle_cond = analyze_form_and_score(
                                    max_spine, min_spine, max_knee, max_ankle
                                )
                                rep_info = {
                                    "rep": rep_index,
                                    "max_spine": max_spine,
                                    "max_knee": max_knee,
                                    "max_ankle": max_ankle,
                                    "min_spine": min_spine,
                                    "min_knee": min_knee,
                                    "min_ankle": min_ankle,
                                    "form_issues": form_issues,
                                    "deviations": deviations,
                                    "abs_deviations": abs_deviations,
                                    "issue_count": len(form_issues),
                                    "score": score,
                                    "spine_cond": spine_cond,
                                    "knee_cond": knee_cond,
                                    "ankle_cond": ankle_cond,
                                }

                        if rep_info:
                            state_tracker["SQUAT_COUNT"] = rep_index
                            compliances = []
                            compliance_count = 0
                            feedback_time = None

                            if state_tracker["SQUAT_COUNT"] > 1:
                                previous_rep = state_tracker["rep_data"][-1]
                                current_rep_temp = {"abs_deviations": rep_info["abs_deviations"]}
                                compliances, compliance_count = check_compliance(current_rep_temp, previous_rep)
                                state_tracker["total_compliance"] += compliance_count
                                if state_tracker["current_feedback_time"] is not None:
                                    feedback_time = state_tracker["current_feedback_time"]
                                    state_tracker["current_feedback_time"] = None

                            state_tracker["current_rep_issues"] = rep_info["form_issues"]
                            state_tracker["current_rep_score"] = rep_info["score"]
                            if state_tracker["SQUAT_COUNT"] > 0:
                                state_tracker["feedback_start_time"] = frame_time

                            full_rep_data = {
                                **rep_info,
                                "compliances": compliances,
                                "compliance_count": compliance_count,
                                "feedback_time": feedback_time,
                                "time": frame_time,
                            }
                            state_tracker["rep_data"].append(full_rep_data)
                            state_tracker["total_issues"] += rep_info["issue_count"]

                            if settings.USE_OLLAMA and not state_tracker["first_llm_call_made"]:
                                send_rep_to_llm(full_rep_data, frame_time, reason="first rep")
                                state_tracker["first_llm_call_made"] = True

                            state_tracker["pending_rep_analysis"] = None

                    state_tracker["state_seq"] = []
                    state_tracker["angles_during_rep"] = {"spine": [], "knee": [], "ankle": []}

                state_tracker["prev_state"] = current_state

                draw_dotted_line(
                    image,
                    left_hip,
                    max(0, left_hip[1] - 200),
                    min(frame_height, left_hip[1] + 100),
                    settings.COLORS["blue"],
                )
                draw_dotted_line(
                    image,
                    left_knee,
                    max(0, left_knee[1] - 200),
                    min(frame_height, left_knee[1] + 100),
                    settings.COLORS["blue"],
                )
                draw_dotted_line(
                    image,
                    left_ankle,
                    max(0, left_ankle[1] - 200),
                    min(frame_height, left_ankle[1] + 100),
                    settings.COLORS["blue"],
                )

                spine_multiplier = 1 if left_shoulder[0] > left_hip[0] else -1
                knee_multiplier = 1 if left_hip[0] > left_knee[0] else -1
                ankle_multiplier = 1 if left_knee[0] > left_ankle[0] else -1

                cv2.ellipse(
                    image,
                    tuple(left_hip),
                    (40, 40),
                    angle=0,
                    startAngle=-90,
                    endAngle=-90 + spine_multiplier * int(spine_angle),
                    color=settings.COLORS["white"],
                    thickness=6,
                )
                cv2.ellipse(
                    image,
                    tuple(left_knee),
                    (40, 40),
                    angle=0,
                    startAngle=-90,
                    endAngle=-90 + knee_multiplier * int(knee_angle),
                    color=settings.COLORS["white"],
                    thickness=6,
                )
                cv2.ellipse(
                    image,
                    tuple(left_ankle),
                    (40, 40),
                    angle=0,
                    startAngle=-90,
                    endAngle=-90 + ankle_multiplier * int(ankle_angle),
                    color=settings.COLORS["white"],
                    thickness=6,
                )

                cv2.line(image, tuple(left_hip), tuple(left_shoulder), settings.COLORS["light_blue"], 10)
                cv2.line(image, tuple(left_hip), tuple(left_knee), settings.COLORS["light_blue"], 10)
                cv2.line(image, tuple(left_knee), tuple(left_ankle), settings.COLORS["light_blue"], 10)

                cv2.circle(image, tuple(left_shoulder), 10, settings.COLORS["yellow"], -1)
                cv2.circle(image, tuple(left_hip), 10, settings.COLORS["yellow"], -1)
                cv2.circle(image, tuple(left_knee), 10, settings.COLORS["yellow"], -1)
                cv2.circle(image, tuple(left_ankle), 10, settings.COLORS["yellow"], -1)

                cv2.putText(image, f"{int(spine_angle)}", (left_hip[0] + 15, left_hip[1]), cv2.FONT_HERSHEY_TRIPLEX, 2.5, settings.COLORS["green"], 6)
                cv2.putText(image, f"{int(knee_angle)}", (left_knee[0] + 15, left_knee[1]), cv2.FONT_HERSHEY_TRIPLEX, 2.5, settings.COLORS["green"], 6)
                cv2.putText(image, f"{int(ankle_angle)}", (left_ankle[0] + 15, left_ankle[1]), cv2.FONT_HERSHEY_TRIPLEX, 2.5, settings.COLORS["green"], 6)

                cv2.putText(image, f"SPINE: {int(spine_angle)}", (30, 60), cv2.FONT_HERSHEY_TRIPLEX, 2, settings.COLORS["white"], 2)
                cv2.putText(image, f"KNEE: {int(knee_angle)}", (30, 140), cv2.FONT_HERSHEY_TRIPLEX, 2, settings.COLORS["white"], 2)
                cv2.putText(image, f"ANKLE: {int(ankle_angle)}", (30, 220), cv2.FONT_HERSHEY_TRIPLEX, 2, settings.COLORS["white"], 2)
                cv2.putText(image, f"REPS: {state_tracker['SQUAT_COUNT']}", (30, 300), cv2.FONT_HERSHEY_TRIPLEX, 2, settings.COLORS["cyan"], 4)

                state_name_map = {"s1": "STANDING", "s2": "TRANSITION", "s3": "SQUAT"}
                state_display = state_name_map.get(current_state, "UNKNOWN")
                state_color = settings.COLORS["green"] if current_state == "s3" else settings.COLORS["white"]
                cv2.putText(image, f"STATE: {state_display}", (30, 380), cv2.FONT_HERSHEY_TRIPLEX, 2, state_color, 2)

                if state_tracker["show_feedback"] and state_tracker["SQUAT_COUNT"] > 0:
                    right_x = frame_width - 1000
                    cv2.putText(image, " Suggestions:", (right_x, 40), cv2.FONT_HERSHEY_TRIPLEX, 2, settings.COLORS["orange"], 4)

                    if state_tracker["current_rep_issues"]:
                        y_offset = 140
                        for issue in state_tracker["current_rep_issues"]:
                            hint = settings.ISSUE_HINTS.get(issue, issue)
                            cv2.putText(image, f"- {hint}", (right_x, y_offset), cv2.FONT_HERSHEY_TRIPLEX, 2.5, settings.COLORS["red"], 6)
                            y_offset += 100
                    else:
                        cv2.putText(image, "Good form!", (right_x, 140), cv2.FONT_HERSHEY_TRIPLEX, 2.5, settings.COLORS["green"], 6)

                    if state_tracker["current_rep_score"] is not None:
                        score = state_tracker["current_rep_score"]
                        if score >= 0.8:
                            score_color = settings.COLORS["green"]
                        elif score >= 0.5:
                            score_color = settings.COLORS["yellow"]
                        else:
                            score_color = settings.COLORS["red"]
                        cv2.putText(image, f"SCORE: {score:.2f}", (right_x - 100, 500), cv2.FONT_HERSHEY_TRIPLEX, 3.5, score_color, 10)

            except Exception:
                cv2.putText(image, "No pose detected", (30, 60), cv2.FONT_HERSHEY_TRIPLEX, 2, settings.COLORS["red"], 2)

            cv2.imshow(settings.WINDOW_NAME, image)
            if cv2.waitKey(10) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()
    _print_and_save_summary()


def _print_and_save_summary() -> None:
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total Reps: {state_tracker['SQUAT_COUNT']}")
    print(f"Mode: {'Personality Adaptive (squatper)' if settings.PERSONALITY_ADAPTIVE_MODE else 'Generic (squat-coach)'}")

    if len(state_tracker["rep_data"]) > 0:
        last_rep_issues = state_tracker["rep_data"][-1]["issue_count"]
        adjusted_total_issues = state_tracker["total_issues"] - last_rep_issues
    else:
        adjusted_total_issues = 0

    print(f"Total Issues (excluding last rep): {adjusted_total_issues}")
    print(f"Total Compliance: {state_tracker['total_compliance']}")

    feedback_times = [r["feedback_time"] for r in state_tracker["rep_data"] if r.get("feedback_time") is not None]
    if feedback_times:
        print(f"Average Feedback Viewing Time: {np.mean(feedback_times):.2f}s\n")
    else:
        print("Average Feedback Viewing Time: N/A\n")

    if state_tracker["rep_data"]:
        avg_score = np.mean([r["score"] for r in state_tracker["rep_data"]])
        print(f"Average Score: {avg_score:.2f}")

    if settings.PERSONALITY_ADAPTIVE_MODE and settings.PARTICIPANT_NAME and state_tracker["rep_data"]:
        scores = [r["score"] for r in state_tracker["rep_data"]]
        avg_score = float(np.mean(scores)) if scores else 0.0
        total_issues = adjusted_total_issues
        total_compliance = state_tracker["total_compliance"]
        avg_feedback_time = float(np.mean(feedback_times)) if feedback_times else None

        os.makedirs("records", exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in settings.PARTICIPANT_NAME).strip()
        if not safe_name:
            safe_name = "participant"

        filepath = os.path.join("records", f"{safe_name}.txt")
        lines = [
            f"Participant: {settings.PARTICIPANT_NAME}",
            "Mode: Personality Adaptive (squatper)",
            f"Total Reps: {state_tracker['SQUAT_COUNT']}",
            f"Average Score: {avg_score:.4f}",
            f"Total Issues (excluding last rep): {total_issues}",
            f"Total Compliance: {total_compliance}",
            f"Average Feedback Processing Time: {avg_feedback_time:.4f} s" if avg_feedback_time is not None else "Average Feedback Processing Time: N/A",
            f"Session End Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"Session summary saved to: {filepath}")
        except Exception as e:
            print(f"Could not write summary file ({filepath}): {e}")

    print("=" * 60)
