"""State management for analyzer runtime."""


state_tracker = {
    "state_seq": [],
    "prev_state": None,
    "curr_state": None,
    "SQUAT_COUNT": 0,
    "angles_during_rep": {"spine": [], "knee": [], "ankle": []},
    "rep_data": [],
    "current_rep_issues": [],
    "current_rep_score": None,
    "show_feedback": False,
    "total_issues": 0,
    "total_compliance": 0,
    "feedback_start_time": None,
    "current_feedback_time": None,
    "pending_rep_analysis": None,
    "llm_feedback": {},
    "spoken_reps": set(),
    "last_llm_call_time": None,
    "latest_llm_feedback": None,
    "feedback_ready": False,
    "session_start_time": None,
    "first_llm_call_made": False,
    "last_rep_sent_to_llm": 0,
}


def reset_state_tracker() -> None:
    """Reset all per-run state in the global state_tracker."""
    state_tracker["state_seq"] = []
    state_tracker["prev_state"] = None
    state_tracker["curr_state"] = None
    state_tracker["SQUAT_COUNT"] = 0
    state_tracker["angles_during_rep"] = {"spine": [], "knee": [], "ankle": []}
    state_tracker["rep_data"] = []
    state_tracker["current_rep_issues"] = []
    state_tracker["current_rep_score"] = None
    state_tracker["show_feedback"] = False
    state_tracker["total_issues"] = 0
    state_tracker["total_compliance"] = 0
    state_tracker["feedback_start_time"] = None
    state_tracker["current_feedback_time"] = None
    state_tracker["pending_rep_analysis"] = None
    state_tracker["llm_feedback"] = {}
    state_tracker["spoken_reps"] = set()
    state_tracker["last_llm_call_time"] = None
    state_tracker["latest_llm_feedback"] = None
    state_tracker["feedback_ready"] = False
    state_tracker["session_start_time"] = None
    state_tracker["first_llm_call_made"] = False
    state_tracker["last_rep_sent_to_llm"] = 0
