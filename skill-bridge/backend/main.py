from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path
import logging

from models import (
    AnalysisRequest, AnalysisResponse, SkillRecommendation,
    RoleSummary, SkillCourses, Course,
)
from services import role_service, ai_service, course_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data on startup."""
    role_service.load_roles()
    logger.info(f"Loaded {len(role_service.get_all_roles())} roles")
    yield


app = FastAPI(
    title="Skill-Bridge Career Navigator",
    description="AI-powered career gap analysis with rule-based fallback",
    version="1.0.0",
    lifespan=lifespan,
)


# --- API Routes ---

@app.get("/api/roles", response_model=list[RoleSummary])
def list_roles(
    category: str | None = Query(None, description="Filter by category"),
    q: str | None = Query(None, description="Search by keyword"),
):
    """List and filter available roles."""
    roles = role_service.filter_roles(category=category, q=q)
    return roles


@app.get("/api/skills", response_model=list[str])
def list_skills():
    """Get all unique skills for autocomplete."""
    return role_service.get_all_skills()


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest):
    """Run gap analysis: AI primary with rule-based fallback."""
    # Validate role exists
    role = role_service.get_role_by_id(request.target_role_id)
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{request.target_role_id}' not found")

    # Validate level exists for this role
    if request.target_level.value not in role["levels"]:
        raise HTTPException(
            status_code=422,
            detail=f"Level '{request.target_level.value}' not found for role '{request.target_role_id}'"
        )

    # Deduplicate skills while preserving order
    seen = set()
    unique_skills = []
    for s in request.skills:
        s_stripped = s.strip()
        if s_stripped and s_stripped.lower() not in seen:
            seen.add(s_stripped.lower())
            unique_skills.append(s_stripped)

    # Run analysis
    result = ai_service.analyze_skills(
        skills=unique_skills,
        role=role,
        target_level=request.target_level.value,
    )

    return AnalysisResponse(
        role=role["title"],
        level=request.target_level.value,
        skills=[SkillRecommendation(**s) for s in result["skills"]],
        used_fallback=result["used_fallback"],
        matching_skills=result.get("matching_skills", []),
        total_required=result.get("total_required", 0),
    )


@app.get("/api/courses", response_model=list[SkillCourses])
async def get_courses(
    skill: list[str] = Query(..., description="Skills to find courses for"),
    level: str = Query("junior", description="Target career level for content depth"),
):
    """Fetch YouTube course recommendations for given skills at appropriate depth."""
    if not skill:
        raise HTTPException(status_code=422, detail="At least one skill is required")

    results = await course_service.get_courses_for_skills(skill, level)

    return [
        SkillCourses(
            skill=r["skill"],
            courses=[Course(**c) for c in r["courses"]],
        )
        for r in results
    ]


# --- Serve Frontend ---

frontend_path = Path(__file__).parent.parent / "frontend"

if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(frontend_path / "index.html")