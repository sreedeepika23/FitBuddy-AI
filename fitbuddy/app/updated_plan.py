"""
Feedback-based plan revision.

Function: update_workout_plan()

Takes the user's original 7-day plan plus free-text feedback (e.g. "add
more cardio", "include more rest days") and asks Gemini Pro to return a
revised plan that respects the feedback while keeping the same overall
structure (Day 1 - Day 7).
"""

import os

from google.genai import types

from app.ai_client import get_client

PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")


def _build_update_prompt(original_plan: str, feedback: str) -> str:
    return f"""You are FitBuddy, an encouraging certified personal trainer.

Here is a user's current 7-day workout plan:
---
{original_plan}
---

The user has given the following feedback about this plan:
"{feedback}"

Revise the plan to incorporate this feedback while keeping the same
overall 7-day structure (Day 1 through Day 7, with a warm-up, main
workout, and cooldown for each workout day). Keep at least one rest or
active-recovery day unless the feedback explicitly says otherwise.

Format the response as plain text using clear headings like "Day 1: ..."
Do not use markdown tables. Do not include any commentary before Day 1
or after Day 7 - return only the revised plan.
"""


def update_workout_plan(original_plan: str, feedback: str) -> str:
    """Call Gemini Pro to revise a workout plan based on user feedback."""
    client = get_client()
    prompt = _build_update_prompt(original_plan, feedback)

    try:
        response = client.models.generate_content(
            model=PRO_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1500,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise ValueError("Empty response from Gemini")
        return text
    except Exception as exc:  # noqa: BLE001 - surface a friendly fallback
        return (
            "We couldn't update your plan right now "
            f"({exc}). Please check your GOOGLE_API_KEY and try again."
        )
