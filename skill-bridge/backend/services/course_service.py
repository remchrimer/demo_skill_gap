import os
import logging
import httpx

logger = logging.getLogger(__name__)

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"

# Skills that are "soft" or leadership-oriented need different search strategies
LEADERSHIP_SKILLS = {
    "technical leadership", "mentoring", "cross-team collaboration",
    "executive communication", "executive-level engagement", "c-suite advisory",
    "stakeholder management", "client relationship management",
    "stakeholder relationship building", "team building", "team management & mentoring",
    "mentoring & team development", "organizational influence", "practice development",
    "industry thought leadership", "strategic account planning",
    "complex engagement leadership", "customer advocacy", "client engagement & scoping",
    "executive & c-suite briefings", "customer communication", "business communication",
    "presentation skills", "technical presentations & workshops", "customer discovery",
    "competitive differentiation", "competitive positioning", "product thinking",
    "platform thinking", "p&l ownership", "market positioning",
    "cross-functional collaboration", "cross-functional leadership",
    "practice development & go-to-market", "client relationship development",
    "product strategy", "design leadership", "partner ecosystem strategy",
    "technical escalation leadership", "engineering collaboration (bug filing & triage)",
    "customer advocacy", "technical documentation leadership",
    "cross-functional problem solving", "product quality improvement",
    "complex deal support", "executive engagement",
    "soc modernization strategy", "client advisory (ciso-level)",
    "practice development", "zero trust transformation leadership",
    "technical breach response leadership", "complex engagement leadership",
    "regulatory expertise", "domain architecture & strategy",
    "enterprise security strategy", "qa strategy & leadership",
    "release quality management", "devops architecture",
    "release engineering strategy", "automation strategy",
    "platform engineering", "site reliability architecture",
    "enterprise architecture", "platform strategy", "vendor evaluation",
    "cost optimization", "compliance & governance",
    "product roadmapping", "prioritization frameworks",
    "go-to-market collaboration", "competitive intelligence",
}


def _is_leadership_skill(skill: str) -> bool:
    return skill.lower().strip() in LEADERSHIP_SKILLS


def _simplify_skill(skill: str) -> str:
    """Extract the core concept from compound skill names for better search results."""
    # Remove parenthetical details: "Forensic Tools (EnCase, FTK, X-Ways)" → "Forensic Tools"
    import re
    skill = re.sub(r'\s*\(.*?\)', '', skill)
    # Remove common filler phrases
    skill = skill.replace(" & ", " and ")
    # If skill has a colon or dash separator, take the more specific part
    # "Security Architecture Design" is fine, but "C-Suite Advisory" should stay
    return skill.strip()


def _build_search_query(skill: str, level: str) -> str:
    """Build a level and skill-type appropriate YouTube search query."""
    is_leadership = _is_leadership_skill(skill)
    clean_skill = _simplify_skill(skill)

    if level == "junior":
        if is_leadership:
            return f"{clean_skill} tips for new professionals"
        return f"{clean_skill} tutorial for beginners"

    elif level == "mid":
        if is_leadership:
            return f"{clean_skill} skills for engineering managers"
        return f"{clean_skill} advanced techniques real world examples"

    else:  # senior
        if is_leadership:
            return f"{clean_skill} engineering leadership talk"
        return f"{clean_skill} senior engineer staff engineer talk"


async def _fetch_youtube_courses(skill: str, level: str) -> list[dict]:
    """Fetch top 3 YouTube videos for a skill at the appropriate level."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY not set")

    query = _build_search_query(skill, level)

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 3,
        "order": "relevance",
        "videoDuration": "medium",
        "key": api_key,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(YOUTUBE_API_URL, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

    courses = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        snippet = item["snippet"]
        courses.append({
            "title": snippet["title"],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": snippet["thumbnails"]["medium"]["url"],
            "channel": snippet["channelTitle"],
        })

    return courses


def _fallback_search_url(skill: str, level: str) -> list[dict]:
    """Generate a direct YouTube search URL as fallback."""
    query = _build_search_query(skill, level).replace(" ", "+")
    return [{
        "title": f"Search YouTube for '{skill}' resources",
        "url": f"https://www.youtube.com/results?search_query={query}",
        "thumbnail": "",
        "channel": "YouTube Search",
    }]


async def get_courses_for_skills(skills: list[str], level: str) -> list[dict]:
    """
    Fetch YouTube courses for each skill at the appropriate level.
    Falls back to search URLs if API fails.
    """
    results = []

    for skill in skills:
        try:
            courses = await _fetch_youtube_courses(skill, level)
            results.append({
                "skill": skill,
                "courses": courses,
            })
        except Exception as e:
            logger.warning(f"YouTube API failed for '{skill}': {e}")
            results.append({
                "skill": skill,
                "courses": _fallback_search_url(skill, level),
            })

    return results