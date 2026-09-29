"""
Pydantic schemas used across FitBuddy.

These models validate and structure the data that flows between the
HTML forms, the FastAPI route handlers, and the Gemini-powered
generator functions.
"""

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    """Captures the data a user submits on the home page (index.html)."""

    username: str = Field(..., min_length=1, max_length=80)
    user_id: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=10, le=100)
    weight: float = Field(..., gt=0, le=400)
    goal: str = Field(..., min_length=1)
    intensity: str = Field(..., min_length=1)


class FeedbackRequest(BaseModel):
    """Captures feedback submitted on the result page to refine a plan."""

    user_id: str = Field(..., min_length=1, max_length=50)
    feedback: str = Field(..., min_length=1)
