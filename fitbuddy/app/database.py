"""
Database layer for FitBuddy.

Uses SQLAlchemy ORM with a local SQLite file (fitbuddy.db) to persist:
  - User      : the personal details a user submits on the home page
  - Plan      : the AI-generated workout plan, nutrition tip, and any
                feedback-updated plan for that user

Exposed helper functions (mirrors the project spec):
  save_user(), save_plan(), update_plan(),
  get_user(), get_original_plan(),
  get_all_users(), get_all_plans()
"""

import os
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "fitbuddy.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --------------------------------------------------------------------------
# ORM Models
# --------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String, nullable=False)
    intensity = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("Plan", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False, unique=True)
    workout_plan = Column(Text, nullable=False)
    nutrition_tip = Column(Text, nullable=True)
    updated_plan = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="plan")


def init_db() -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------------
def save_user(db: Session, user_input) -> User:
    """Create a new user record, or update it if the user_id already exists."""
    existing = db.query(User).filter(User.user_id == user_input.user_id).first()
    if existing:
        existing.username = user_input.username
        existing.age = user_input.age
        existing.weight = user_input.weight
        existing.goal = user_input.goal
        existing.intensity = user_input.intensity
        db.commit()
        db.refresh(existing)
        return existing

    user = User(
        user_id=user_input.user_id,
        username=user_input.username,
        age=user_input.age,
        weight=user_input.weight,
        goal=user_input.goal,
        intensity=user_input.intensity,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_plan(db: Session, user_id: str, workout_plan: str, nutrition_tip: str) -> Plan:
    """Create (or overwrite) the original AI-generated plan for a user."""
    existing = db.query(Plan).filter(Plan.user_id == user_id).first()
    if existing:
        existing.workout_plan = workout_plan
        existing.nutrition_tip = nutrition_tip
        existing.updated_plan = None
        existing.feedback = None
        db.commit()
        db.refresh(existing)
        return existing

    plan = Plan(user_id=user_id, workout_plan=workout_plan, nutrition_tip=nutrition_tip)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db: Session, user_id: str, updated_plan: str, feedback: str | None = None) -> Plan | None:
    """Store a feedback-revised plan alongside the original plan."""
    plan = db.query(Plan).filter(Plan.user_id == user_id).first()
    if not plan:
        return None
    plan.updated_plan = updated_plan
    if feedback is not None:
        plan.feedback = feedback
    db.commit()
    db.refresh(plan)
    return plan


def get_user(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.user_id == user_id).first()


def get_original_plan(db: Session, user_id: str) -> Plan | None:
    return db.query(Plan).filter(Plan.user_id == user_id).first()


def get_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


def get_all_plans(db: Session) -> list[Plan]:
    return db.query(Plan).all()


def delete_user(db: Session, user_id: str) -> bool:
    """Delete a user (and their plan, via cascade). Used by the admin panel."""
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
