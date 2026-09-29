"""
Basic smoke tests for FitBuddy.

These tests mock out the Gemini calls so they run instantly and do NOT
require a real GOOGLE_API_KEY or network access - useful for CI and for
verifying the FastAPI + SQLAlchemy wiring is correct.

Run with:
    pytest -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Point at a throwaway test database before importing the app
os.environ["GOOGLE_API_KEY"] = "test-key-not-used"

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Reset tables before each test for isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_home_page_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text
    assert "name=\"username\"" in response.text


@patch("app.routes.generate_nutrition_tip_with_flash", return_value="Drink water and eat protein.")
@patch("app.routes.generate_workout_gemini", return_value="Day 1: Full Body\n...\nDay 7: Rest")
def test_generate_workout(mock_workout, mock_tip):
    response = client.post(
        "/generate-workout",
        data={
            "username": "Test User",
            "user_id": "u123",
            "age": 30,
            "weight": 70,
            "goal": "muscle gain",
            "intensity": "medium",
        },
    )
    assert response.status_code == 200
    assert "Day 1: Full Body" in response.text
    assert "Drink water and eat protein." in response.text


@patch("app.routes.generate_nutrition_tip_with_flash", return_value="Add more fiber.")
@patch("app.routes.update_workout_plan", return_value="Day 1: More Cardio\n...\nDay 7: Rest")
@patch("app.routes.generate_workout_gemini", return_value="Day 1: Full Body\n...\nDay 7: Rest")
def test_submit_feedback(mock_workout, mock_update, mock_tip):
    # First, generate an original plan
    client.post(
        "/generate-workout",
        data={
            "username": "Test User",
            "user_id": "u456",
            "age": 25,
            "weight": 60,
            "goal": "weight loss",
            "intensity": "high",
        },
    )

    # Then submit feedback to revise it
    response = client.post(
        "/submit-feedback",
        data={"user_id": "u456", "feedback": "Add more cardio"},
    )
    assert response.status_code == 200
    assert "Day 1: More Cardio" in response.text


def test_submit_feedback_unknown_user():
    response = client.post(
        "/submit-feedback",
        data={"user_id": "does-not-exist", "feedback": "anything"},
    )
    assert response.status_code == 404
    assert "No existing plan found" in response.text


@patch("app.routes.generate_nutrition_tip_with_flash", return_value="Tip.")
@patch("app.routes.generate_workout_gemini", return_value="Day 1: Full Body")
def test_view_all_users(mock_workout, mock_tip):
    client.post(
        "/generate-workout",
        data={
            "username": "Admin View User",
            "user_id": "u789",
            "age": 40,
            "weight": 80,
            "goal": "general wellness",
            "intensity": "low",
        },
    )
    response = client.get("/view-all-users")
    assert response.status_code == 200
    assert "Admin View User" in response.text
    assert "u789" in response.text
