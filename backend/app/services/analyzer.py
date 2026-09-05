"""Application Competitiveness Analyzer.

Produces profile subscores (0-100), a per-university fit, and a
Reach/Target/Likely classification. Everything here is a HEURISTIC ESTIMATE
built from published-style statistics and counselor rules of thumb - it is
not a probability of admission, and the API/UI must always say so.

Key modeling choices (deliberate, conservative):
- Any school with an acceptance rate under 15% is a Reach for every applicant.
- International applicants get a small strength penalty (their effective admit
  rates are typically lower than the published overall rate).
- The essay subscore is absent until the Phase 3 essay coach exists; weights
  renormalize over available components.
"""

from .major_advisor import major_preparation_score

DISCLAIMER = (
    "This is a heuristic estimate to help you plan - not a probability of "
    "admission and not a guarantee. Holistic review considers far more than "
    "these inputs."
)

LEADERSHIP_KEYWORDS = [
    "president", "captain", "founder", "lead", "chair", "director", "head",
    "editor", "organizer", "manager", "coach", "officer", "vp", "vice",
]

# weights for the overall profile score; renormalized over available subscores
WEIGHTS = {
    "academics": 0.30,
    "course_rigor": 0.15,
    "activities": 0.15,
    "leadership": 0.10,
    "awards": 0.10,
    "major_preparation": 0.20,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _gpa_norm(profile) -> float | None:
    if profile.gpa is None or not profile.gpa_scale:
        return None
    return _clamp(profile.gpa / profile.gpa_scale)


def _test_norm(profile) -> float | None:
    """Best standardized-test strength on a national-ish 0-1 scale."""
    scores = []
    if profile.sat:
        scores.append(_clamp((profile.sat - 800) / 800))
    if profile.act:
        scores.append(_clamp((profile.act - 12) / 24))
    return max(scores) if scores else None


def academics_score(profile) -> int | None:
    gpa = _gpa_norm(profile)
    test = _test_norm(profile)
    if gpa is None and test is None:
        return None
    if gpa is None:
        return round(test * 100)
    if test is None:
        return round(gpa * 100)
    return round((0.6 * gpa + 0.4 * test) * 100)


def course_rigor_score(profile) -> int:
    count = len(profile.courses or [])
    return min(100, round(count * 12.5))


def activities_score(profile) -> int:
    n = len(profile.activities or [])
    return 0 if n == 0 else min(100, 10 + n * 15)


def leadership_score(profile) -> int:
    hits = 0
    any_activity = False
    for act in profile.activities or []:
        any_activity = True
        text = " ".join(str(v) for v in act.values()).lower() if isinstance(act, dict) else str(act).lower()
        if any(kw in text for kw in LEADERSHIP_KEYWORDS):
            hits += 1
    base = 15 if any_activity else 0
    return min(100, base + hits * 30)


def awards_score(profile) -> int:
    return min(100, len(profile.awards or []) * 25)


def profile_scores(profile) -> dict:
    """School-independent subscores + weighted overall (0-100)."""
    subscores = {
        "academics": academics_score(profile),
        "course_rigor": course_rigor_score(profile),
        "activities": activities_score(profile),
        "leadership": leadership_score(profile),
        "awards": awards_score(profile),
        "major_preparation": major_preparation_score(profile, profile.intended_major),
    }

    available = {k: v for k, v in subscores.items() if v is not None}
    total_weight = sum(WEIGHTS[k] for k in available)
    overall = (
        round(sum(v * WEIGHTS[k] for k, v in available.items()) / total_weight)
        if total_weight
        else 0
    )

    notes = []
    if subscores["academics"] is None:
        notes.append("No GPA or test scores yet - add them for a much more meaningful estimate.")
    if subscores["major_preparation"] is None:
        notes.append("Pick an intended major to unlock the major-preparation subscore.")
    notes.append("Essay quality is not scored yet - the essay coach arrives in a later phase.")

    return {"subscores": subscores, "overall": overall, "notes": notes, "disclaimer": DISCLAIMER}


def _test_position(profile, university) -> float | None:
    """Where the student's score sits in the school's mid-50% band (0..1)."""
    if university.test_policy == "blind":
        return None
    positions = []
    if profile.sat and university.sat_25 and university.sat_75 and university.sat_75 > university.sat_25:
        positions.append(_clamp((profile.sat - university.sat_25) / (university.sat_75 - university.sat_25)))
    if profile.act and university.act_25 and university.act_75 and university.act_75 > university.act_25:
        positions.append(_clamp((profile.act - university.act_25) / (university.act_75 - university.act_25)))
    return max(positions) if positions else None


def university_fit(profile, university) -> dict:
    """Fit vs one university: strength, Reach/Target/Likely, and reasons."""
    scores = profile_scores(profile)
    sub = scores["subscores"]

    gpa = _gpa_norm(profile)
    test_pos = _test_position(profile, university)

    # academic fit: GPA and test position within this school's band
    parts = [p for p in (gpa, test_pos) if p is not None]
    academic_fit = sum(parts) / len(parts) if parts else 0.35  # unknown -> weak prior

    holistic = [sub[k] for k in ("activities", "leadership", "awards") if sub[k] is not None]
    if sub["major_preparation"] is not None:
        holistic.append(sub["major_preparation"])
    holistic_boost = (sum(holistic) / len(holistic) / 100) if holistic else 0.0

    strength = 0.75 * academic_fit + 0.25 * holistic_boost

    reasons = []
    if profile.student_type == "international":
        strength -= 0.05
        reasons.append(
            "International applicant pools are typically more competitive than the "
            "published overall admit rate suggests."
        )

    rate = university.acceptance_rate
    if rate is not None and rate < 0.15:
        classification = "reach"
        reasons.append(
            f"{university.name} admits ~{rate:.0%} of applicants (sample data) - "
            "schools this selective are a reach for every applicant, regardless of stats."
        )
    elif rate is None:
        classification = "target"
        reasons.append("No acceptance-rate data - treating as a target; verify independently.")
    elif (
        (strength >= 0.55 and rate >= 0.70)
        or (strength >= 0.70 and rate >= 0.45)
        or (strength >= 0.85 and rate >= 0.30)
    ):
        classification = "likely"
    elif strength < 0.35 or (strength < 0.55 and rate < 0.35):
        classification = "reach"
    else:
        classification = "target"

    if test_pos is not None:
        if test_pos >= 0.75:
            reasons.append("Your test score is at or above this school's 75th percentile (sample data).")
        elif test_pos <= 0.1:
            reasons.append("Your test score is near or below this school's 25th percentile (sample data).")
    elif university.test_policy == "blind":
        reasons.append("Test-blind school: scores are not considered here.")
    elif profile.sat is None and profile.act is None:
        reasons.append("No test score on file - the estimate leans on GPA alone.")

    if university.test_policy == "required" and not (profile.sat or profile.act):
        reasons.append("This school requires tests and you have none yet - that gap dominates everything else.")

    # highest-impact improvement: lowest available subscore
    improvable = {k: v for k, v in sub.items() if v is not None}
    biggest_lever = min(improvable, key=improvable.get) if improvable else None

    return {
        "university_id": university.id,
        "university": university.name,
        "acceptance_rate": rate,
        "strength": round(strength, 2),
        "classification": classification,
        "subscores": sub,
        "overall": scores["overall"],
        "reasons": reasons,
        "biggest_lever": biggest_lever,
        "disclaimer": DISCLAIMER,
    }
