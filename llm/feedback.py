"""Prompt building and LLM feedback generation."""

from typing import Dict

from config import settings
from llm.client import call_ollama


def generate_llm_feedback(last_rep: Dict) -> str:
    """Generate feedback from rep metrics, preserving prompt behavior."""
    if not last_rep:
        return ""

    spine_cond = float(last_rep["spine_cond"])
    knee_cond = float(last_rep["knee_cond"])
    ankle_cond = float(last_rep["ankle_cond"])
    rep_id = last_rep.get("rep", None)
    issues = last_rep.get("form_issues", []) or []
    issues_str = ", ".join(issues) if issues else "None (form looked clean)"

    if settings.PERSONALITY_ADAPTIVE_MODE:
        b01 = {k: v / 10.0 for k, v in settings.BIG5_PERSONALITY.items()}
        prompt = (
            f'""You are a concise squat coach. Given spine, knee, and ankle conditions (0-1), '
            f'Big Five personality traits (0-1), and a list of issues, identify the priority area '
            f'and give 1-2 short cues. Max 18 words."\n\n'
            f'Last rep{f" (rep #{rep_id})" if rep_id is not None else ""}:\n'
            f'Spine : {spine_cond:.2f},Knee : {knee_cond:.2f},Ankle : {ankle_cond:.2f},'
            f'Openness: {b01["openness"]:.1f},Conscientiousness: {b01["conscientiousness"]:.1f},'
            f'Extraversion: {b01["extraversion"]:.1f},Agreeableness: {b01["agreeableness"]:.1f},'
            f'Neuroticism: {b01["neuroticism"]:.1f},issues: {issues_str}\n\n'
        )
    else:
        prompt = (
            f'"You are a concise squat coach. Given spine, knee, and ankle conditions (0-1) and a '
            f'list of issues, identify the priority area and give 1-2 short cues. Max 18 words.\n\n'
            f'Last rep{f" (rep #{rep_id})" if rep_id is not None else ""}:\n'
            f'Spine : {spine_cond:.2f},Knee : {knee_cond:.2f},Ankle : {ankle_cond:.2f},issues: {issues_str}\n\n'
        )
    return call_ollama(prompt)
