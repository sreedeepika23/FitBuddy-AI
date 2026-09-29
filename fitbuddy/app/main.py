"""
FitBuddy - AI Fitness Plan Generator using Gemini Models

Application entrypoint. Run with:
    uvicorn app.main:app --reload

Then visit:
    http://127.0.0.1:8000        (the app)
    http://127.0.0.1:8000/docs   (interactive API docs)
"""

import os

from dotenv import load_dotenv

# Load environment variables from .env before anything else needs them
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "..", "static")

app = FastAPI(
    title="FitBuddy - AI Fitness Plan Generator",
    description="Generates personalized 7-day workout plans and nutrition "
                 "tips using Google's Gemini models.",
    version="1.0.0",
)

# Serve /static/... (css, images) directly
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# All page + API routes live in routes.py
app.include_router(router)


@app.on_event("startup")
def on_startup():
    """Create the SQLite tables on first run."""
    init_db()
