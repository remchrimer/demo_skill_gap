from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# --- Enums ---

class TargetLevel(str, Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"


# --- Request Models ---

class AnalysisRequest(BaseModel):
    skills: list[str] = Field(
        ..., min_length=1, max_length=20,
        description="List of user's current skills"
    )
    target_role_id: str = Field(
        ..., description="ID of the target role from roles.json"
    )
    target_level: TargetLevel = Field(
        ..., description="Target career level"
    )


# --- Response Models ---

class SkillRecommendation(BaseModel):
    name: str
    reason: str


class AnalysisResponse(BaseModel):
    role: str
    level: str
    skills: list[SkillRecommendation]
    used_fallback: bool
    matching_skills: list[str]
    total_required: int


class RoleLevel(BaseModel):
    required_skills: list[str]
    nice_to_have: list[str]


class RoleSummary(BaseModel):
    id: str
    title: str
    category: str
    description: str
    levels: dict[str, RoleLevel]


class Course(BaseModel):
    title: str
    url: str
    thumbnail: str
    channel: str


class SkillCourses(BaseModel):
    skill: str
    courses: list[Course]