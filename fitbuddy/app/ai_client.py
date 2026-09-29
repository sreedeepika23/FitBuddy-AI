"""
Shared Google Gemini client factory.

FitBuddy is built on Google's current unified `google-genai` SDK
(`pip install google-genai`). The project's original spec referenced the
older `google-generativeai` package, which Google has since deprecated in
favor of this one — the usage pattern is very similar, so this is a
drop-in modernization.

All Gemini calls in the app (gemini_generator.py, gemini_flash_generator.py,
updated_plan.py) go through get_client() so there is a single place that
reads the API key and configures the client.
"""

import os
from functools import lru_cache

from google import genai


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Return a cached Gemini client built from the GOOGLE_API_KEY env var."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to your .env file "
            "(see .env.example) before starting the server."
        )
    return genai.Client(api_key=api_key)
