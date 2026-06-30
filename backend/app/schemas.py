from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    company: Optional[str] = ""
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    company: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# Executive schemas
class ExecutiveBase(BaseModel):
    id: str
    title: str
    role: str
    description: str
    focus_areas: list[str]
    status: str
    insights_count: int
    risk_level: str


# Insight schemas
class Insight(BaseModel):
    id: str
    executive_id: str
    executive_title: str
    category: str
    priority: str
    title: str
    summary: str
    impact: str
    recommendation: str
    confidence: int
    created_at: str


# Briefing schemas
class BriefingItem(BaseModel):
    category: str
    title: str
    detail: str
    impact: Optional[str] = None
    recommendation: Optional[str] = None
    probability: Optional[int] = None


class DailyBriefing(BaseModel):
    date: str
    company: str
    overall_health: str
    health_score: int
    items: list[BriefingItem]
    top_priority: str
