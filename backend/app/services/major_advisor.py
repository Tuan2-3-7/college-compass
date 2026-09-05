"""Major Advisor + Skill-Gap Analysis.

Compares what a major typically values (data/majors.py) against the student's
profile, producing per-skill status, an improvement plan, and a 0-100
major-preparation score used by the competitiveness analyzer.
"""

from ..data.majors import MAJORS

STATUS_STRONG = "strong"
STATUS_DEVELOPING = "developing"
STATUS_MISSING = "missing"


def profile_text_blob(profile) -> str:
    """Everything we can match keywords against, lowercased."""
    parts: list[str] = []
    parts.extend(profile.courses or [])
    for act in profile.activities or []:
        if isinstance(act, dict):
            parts.extend(str(v) for v in act.values())
        else:
            parts.append(str(act))
    parts.extend(profile.awards or [])
    return " | ".join(parts).lower()


def _match_evidence(keywords: list[str], blob: str, items: list[str]) -> list[str]:
    """Return the original profile items that matched any keyword."""
    evidence = []
    for item in items:
        low = item.lower()
        if any(kw in low for kw in keywords):
            evidence.append(item)
    return evidence


def analyze_skills(profile, major_key: str) -> list[dict]:
    """Per-skill gap analysis for one major. Raises KeyError for unknown major."""
    major = MAJORS[major_key]
    blob = profile_text_blob(profile)

    # original items for evidence display
    items: list[str] = list(profile.courses or [])
    for act in profile.activities or []:
        if isinstance(act, dict) and act.get("name"):
            items.append(str(act["name"]))
    items.extend(profile.awards or [])

    results = []
    for skill in major["skills"]:
        evidence = _match_evidence(skill["keywords"], blob, items)
        if len(evidence) >= 2:
            status = STATUS_STRONG
        elif len(evidence) == 1:
            status = STATUS_DEVELOPING
        else:
            status = STATUS_MISSING
        results.append(
            {
                "key": skill["key"],
                "name": skill["name"],
                "status": status,
                "evidence": evidence[:5],
                "how_to_build": skill["build"],
            }
        )
    return results


def major_preparation_score(profile, major_key: str | None) -> int | None:
    """0-100 preparation score; None when no major is chosen or it's unknown."""
    if not major_key or major_key not in MAJORS:
        return None
    skills = analyze_skills(profile, major_key)
    if not skills:
        return None
    points = {STATUS_STRONG: 1.0, STATUS_DEVELOPING: 0.5, STATUS_MISSING: 0.0}
    total = sum(points[s["status"]] for s in skills)
    return round(total / len(skills) * 100)


def improvement_plan(skills: list[dict]) -> list[dict]:
    """Ordered plan: missing skills first, then developing ones."""
    plan = []
    for s in skills:
        if s["status"] == STATUS_MISSING:
            plan.append({"skill": s["name"], "priority": "high", "action": s["how_to_build"]})
    for s in skills:
        if s["status"] == STATUS_DEVELOPING:
            plan.append({"skill": s["name"], "priority": "medium", "action": s["how_to_build"]})
    return plan


def advisor_payload(profile, major_key: str) -> dict:
    """Full Major Advisor response: roadmap + personalized gap analysis."""
    major = MAJORS[major_key]
    skills = analyze_skills(profile, major_key)
    return {
        "major": major_key,
        "label": major["label"],
        "academic_prep": major["academic_prep"],
        "experiences": major["experiences"],
        "application_evidence": major["evidence"],
        "skills": skills,
        "improvement_plan": improvement_plan(skills),
        "preparation_score": major_preparation_score(profile, major_key),
    }
