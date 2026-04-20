"""Form scoring and compliance evaluation."""


def analyze_form_and_score(max_spine, min_spine, max_knee, max_ankle):
    """Analyze form, return issues/deviations/score with original logic."""
    issues = []
    deviations = {}
    abs_deviations = {
        "bend_forward": 0,
        "bend_backward": 0,
        "shallow_squat": 0,
        "deep_squat": 0,
        "knee_crossing_toe": 0,
    }

    spine_condition = 1
    knee_condition = 1
    ankle_condition = 1

    if min_spine <= 10:
        deviation = 10 - min_spine
        issues.append("Bend forward")
        deviations["bend_forward"] = deviation
        abs_deviations["bend_forward"] = deviation
        spine_condition = (min_spine - 0) / (10 - 0)

    if max_spine >= 40:
        deviation = max_spine - 40
        issues.append("Bend backward")
        deviations["bend_backward"] = deviation
        abs_deviations["bend_backward"] = deviation

        if max_spine > 50:
            spine_condition = 0
        else:
            spine_condition = (50 - max_spine) / (50 - 40)

    if max_knee <= 75:
        deviation = 75 - max_knee
        issues.append("Shallow squat")
        deviations["shallow_squat"] = deviation
        abs_deviations["shallow_squat"] = deviation

        if max_knee < 55:
            knee_condition = 0
        else:
            knee_condition = (max_knee - 55) / (80 - 55)
    elif max_knee >= 90:
        deviation = max_knee - 90
        issues.append("Deep squat")
        deviations["deep_squat"] = deviation
        abs_deviations["deep_squat"] = deviation

        if max_knee > 110:
            knee_condition = 0
        else:
            knee_condition = (110 - max_knee) / (110 - 90)

    if max_ankle >= 35:
        deviation = max_ankle - 35
        issues.append("Knee crossing toe")
        deviations["knee_crossing_toe"] = deviation
        abs_deviations["knee_crossing_toe"] = deviation

        if max_ankle > 40:
            ankle_condition = 0
        else:
            ankle_condition = (40 - max_ankle) / (40 - 35)

    score = (0.45 * spine_condition) + (0.35 * knee_condition) + (0.20 * ankle_condition)
    return issues, deviations, abs_deviations, score, spine_condition, knee_condition, ankle_condition


def check_compliance(current_rep_data, previous_rep_data):
    """Compare current vs previous rep deviations to see improvements."""
    compliances = []
    compliance_count = 0

    curr_abs_dev = current_rep_data["abs_deviations"]
    prev_abs_dev = previous_rep_data["abs_deviations"]

    error_types = ["bend_forward", "bend_backward", "shallow_squat", "deep_squat", "knee_crossing_toe"]
    error_names = {
        "bend_forward": "Bend forward",
        "bend_backward": "Bend backward",
        "shallow_squat": "Shallow squat",
        "deep_squat": "Deep squat",
        "knee_crossing_toe": "Knee crossing toe",
    }

    for error_type in error_types:
        prev_dev = prev_abs_dev[error_type]
        curr_dev = curr_abs_dev[error_type]
        if prev_dev > 0 and curr_dev < prev_dev:
            improvement = prev_dev - curr_dev
            compliances.append(
                {
                    "error": error_names[error_type],
                    "prev_deviation": prev_dev,
                    "curr_deviation": curr_dev,
                    "improvement": improvement,
                }
            )
            compliance_count += 1

    return compliances, compliance_count
