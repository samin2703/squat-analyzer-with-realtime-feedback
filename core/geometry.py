"""Geometry and movement-state helpers."""

import numpy as np

from config.settings import THRESHOLDS


def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle


def get_state(knee_angle):
    knee = None
    if THRESHOLDS["HIP_KNEE_VERT"]["NORMAL"][0] <= knee_angle <= THRESHOLDS["HIP_KNEE_VERT"]["NORMAL"][1]:
        knee = 1
    elif THRESHOLDS["HIP_KNEE_VERT"]["TRANS"][0] <= knee_angle <= THRESHOLDS["HIP_KNEE_VERT"]["TRANS"][1]:
        knee = 2
    elif THRESHOLDS["HIP_KNEE_VERT"]["PASS"][0] <= knee_angle <= THRESHOLDS["HIP_KNEE_VERT"]["PASS"][1]:
        knee = 3
    return f"s{knee}" if knee else None


def update_state_sequence(state_tracker, state, spine_angle, knee_angle, ankle_angle):
    if state in ["s2", "s3"]:
        state_tracker["angles_during_rep"]["spine"].append(spine_angle)
        state_tracker["angles_during_rep"]["knee"].append(knee_angle)
        state_tracker["angles_during_rep"]["ankle"].append(ankle_angle)

    if state == "s2":
        if (("s3" not in state_tracker["state_seq"]) and (state_tracker["state_seq"].count("s2") == 0)) or (
            ("s3" in state_tracker["state_seq"]) and (state_tracker["state_seq"].count("s2") == 1)
        ):
            state_tracker["state_seq"].append(state)

    elif state == "s3":
        if (state not in state_tracker["state_seq"]) and "s2" in state_tracker["state_seq"]:
            state_tracker["state_seq"].append(state)
