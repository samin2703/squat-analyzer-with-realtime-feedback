"""Background worker for async LLM requests."""

import threading
import time
from queue import Queue
from typing import Dict

from config import settings
from core.state import state_tracker
from llm.feedback import generate_llm_feedback


llm_queue: "Queue[Dict]" = Queue()
_worker_started = False


def feedback_worker():
    """Worker thread that processes last-rep summaries."""
    while True:
        last_rep = llm_queue.get()
        try:
            if not settings.USE_OLLAMA or not last_rep:
                continue
            text = generate_llm_feedback(last_rep)
            if text:
                state_tracker["latest_llm_feedback"] = text
                state_tracker["feedback_ready"] = True
                print(f"[LLM Feedback Ready]: {text}\n")
        finally:
            llm_queue.task_done()


def start_feedback_worker() -> None:
    global _worker_started
    if _worker_started:
        return
    threading.Thread(target=feedback_worker, daemon=True).start()
    _worker_started = True


def send_rep_to_llm(rep_data: Dict, frame_time: float, reason: str = ""):
    """Send rep to LLM queue and update scheduling markers."""
    if not settings.USE_OLLAMA or not rep_data:
        return

    rep_num = rep_data.get("rep", 0)
    if rep_num == state_tracker["last_rep_sent_to_llm"]:
        print(f"[{frame_time:.1f}s] Rep #{rep_num} already sent to LLM, skipping duplicate.")
        return

    llm_queue.put(rep_data)
    state_tracker["last_llm_call_time"] = time.time()
    state_tracker["last_rep_sent_to_llm"] = rep_num

    reason_str = f" ({reason})" if reason else ""
    print(f"\n[{frame_time:.1f}s] Sending Rep #{rep_num} to LLM{reason_str}...")
