import json
from pathlib import Path

_roles_data: list[dict] = []


def load_roles() -> list[dict]:
    """Load roles from JSON file into memory. Called once at startup."""
    global _roles_data
    data_path = Path(__file__).parent.parent / "data" / "roles.json"
    with open(data_path, "r") as f:
        data = json.load(f)
    _roles_data = data["roles"]
    return _roles_data


def get_all_roles() -> list[dict]:
    """Return all roles."""
    return _roles_data


def filter_roles(category: str | None = None, q: str | None = None) -> list[dict]:
    """Filter roles by category and/or search query."""
    results = _roles_data

    if category:
        results = [r for r in results if r["category"].lower() == category.lower()]

    if q:
        query = q.lower()
        results = [
            r for r in results
            if query in r["title"].lower() or query in r["description"].lower()
        ]

    return results


def get_role_by_id(role_id: str) -> dict | None:
    """Get a single role by ID."""
    for role in _roles_data:
        if role["id"] == role_id:
            return role
    return None


def get_all_skills() -> list[str]:
    """Extract all unique skills from all roles and levels for autocomplete."""
    skills = set()
    for role in _roles_data:
        for level_data in role["levels"].values():
            for skill in level_data["required_skills"]:
                skills.add(skill)
            for skill in level_data.get("nice_to_have", []):
                skills.add(skill)
    return sorted(skills)