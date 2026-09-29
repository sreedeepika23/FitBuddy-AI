"""
Workout plan generation powered by a Gemini "Pro"-tier model.

Function: generate_workout_gemini()

Builds a structured prompt from the user's profile (goal + intensity,
plus age/weight for context) and asks Gemini for a 7-day, day-by-day
workout plan that includes a warm-up, main workout, and cooldown for
each day. The plan is returned as plain text so it can be dropped
straight into a <pre> block in result.html.
"""

import os

from google import genai
from google.genai import types

from app.ai_client import get_client

# The project spec calls for "Gemini 1.5 Pro". That model line has since
# been retired in favor of newer Gemini releases, so the model name is
# read from the environment and defaults to a current Pro-tier model.
# Override GEMINI_PRO_MODEL in your .env file if Google renames/retires
# this model again.
PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")


def _build_workout_prompt(username: str, age: int, weight: float, goal: str, intensity: str) -> str:
    return f"""You are FitBuddy, an encouraging certified personal trainer.

Create a personalized 7-day workout plan for the following person:
- Name: {username}
- Age: {age}
- Weight: {weight} kg
- Fitness goal: {goal}
- Preferred workout intensity: {intensity}

Requirements:
- Cover Day 1 through Day 7. Include at least one rest or active-recovery day.
- For each day, give a short focus label (e.g. "Full Body", "Upper Body",
  "Cardio", "Core & Flexibility", "Rest / Active Recovery").
- For each workout day include:
    1) A brief warm-up (5-10 minutes)
    2) The main workout as a list of exercises with sets, reps (or duration),
       and rest intervals
    3) A short cooldown / stretching note
- Keep the tone motivating but concise.
- Format the response as plain text using clear headings like "Day 1: ..."
  followed by indented details. Do not use markdown tables. Do not include
  any extra commentary before Day 1 or after Day 7.
"""


def generate_workout_gemini(username: str, age: int, weight: float, goal: str, intensity: str) -> str:
    """Call Gemini Pro to generate a structured 7-day workout plan."""
    client = get_client()
    prompt = _build_workout_prompt(username, age, weight, goal, intensity)

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
            "We couldn't reach the AI workout generator right now "
            f"({exc}). Please check your GOOGLE_API_KEY and try again."
        )
