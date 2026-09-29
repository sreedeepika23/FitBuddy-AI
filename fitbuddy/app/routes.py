"""
routes.py - the operational core of FitBuddy.

Bridges the frontend templates, the AI generation modules
(Gemini Pro & Flash), and the SQLite database.

Routes:
    GET  /                 -> home page with the user-input form
    POST /generate-workout -> generate a 7-day plan + nutrition tip
    POST /submit-feedback  -> revise an existing plan based on feedback
    GET  /view-all-users   -> admin dashboard of all users & plans
    POST /delete-user/{id} -> admin: remove a user and their plan
"""

import os

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import (
    get_db,
    save_user,
    save_plan,
    update_plan,
    get_user,
    get_original_plan,
    get_all_users,
    get_all_plans,
    delete_user,
)
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan
from app.models import UserInput


router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "templates")
)

templates = Jinja2Templates(directory=TEMPLATE_DIR)


# --------------------------------------------------------------------------
# / - Home route
# --------------------------------------------------------------------------
@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


# --------------------------------------------------------------------------
# /generate-workout - Plan Generator
# --------------------------------------------------------------------------
@router.post("/generate-workout")
def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    # Validate/structure the incoming form data
    user_input = UserInput(
        username=username,
        user_id=user_id,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
    )

    # Call Gemini Pro for the workout plan
    workout_plan = generate_workout_gemini(
        username=user_input.username,
        age=user_input.age,
        weight=user_input.weight,
        goal=user_input.goal,
        intensity=user_input.intensity,
    )

    # Call Gemini Flash for the nutrition tip
    nutrition_tip = generate_nutrition_tip_with_flash(
        goal=user_input.goal
    )

    # Save user and generated plan
    save_user(db, user_input)

    save_plan(
        db,
        user_input.user_id,
        workout_plan,
        nutrition_tip,
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "username": user_input.username,
            "user_id": user_input.user_id,
            "age": user_input.age,
            "weight": user_input.weight,
            "goal": user_input.goal,
            "intensity": user_input.intensity,
            "workout_plan": workout_plan,
            "nutrition_tip": nutrition_tip,
            "updated_plan": None,
            "feedback_sent": False,
        },
    )


# --------------------------------------------------------------------------
# /submit-feedback - Update Plan with Feedback
# --------------------------------------------------------------------------
@router.post("/submit-feedback")
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user(db, user_id)
    plan = get_original_plan(db, user_id)

    if not user or not plan:
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "error": (
                    f"No existing plan found for user_id "
                    f"'{user_id}'. Please generate a plan first."
                )
            },
            status_code=404,
        )

    # Revise the plan using Gemini Pro
    revised_plan = update_workout_plan(
        plan.workout_plan,
        feedback,
    )

    # Refresh nutrition tip
    nutrition_tip = generate_nutrition_tip_with_flash(
        goal=user.goal
    )

    # Update database
    update_plan(
        db,
        user_id,
        revised_plan,
        feedback,
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "username": user.username,
            "user_id": user.user_id,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity,
            "workout_plan": plan.workout_plan,
            "nutrition_tip": nutrition_tip,
            "updated_plan": revised_plan,
            "feedback_sent": True,
        },
    )


# --------------------------------------------------------------------------
# /view-all-users - Admin View
# --------------------------------------------------------------------------
@router.get("/view-all-users")
def view_all_users(
    request: Request,
    db: Session = Depends(get_db),
):
    users = get_all_users(db)
    plans = get_all_plans(db)

    # Index plans by user_id
    plans_by_user = {
        plan.user_id: plan
        for plan in plans
    }

    rows = []

    for user in users:
        plan = plans_by_user.get(user.user_id)

        rows.append(
            {
                "user_id": user.user_id,
                "username": user.username,
                "age": user.age,
                "weight": user.weight,
                "goal": user.goal,
                "intensity": user.intensity,
                "workout_plan": (
                    plan.workout_plan
                    if plan
                    else None
                ),
                "nutrition_tip": (
                    plan.nutrition_tip
                    if plan
                    else None
                ),
                "updated_plan": (
                    plan.updated_plan
                    if plan
                    else None
                ),
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "users": rows,
        },
    )


# --------------------------------------------------------------------------
# /delete-user/{user_id} - Admin: remove a user
# --------------------------------------------------------------------------
@router.post("/delete-user/{user_id}")
def delete_user_route(
    user_id: str,
    db: Session = Depends(get_db),
):
    delete_user(db, user_id)

    return RedirectResponse(
        url="/view-all-users",
        status_code=303,
    )