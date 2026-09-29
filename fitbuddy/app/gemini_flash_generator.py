"""
Nutrition / recovery tip generation powered by a Gemini "Flash"-tier model.

Function: generate_nutrition_tip_with_flash()

Flash is used here (rather than Pro) because a nutrition tip is a short,
low-latency, low-complexity generation - a good fit for a fast, lightweight
model, and it keeps the two AI calls in /generate-workout running against
different model tiers as described in the project spec.
"""

import os

from google.genai import types

from app.ai_client import get_client

# The spec calls for "Gemini Flash". Defaults to a current Flash-tier
# model; override with GEMINI_FLASH_MODEL in .env if needed.
FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")


def _build_nutrition_prompt(goal: str) -> str:
    return f"""You are FitBuddy, a concise fitness and nutrition coach.

Give ONE short, practical nutrition or recovery tip (2-3 sentences max)
for someone whose fitness goal is: "{goal}".

Be specific and actionable (e.g. name food sources, timing, or a recovery
habit). Do not use markdown formatting, headings, or bullet points -
return plain sentences only.
"""


def generate_nutrition_tip_with_flash(goal: str) -> str:
    """Call Gemini Flash to generate a short nutrition/recovery tip."""
    client = get_client()
    prompt = _build_nutrition_prompt(goal)

    try:
        response = client.models.generate_content(
            model=FLASH_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.6,
                max_output_tokens=200,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise ValueError("Empty response from Gemini")
        return text
    except Exception as exc:  # noqa: BLE001 - surface a friendly fallback
        return f"Nutrition tip unavailable right now ({exc})."
